#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.config import PROJECT_ROOT, load_settings, record_embedding_dimension


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--soft", action="store_true")
    group.add_argument("--hard", action="store_true")
    args = parser.parse_args()

    if args.soft:
        return soft_reset()
    return hard_reset()


def soft_reset() -> int:
    raw_dir = PROJECT_ROOT / "eval" / "results" / "raw"
    if raw_dir.exists():
        for path in raw_dir.iterdir():
            if path.name == ".gitkeep":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    console.print("[green][OK][/green] cleared eval/results/raw")
    console.print("[yellow][WARN][/yellow] Cognee metadata prune is package-version specific; use hard reset for a full store reset.")
    return 0


def hard_reset() -> int:
    data_dir = PROJECT_ROOT / ".data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    console.print("[green][OK][/green] deleted ./.data")

    if shutil.which("docker"):
        subprocess.run(["docker", "compose", "down"], cwd=PROJECT_ROOT, check=False)
        subprocess.run(["docker", "compose", "up", "-d"], cwd=PROJECT_ROOT, check=False)
        console.print("[green][OK][/green] restarted docker compose")
    else:
        console.print("[yellow][WARN][/yellow] docker not found; Neo4j was not restarted")

    if os.getenv("RECORD_EMBEDDING_DIMENSION_AFTER_RESET", "true").lower() in {
        "1",
        "true",
        "yes",
    }:
        record_embedding_dimension(load_settings())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

