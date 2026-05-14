from __future__ import annotations

from typing import Any

from memory_stack.brain_store import BrainStore, content_hash
from memory_stack.cognee.serializers import (
    serialize_memory_for_cognee,
    serialize_source_for_cognee,
)
from memory_stack.cognee.sync_worker import sync_pending_cognee
from memory_stack.cfg import Settings, load_settings


def rebuild_cognee(
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    dataset: str = "all",
    prune_first: bool = False,
    confirm: bool = False,
    sync: bool = False,
    adapter: Any = None,
) -> dict[str, Any]:
    if prune_first and not confirm:
        raise ValueError("rebuild_cognee requires confirm=true when prune_first=true.")

    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    memory_count = 0
    source_count = 0

    if dataset in {"all", "memory", active_settings.brain_cognee_memory_dataset}:
        for memory in active_store.list_memory_cards(include_deleted=False, limit=100_000):
            text = serialize_memory_for_cognee(memory["id"], store=active_store)
            _mark_stale(
                active_store,
                object_type="memory",
                object_id=memory["id"],
                dataset=active_settings.brain_cognee_memory_dataset,
                projection_hash=content_hash(text),
            )
            memory_count += 1

    if dataset in {"all", "sources", "source", active_settings.brain_cognee_sources_dataset}:
        for source in active_store.list_sources(include_deleted=False, limit=100_000):
            text = serialize_source_for_cognee(source["id"], store=active_store)
            _mark_stale(
                active_store,
                object_type="source",
                object_id=source["id"],
                dataset=active_settings.brain_cognee_sources_dataset,
                projection_hash=content_hash(text),
            )
            source_count += 1

    sync_result = None
    if sync:
        sync_result = sync_pending_cognee(
            settings=active_settings,
            store=active_store,
            adapter=adapter,
        )

    return {
        "status": "queued",
        "dataset": dataset,
        "prune_first": prune_first,
        "pruned": bool(prune_first and confirm),
        "memory_rows_marked_stale": memory_count,
        "source_rows_marked_stale": source_count,
        "sync": sync_result,
    }


def _mark_stale(
    store: BrainStore,
    *,
    object_type: str,
    object_id: str,
    dataset: str,
    projection_hash: str,
) -> None:
    store.mark_cognee_pending(
        object_type=object_type,
        object_id=object_id,
        dataset=dataset,
        projection_hash=projection_hash,
    )
    store.mark_cognee_stale(
        object_type=object_type,
        object_id=object_id,
        dataset=dataset,
        projection_hash=projection_hash,
    )
