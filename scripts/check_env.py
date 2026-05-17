#!/usr/bin/env python3
from __future__ import annotations

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cfg import check_embedding_dimension_change, load_settings, repo_path


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Brain runtime configuration.")
    parser.add_argument("--env", choices=["dev", "staging", "prod"], default=None, help="Config profile to load.")
    args = parser.parse_args()

    settings = load_settings(config_env=args.env)

    console.print(f"[green][OK][/green] profile={settings.profile}")
    console.print(f"[green][OK][/green] llm={format_provider_model(settings.llm_provider, settings.llm_model)}")
    console.print(
        "[green][OK][/green] "
        f"embeddings={format_provider_model(settings.embedding_provider, settings.embedding_model)}"
    )
    console.print(
        f"[green][OK][/green] graph={settings.graph_database_provider} "
        f"{settings.graph_database_url}"
    )
    console.print(
        f"[green][OK][/green] vector={settings.vector_db_provider} {settings.vector_db_url}"
    )
    console.print(f"[green][OK][/green] db={settings.db_provider} {settings.db_name}")
    console.print(
        f"[green][OK][/green] system_root={repo_path(settings.system_root_directory)}"
    )
    console.print(f"[green][OK][/green] data_root={repo_path(settings.data_root_directory)}")
    console.print(
        f"[green][OK][/green] curated_mcp=http://{settings.brain_mcp_host}:"
        f"{settings.brain_mcp_port}{settings.brain_mcp_path}"
    )
    console.print(
        f"[green][OK][/green] admin_mcp=http://{settings.brain_mcp_host}:"
        f"{settings.brain_mcp_port}{settings.brain_admin_mcp_path}"
    )

    ok, message = check_embedding_dimension_change(settings)
    style = "green" if ok else "red"
    label = "OK" if ok else "FAIL"
    console.print(f"[{style}][{label}][/{style}] {message}")
    return 0 if ok else 1


def format_provider_model(provider: str, model: str) -> str:
    if model.startswith(f"{provider}/"):
        return model
    return f"{provider}/{model}"


if __name__ == "__main__":
    raise SystemExit(main())
