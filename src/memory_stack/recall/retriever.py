from __future__ import annotations

import json
import re
from typing import Any

from memory_stack.brain_store import BrainStore
from memory_stack.cognee_adapter import recall_text, run_async
from memory_stack.config import Settings


MEMORY_ID_RE = re.compile(r"\bmem_[A-Za-z0-9]+\b")
SOURCE_ID_RE = re.compile(r"\bsrc_[A-Za-z0-9]+\b")


class DefaultCogneeSearchAdapter:
    def search(
        self,
        query: str,
        *,
        dataset: str,
        top_k: int,
        settings: Settings,
    ) -> Any:
        return run_async(
            recall_text(
                query=query,
                dataset=dataset,
                search_type="CHUNKS",
                top_k=top_k,
                settings=settings,
            )
        )


def retrieve_memories(
    store: BrainStore,
    query: str,
    *,
    settings: Settings | None = None,
    cognee_searcher: Any = None,
    include_superseded: bool = False,
    include_conflicts: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    db_results = store.search_memory(
        query,
        include_superseded=include_superseded,
        include_conflicts=include_conflicts,
        limit=limit,
    )
    if len(db_results) >= limit:
        return db_results

    hydrated = retrieve_cognee_memories(
        store,
        query,
        settings=settings,
        cognee_searcher=cognee_searcher,
        include_superseded=include_superseded,
        include_conflicts=include_conflicts,
        limit=limit,
    )
    return _merge_memories(db_results, hydrated, limit=limit)


def retrieve_cognee_memories(
    store: BrainStore,
    query: str,
    *,
    settings: Settings | None,
    cognee_searcher: Any = None,
    include_superseded: bool = False,
    include_conflicts: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    if settings is None:
        return []
    if not settings.brain_cognee_recall_enabled and cognee_searcher is None:
        return []
    searcher = cognee_searcher or DefaultCogneeSearchAdapter()
    try:
        result = searcher.search(
            query,
            dataset=settings.brain_cognee_memory_dataset,
            top_k=settings.brain_cognee_recall_top_k,
            settings=settings,
        )
    except Exception:
        return []

    memory_ids, _source_ids = extract_brain_ids_from_cognee_result(result)
    memories: list[dict[str, Any]] = []
    for memory_id in memory_ids:
        memory = store.get_memory(memory_id)
        if memory is None:
            continue
        if not _visible_memory(
            memory,
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
        ):
            continue
        memories.append(memory)
        if len(memories) >= limit:
            break
    return memories


def retrieve_open_loops(
    store: BrainStore,
    *,
    topic: str | None = None,
    status: str = "open",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return store.list_open_loops(topic=topic, status=status, limit=limit)


def extract_brain_ids_from_cognee_result(result: Any) -> tuple[list[str], list[str]]:
    text = _result_text(result)
    return (_unique(MEMORY_ID_RE.findall(text)), _unique(SOURCE_ID_RE.findall(text)))


def _result_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=True, sort_keys=True, default=str)
    except TypeError:
        return str(result)


def _merge_memories(
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for memory in [*primary, *secondary]:
        if memory["id"] in seen:
            continue
        seen.add(memory["id"])
        merged.append(memory)
        if len(merged) >= limit:
            break
    return merged


def _visible_memory(
    memory: dict[str, Any],
    *,
    include_superseded: bool,
    include_conflicts: bool,
) -> bool:
    status = memory["status"]
    if status == "current":
        return True
    if status == "conflicted":
        return include_conflicts
    if status == "superseded":
        return include_superseded
    return False


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
