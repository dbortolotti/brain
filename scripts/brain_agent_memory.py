#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.cognee_adapter import improve_cognee, run_async
from memory_stack.cfg import load_settings
from memory_stack.io import to_jsonable


DEFAULT_SESSION_ID = "portable_agent_session"


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge one Cognee agent session into Brain agent memory.")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--env", choices=["dev", "prod"], default="prod")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--node-name", action="append", default=None)
    parser.add_argument("--background", action="store_true")
    args = parser.parse_args()

    session_id = args.session_id.strip()
    if not session_id:
        raise SystemExit("session_id must not be blank.")

    settings = load_settings(args.env_file, config_env=args.env)
    result = run_async(
        improve_cognee(
            dataset=settings.brain_cognee_agent_memory_dataset,
            node_name=args.node_name,
            session_ids=[session_id],
            run_in_background=args.background,
            settings=settings,
        )
    )
    payload = {
        "session_id": session_id,
        "dataset": "agent_memory",
        "resolved_dataset": settings.brain_cognee_agent_memory_dataset,
        "node_name": args.node_name or [],
        "run_in_background": args.background,
        "result": to_jsonable(result),
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
