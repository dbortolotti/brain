#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cfg import (
    PROJECT_ROOT,
    load_settings,
    provider_api_environment,
    repo_path,
)


console = Console()
CLAUDE_CONFIG_PATH = (
    Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    settings = load_settings()
    env = {
        "PROFILE": settings.profile,
        "LLM_PROVIDER": settings.llm_provider,
        "LLM_MODEL": settings.llm_model,
        "LLM_API_KEY": settings.llm_api_key or "",
        "EMBEDDING_PROVIDER": settings.embedding_provider,
        "EMBEDDING_MODEL": settings.embedding_model,
        "EMBEDDING_API_KEY": settings.embedding_api_key or "",
        "GRAPH_DATABASE_PROVIDER": settings.graph_database_provider,
        "GRAPH_DATABASE_URL": settings.graph_database_url,
        "GRAPH_DATABASE_USERNAME": settings.graph_database_username,
        "GRAPH_DATABASE_PASSWORD": settings.graph_database_password,
        "VECTOR_DB_PROVIDER": settings.vector_db_provider,
        "VECTOR_DB_URL": str(repo_path(settings.vector_db_url)),
        "DB_PROVIDER": settings.db_provider,
        "DB_NAME": settings.db_name,
        "SYSTEM_ROOT_DIRECTORY": str(repo_path(settings.system_root_directory)),
        "DATA_ROOT_DIRECTORY": str(repo_path(settings.data_root_directory)),
    }
    env.update(provider_api_environment(settings))
    config = {
        "mcpServers": {
            "brain": {
                "command": sys.executable,
                "args": ["-m", "memory_stack.mcp_stdio"],
                "cwd": str(PROJECT_ROOT),
                "env": env,
            }
        }
    }

    payload = json.dumps(config, indent=2)
    print(payload)
    target = Path(args.output) if args.output else CLAUDE_CONFIG_PATH
    print(f"target: {target}")

    if args.write or args.output:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload + "\n", encoding="utf-8")
        console.print(f"[green][OK][/green] wrote {target}")
    else:
        print("[WARN] not written; pass --write to update Claude config")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
