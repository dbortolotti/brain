#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from memory_stack.cfg import load_settings
from memory_stack.cognee_adapter import cognify_dataset, run_async


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Cognee cognify over the configured Brain datasets."
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        default=None,
        help=(
            "Dataset name to cognify (repeatable). Defaults to the configured "
            "memory, sources, and data datasets."
        ),
    )
    parser.add_argument("--no-temporal", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    requested = args.datasets or [
        settings.brain_cognee_memory_dataset,
        settings.brain_cognee_sources_dataset,
        settings.brain_cognee_data_dataset,
    ]
    datasets = [name for name in dict.fromkeys(item.strip() for item in requested) if name]

    results: list[dict[str, str]] = []
    failures = 0
    for dataset in datasets:
        try:
            run_async(
                cognify_dataset(dataset, temporal=not args.no_temporal, settings=settings)
            )
        except Exception as exc:
            failures += 1
            results.append({"dataset": dataset, "status": "failed", "error": str(exc)})
        else:
            results.append({"dataset": dataset, "status": "ok"})

    print(
        json.dumps(
            {"status": "failed" if failures else "ok", "datasets": results},
            sort_keys=True,
        ),
        flush=True,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
