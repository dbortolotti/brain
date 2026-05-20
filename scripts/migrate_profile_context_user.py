#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.brain_store import BrainStore, normalize_user_id
from memory_stack.cfg import load_settings
from memory_stack.profile_context import _context_id, _normalize_statement, _path, sync_profile_context


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move profile-context records from one Brain user scope to another."
    )
    parser.add_argument("--from-user", default="default")
    parser.add_argument("--to-user", required=True)
    parser.add_argument("--env", choices=["dev", "qa", "staging", "prod"], default="prod")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--allow-target-existing",
        action="store_true",
        help="Merge into a non-empty target profile-context file.",
    )
    args = parser.parse_args()

    settings = load_settings(args.env_file, config_env=args.env)
    from_user = normalize_user_id(args.from_user)
    to_user = normalize_user_id(args.to_user)
    if from_user == to_user:
        raise SystemExit("--from-user and --to-user must differ")

    source_path = _path(settings, user_id=from_user)
    target_path = _path(settings, user_id=to_user)
    source_records = read_records(source_path)
    target_records = read_records(target_path)
    if target_records and not args.allow_target_existing:
        raise SystemExit(
            f"target profile-context file is non-empty: {target_path}; "
            "pass --allow-target-existing to merge"
        )

    plan = {
        "from_user": from_user,
        "to_user": to_user,
        "source_path": str(source_path),
        "target_path": str(target_path),
        "source_count": len(source_records),
        "target_count": len(target_records),
        "old_memory_ids": [record.get("memory_id") for record in source_records if record.get("memory_id")],
    }
    print(json.dumps(plan, indent=2, sort_keys=True))
    if not args.apply:
        print("dry run only; pass --apply to migrate", file=sys.stderr)
        return 0

    backups = backup_files(settings, source_path, target_path)
    migrated_records = migrate_records(source_records, target_records, to_user=to_user)
    write_records(target_path, migrated_records)
    write_records(source_path, [])

    old_memory_ids = [str(record["memory_id"]) for record in source_records if record.get("memory_id")]
    default_store = BrainStore(settings, user_id=from_user)
    deleted_old = [memory_id for memory_id in old_memory_ids if default_store.update_memory_status(memory_id, "deleted")]
    synced = sync_profile_context(settings, user_id=to_user)
    print(
        json.dumps(
            {
                "status": "migrated",
                "backups": backups,
                "deleted_old_projection_count": len(deleted_old),
                "synced_target_count": synced["synced_count"],
                "target_profile_context_count": synced["profile_context_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit(f"profile context file must contain a list: {path}")
    return [record for record in payload if isinstance(record, dict) and record.get("statement")]


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def migrate_records(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    *,
    to_user: str,
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for record in target_records:
        statement = _normalize_statement(str(record["statement"]))
        scope = str(record.get("scope") or "answer_tailoring").strip() or "answer_tailoring"
        by_key[(scope, statement.casefold())] = dict(record)
    for source in source_records:
        statement = _normalize_statement(str(source["statement"]))
        scope = str(source.get("scope") or "answer_tailoring").strip() or "answer_tailoring"
        record = {
            key: value
            for key, value in source.items()
            if key
            not in {
                "id",
                "user_id",
                "memory_id",
                "owner_entity_id",
                "previous_memory_id",
                "sync_error",
                "synced_at",
            }
        }
        record.update(
            {
                "id": _context_id(statement, scope, user_id=to_user),
                "user_id": to_user,
                "statement": statement,
                "scope": scope,
                "sync_status": "pending",
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )
        by_key[(scope, statement.casefold())] = record
    return sorted(by_key.values(), key=lambda item: (str(item.get("scope")), str(item.get("statement"))))


def backup_files(settings, source_path: Path, target_path: Path) -> dict[str, str]:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    paths = {
        "brain_db": sqlite_path(settings.brain_database_url),
        "source_profile_context": source_path,
        "target_profile_context": target_path,
    }
    backups: dict[str, str] = {}
    for label, path in paths.items():
        if path.exists():
            backup = path.with_name(f"{path.name}.bak_profile_context_migration_{stamp}")
            shutil.copy2(path, backup)
            backups[label] = str(backup)
    return backups


def sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise SystemExit(f"Only SQLite Brain DB migrations are supported, got: {database_url}")
    return Path(database_url.removeprefix(prefix)).expanduser()


if __name__ == "__main__":
    raise SystemExit(main())
