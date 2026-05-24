#!/usr/bin/env python3
from __future__ import annotations

import json

from memory_stack.cfg import load_settings
from memory_stack.taste.cognee_store import CogneePalateStore


def main() -> int:
    settings = load_settings()
    pruned = CogneePalateStore(settings).prune_deleted_items()
    print(
        json.dumps(
            {
                "status": "ok",
                "dataset": settings.brain_cognee_palate_dataset,
                "pruned_deleted_palate_items": pruned,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
