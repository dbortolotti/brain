#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, update

from memory_stack import brain_schema as schema
from memory_stack.brain_store import create_brain_engine, normalize_user_id
from memory_stack.cfg import Settings, load_settings
from memory_stack.oauth import auth_users_file_path, ensure_auth_password, write_auth_users
from memory_stack.profile_context import _context_id, _normalize_statement, _path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move the original single-user Brain data from default to daniele and create root auth."
    )
    parser.add_argument("--from-user", default="default")
    parser.add_argument("--to-user", default="daniele")
    parser.add_argument("--root-user", default="default")
    parser.add_argument("--to-display-name", default="Daniele Bortolotti")
    parser.add_argument("--to-email", default="")
    parser.add_argument("--root-display-name", default="Root")
    parser.add_argument("--root-password-file", default=None)
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this, only print a plan.")
    parser.add_argument(
        "--allow-target-existing",
        action="store_true",
        help="Allow moving into a user that already has rows.",
    )
    parser.add_argument(
        "--overwrite-profile-context",
        action="store_true",
        help="Replace an existing target profile-context file.",
    )
    args = parser.parse_args()

    settings = load_settings()
    from_user = normalize_user_id(args.from_user)
    to_user = normalize_user_id(args.to_user)
    root_user = normalize_user_id(args.root_user)
    if from_user == to_user:
        raise SystemExit("--from-user and --to-user must differ")
    if root_user != from_user:
        raise SystemExit("This migration expects the root user to remain the original default user.")

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

    backup_paths = backup_mutable_files(settings)
    migrate_database(settings, from_user=from_user, to_user=to_user, args=args)
    migrate_profile_context(
        settings,
        from_user=from_user,
        to_user=to_user,
        overwrite=args.overwrite_profile_context,
    )
    write_auth_registry(
        settings,
        root_user=root_user,
        to_user=to_user,
        to_display_name=args.to_display_name,
        to_email=args.to_email,
        root_display_name=args.root_display_name,
        root_password_file=Path(args.root_password_file).expanduser() if args.root_password_file else None,
    )
    invalidate_oauth_tokens(settings)
    print(json.dumps({"status": "migrated", "backups": backup_paths}, indent=2, sort_keys=True))
    return 0


def build_plan(settings: Settings, *, from_user: str, to_user: str) -> dict[str, Any]:
    engine = create_brain_engine(settings)
    tables = []
    with engine.begin() as conn:
        for table in user_scoped_tables():
            from_count = conn.execute(
                select(func.count()).select_from(table).where(table.c.user_id == from_user)
            ).scalar_one()
            to_count = conn.execute(
                select(func.count()).select_from(table).where(table.c.user_id == to_user)
            ).scalar_one()
            tables.append({"table": table.name, "from_count": int(from_count), "to_count": int(to_count)})
    return {
        "database_url": settings.brain_database_url,
        "from_user": from_user,
        "to_user": to_user,
        "auth_users_file": str(auth_users_file_path(settings) or ""),
        "profile_context_from": str(_path(settings, user_id=from_user)),
        "profile_context_to": str(_path(settings, user_id=to_user)),
        "tables": tables,
    }


def user_scoped_tables() -> list[Any]:
    return [table for table in schema.metadata.sorted_tables if "user_id" in table.c]


def backup_mutable_files(settings: Settings) -> dict[str, str]:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backups: dict[str, str] = {}
    for label, path in {
        "brain_db": sqlite_path(settings.brain_database_url),
        "profile_context": Path(settings.brain_profile_context_path).expanduser(),
        "auth_users": auth_users_file_path(settings),
        "oauth_state": Path(settings.brain_auth_state_path).expanduser(),
    }.items():
        if path and path.exists():
            backup = path.with_name(f"{path.name}.bak_user_migration_{stamp}")
            shutil.copy2(path, backup)
            backups[label] = str(backup)
    return backups


def sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise SystemExit(f"Only SQLite Brain DB migrations are supported, got: {database_url}")
    return Path(database_url.removeprefix(prefix)).expanduser()


