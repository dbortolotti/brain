#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Brain nightly maintenance backups."
    )
    parser.add_argument("--env", choices=["dev", "qa", "staging", "prod"], default="prod")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--backup-dir", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--skip-google-drive", action="store_true")
    parser.add_argument("--skip-cognify", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    env = os.environ.copy()
    if args.env_file:
        env["ENV_FILE"] = args.env_file

    backup_cmd = [sys.executable, str(script_dir / "backup_stores.py")]
    if args.backup_dir:
        backup_cmd.extend(["--backup-dir", args.backup_dir])
    if args.data_dir:
        backup_cmd.extend(["--data-dir", args.data_dir])
    if args.skip_google_drive:
        backup_cmd.append("--skip-google-drive")

    prune_cmd = [sys.executable, str(script_dir / "prune_deleted_palate_items.py")]
    cognify_cmd = [sys.executable, str(script_dir / "cognify_datasets.py")]

    print(f"[maintenance] started at {timestamp()}", flush=True)
    print("[maintenance] pruning deleted palate items", flush=True)
    prune_result = subprocess.run(prune_cmd, env=env, check=False)
    if prune_result.returncode != 0:
        print(
            f"[maintenance] palate prune failed with exit code {prune_result.returncode}",
            file=sys.stderr,
            flush=True,
        )
        return prune_result.returncode

    cognify_returncode = 0
    if args.skip_cognify:
        print("[maintenance] skipping cognify", flush=True)
    else:
        print("[maintenance] cognifying datasets", flush=True)
        cognify_result = subprocess.run(cognify_cmd, env=env, check=False)
        cognify_returncode = cognify_result.returncode
        if cognify_returncode != 0:
            # A cognify failure must never block the backup; report it after.
            print(
                f"[maintenance] cognify failed with exit code {cognify_returncode}",
                file=sys.stderr,
                flush=True,
            )

    print("[maintenance] running backup", flush=True)
    backup_result = subprocess.run(backup_cmd, env=env, check=False)
    if backup_result.returncode != 0:
        print(
            f"[maintenance] backup failed with exit code {backup_result.returncode}",
            file=sys.stderr,
            flush=True,
        )
        return backup_result.returncode

    print(f"[maintenance] completed at {timestamp()}", flush=True)
    return cognify_returncode


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
