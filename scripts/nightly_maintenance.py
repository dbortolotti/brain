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
        description="Run Brain nightly maintenance: cognify agent memory, then back up on success."
    )
    parser.add_argument("--env", choices=["dev", "qa", "staging", "prod"], default="prod")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--node-name", action="append", default=None)
    parser.add_argument("--backup-dir", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--skip-google-drive", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    env = os.environ.copy()
    if args.env_file:
        env["ENV_FILE"] = args.env_file

    agent_cmd = [
        sys.executable,
        str(script_dir / "brain_agent_memory.py"),
        "--env",
        args.env,
    ]
    if args.env_file:
        agent_cmd.extend(["--env-file", args.env_file])
    if args.session_id:
        agent_cmd.extend(["--session-id", args.session_id])
    for node_name in args.node_name or []:
        agent_cmd.extend(["--node-name", node_name])

    backup_cmd = [sys.executable, str(script_dir / "backup_stores.py")]
    if args.backup_dir:
        backup_cmd.extend(["--backup-dir", args.backup_dir])
    if args.data_dir:
        backup_cmd.extend(["--data-dir", args.data_dir])
    if args.skip_google_drive:
        backup_cmd.append("--skip-google-drive")

    print(f"[maintenance] started at {timestamp()}", flush=True)
    print("[maintenance] running agent-memory cognify", flush=True)
    agent_result = subprocess.run(agent_cmd, env=env, check=False)
    if agent_result.returncode != 0:
        print(
            f"[maintenance] agent-memory failed with exit code {agent_result.returncode}; skipping backup",
            file=sys.stderr,
            flush=True,
        )
        return agent_result.returncode

    print("[maintenance] agent-memory completed successfully; running backup", flush=True)
    backup_result = subprocess.run(backup_cmd, env=env, check=False)
    if backup_result.returncode != 0:
        print(
            f"[maintenance] backup failed with exit code {backup_result.returncode}",
            file=sys.stderr,
            flush=True,
        )
        return backup_result.returncode

    print(f"[maintenance] completed at {timestamp()}", flush=True)
    return 0


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