def migrate_database(settings: Settings, *, from_user: str, to_user: str, args: argparse.Namespace) -> None:
    engine = create_brain_engine(settings)
    with engine.begin() as conn:
        for table in user_scoped_tables():
            conn.execute(update(table).where(table.c.user_id == from_user).values(user_id=to_user))
        upsert_brain_user(
            conn,
            user_id=to_user,
            display_name=args.to_display_name,
            email=args.to_email,
            status="active",
            metadata={"migrated_from_user_id": from_user},
        )
        upsert_brain_user(
            conn,
            user_id=args.root_user,
            display_name=args.root_display_name,
            email="",
            status="active",
            metadata={"root_user": True},
        )
        update_profile_metadata(conn, from_user=from_user, to_user=to_user)


def upsert_brain_user(
    conn: Any,
    *,
    user_id: str,
    display_name: str,
    email: str,
    status: str,
    metadata: dict[str, Any],
) -> None:
    existing = conn.execute(
        select(schema.brain_users.c.id).where(schema.brain_users.c.id == user_id)
    ).first()
    values = {
        "display_name": display_name,
        "email": email,
        "status": status,
        "metadata_json": metadata,
        "updated_at": datetime.now(UTC),
    }
    if existing:
        conn.execute(update(schema.brain_users).where(schema.brain_users.c.id == user_id).values(**values))
    else:
        conn.execute(schema.brain_users.insert().values(id=user_id, **values))


def update_profile_metadata(conn: Any, *, from_user: str, to_user: str) -> None:
    for table in (schema.entities, schema.brain_context_records):
        rows = conn.execute(select(table.c.id, table.c.metadata_json)).all()
        for row in rows:
            metadata = dict(row.metadata_json or {})
            changed = False
            for key in ("profile_context_user_id", "profile_owner_id", "profile_user_id"):
                if metadata.get(key) == from_user:
                    metadata[key] = to_user
                    changed = True
            if changed:
                conn.execute(update(table).where(table.c.id == row.id).values(metadata_json=metadata))


def migrate_profile_context(
    settings: Settings,
    *,
    from_user: str,
    to_user: str,
    overwrite: bool,
) -> None:
    source_path = _path(settings, user_id=from_user)
    target_path = _path(settings, user_id=to_user)
    records: list[dict[str, Any]] = []
    if source_path.exists():
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise SystemExit(f"profile context file must contain a list: {source_path}")
        for record in payload:
            if not isinstance(record, dict) or not record.get("statement"):
                continue
            statement = _normalize_statement(str(record["statement"]))
            scope = str(record.get("scope") or "answer_tailoring").strip() or "answer_tailoring"
            record = dict(record)
            record["user_id"] = to_user
            record["id"] = _context_id(statement, scope, user_id=to_user)
            records.append(record)
    if target_path.exists() and target_path.read_text(encoding="utf-8").strip() not in {"", "[]"} and not overwrite:
        raise SystemExit(f"target profile context already exists and is non-empty: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target_path.chmod(0o600)
    if source_path != target_path:
        source_path.write_text("[]\n", encoding="utf-8")
        source_path.chmod(0o600)


def write_auth_registry(
    settings: Settings,
    *,
    root_user: str,
    to_user: str,
    to_display_name: str,
    to_email: str,
    root_display_name: str,
    root_password_file: Path | None,
) -> None:
    daniele_password = ensure_auth_password(settings)
    if root_password_file is None:
        root_password_file = Path(settings.brain_auth_password_file).expanduser().with_name("brain-auth-root-password")
    if root_password_file.exists():
        root_password = root_password_file.read_text(encoding="utf-8").strip()
    else:
        root_password = secrets.token_urlsafe(32)
        root_password_file.write_text(root_password + "\n", encoding="utf-8")
        root_password_file.chmod(0o600)
    users = {
        root_user: {
            "id": root_user,
            "password": root_password,
            "display_name": root_display_name,
            "email": "",
            "superuser": True,
        },
        to_user: {
            "id": to_user,
            "password": daniele_password,
            "display_name": to_display_name,
            "email": to_email,
            "superuser": False,
        },
    }
    write_auth_users(settings, users)


def invalidate_oauth_tokens(settings: Settings) -> None:
    path = Path(settings.brain_auth_state_path).expanduser()
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return
    payload["pending_authorizations"] = {}
    payload["authorization_codes"] = {}
    payload["access_tokens"] = {}
    payload["refresh_tokens"] = {}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


if __name__ == "__main__":
    raise SystemExit(main())
