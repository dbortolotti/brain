from __future__ import annotations

from typing import Any

from memory_stack.taste.ranking import retrieve_candidates


def match_options(
    store: Any,
    *,
    intent: dict[str, Any],
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    return retrieve_candidates(store, intent, options)
