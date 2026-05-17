#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, update

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack import brain_schema as schema
from memory_stack.brain_store import create_brain_engine, normalize_user_id
from memory_stack.cfg import Settings, load_settings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move Brain database rows from one user_id scope to another."
    )
    parser.add_argument("--from-user", default="default")
    parser.add_argument("--to-user", required=True)
    parser.add_argument("--env", choices=["dev", "staging", "prod"], default="prod")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--allow-target-existing",
        action="store_true",
        help="Allow moving rows into a user scope that already has rows.",
    )
    args = parser.parse_args()

    settings = load_settings(args.env_file, config_env=args.env)
    from_user = normalize_user_id(args.from_user)
    to_user = normalize_user_id(args.to_user)
    if from_user == to_user:
        raise SystemExit("--from-user and --to-user must differ")

    plan = build_plan(settings, from_user=from_user, to_user=to_user)
    print(json.dumps(plan, indent=2, sort_keys=True))
    if not args.apply:
        print("dry run only; pass --apply to migrate", file=sys.stderr)
        return 0

    target_rows = sum(item["to_count"] for item in plan["tables"])
    if target_rows and not args.allow_target_existing:
        raise SystemExit(
            f"target user {to_user!r} already has {target_rows} rows; "
            "rerun with --allow-target-existing if this is intentional"
        )

    backups = backup_database(settings)
    migrated = migrate_database(settings, from_user=from_user, to_user=to_user)
    print(
        json.dumps(
            {
                "status": "migrated",
                "backups": backups,
                "migrated_rows": migrated,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def user_scoped_tables() -> list[Any]:
    return [table for table in schema.metadata.sorted_tables if "user_id" in table.c]


def build_plan(settings: Settings, *, from_user: str, to_user: str) -> dict[str, Any]:
    engine = create_brain_engine(settings)
    tables: list[dict[str, Any]] = []
    with engine.begin() as conn:
        for table in user_scoped_tables():
            from_count = conn.execute(
                select(func.count()).select_from(table).where(table.c.user_id == from_user)
            ).scalar_one()
            to_count = conn.execute(
                select(func.count()).select_from(table).where(table.c.user_id == to_user)
            ).scalar_one()
            tables.append(
                {
                    "table": table.name,
                    "from_count": int(from_count),
                    "to_count": int(to_count),
                }
            )
    return {
        "database_url": settings.brain_database_url,
        "from_user": from_user,
        "to_user": to_user,
        "tables": tables,
        "total_from_count": sum(item["from_count"] for item in tables),
        "total_to_count": sum(item["to_count"] for item in tables),
    }


def migrate_database(settings: Settings, *, from_user: str, to_user: str) -> dict[str, int]:
    engine = create_brain_engine(settings)
    migrated: dict[str, int] = {}
    with engine.begin() as conn:
        for table in user_scoped_tables():
            result = conn.execute(update(table).where(table.c.user_id == from_user).values(user_id=to_user))
            migrated[table.name] = int(result.rowcount or 0)
    return migrated


def backup_database(settings: Settings) -> dict[str, str]:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = sqlite_path(settings.brain_database_url)
    if not path.exists():
        return {}
    backup = path.with_name(f"{path.name}.bak_user_scoped_migration_{stamp}")
    shutil.copy2(path, backup)
    return {"brain_db": str(backup)}


def sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise SystemExit(f"Only SQLite Brain DB migrations are supported, got: {database_url}")
    return Path(database_url.removeprefix(prefix)).expanduser()


if __name__ == "__main__":
    raise SystemExit(main())
