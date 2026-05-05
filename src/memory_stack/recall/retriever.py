from __future__ import annotations

from typing import Any

from memory_stack.brain_store import BrainStore


def retrieve_memories(
    store: BrainStore,
    query: str,
    *,
    include_superseded: bool = False,
    include_conflicts: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    return store.search_memory(
        query,
        include_superseded=include_superseded,
        include_conflicts=include_conflicts,
        limit=limit,
    )


def retrieve_open_loops(
    store: BrainStore,
    *,
    topic: str | None = None,
    status: str = "open",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return store.list_open_loops(topic=topic, status=status, limit=limit)
