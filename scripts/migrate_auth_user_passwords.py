#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.cfg import load_settings
from memory_stack.oauth import (
    auth_users_file_path,
    ensure_auth_password,
    load_auth_users,
    needs_password_migration,
    write_auth_users,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Brain auth users to hashed passwords.")
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--config-env", default=None)
    parser.add_argument("--check", action="store_true", help="Fail if any user still needs migration.")
    args = parser.parse_args()

    settings = load_settings(args.env_file, config_env=args.config_env)
    default_password = ensure_auth_password(settings)
    users = load_auth_users(settings, default_password=default_password)
    before = {
        user_id: {
            "password_scheme": record.get("password_scheme") or "legacy",
            "migration_required": needs_password_migration(record),
        }
        for user_id, record in sorted(users.items())
    }
    required = [user_id for user_id, record in users.items() if needs_password_migration(record)]
    if args.check:
        print(json.dumps({"users_file": str(auth_users_file_path(settings) or ""), "users": before}, indent=2))
        return 1 if required else 0

    write_auth_users(settings, users)
    migrated = load_auth_users(settings, default_password=default_password)
    after = {
        user_id: {
            "password_scheme": record.get("password_scheme") or "legacy",
            "migration_required": needs_password_migration(record),
        }
        for user_id, record in sorted(migrated.items())
    }
    print(
        json.dumps(
            {
                "users_file": str(auth_users_file_path(settings) or ""),
                "migrated_users": required,
                "before": before,
                "after": after,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
