from __future__ import annotations

from typing import Any, Protocol

from memory_stack.brain_store import BrainStore, content_hash
from memory_stack.cognee.serializers import (
    node_sets_for_memory,
    node_sets_for_source,
    serialize_memory_for_cognee,
    serialize_source_for_cognee,
)
from memory_stack.cognee_adapter import remember_text, run_async
from memory_stack.cfg import Settings, load_settings


class ProjectionAdapter(Protocol):
    def remember_text(
        self,
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> Any:
        ...


class DefaultCogneeProjectionAdapter:
    def remember_text(
        self,
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> Any:
        return run_async(
            remember_text(
                text,
                dataset_name=dataset_name,
                node_set=node_set,
                settings=settings,
            )
        )


def project_memory(
    memory_id: str,
    *,
    store: BrainStore | None = None,
    settings: Settings | None = None,
    adapter: ProjectionAdapter | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    active_adapter = adapter or DefaultCogneeProjectionAdapter()
    memory = active_store.get_memory(memory_id)
    if memory is None:
        raise ValueError(f"Memory not found: {memory_id}")
    text = serialize_memory_for_cognee(memory_id, store=active_store)
    node_set = node_sets_for_memory(memory)
    result = active_adapter.remember_text(
        text,
        dataset_name=active_settings.brain_cognee_memory_dataset,
        node_set=node_set,
        settings=active_settings,
    )
    return {
        "object_type": "memory",
        "object_id": memory_id,
        "dataset": active_settings.brain_cognee_memory_dataset,
        "projection_hash": content_hash(text, node_set),
        "cognee_reference": _reference_text(result),
        "result": result,
    }


def project_source(
    source_id: str,
    *,
    store: BrainStore | None = None,
    settings: Settings | None = None,
    adapter: ProjectionAdapter | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    active_adapter = adapter or DefaultCogneeProjectionAdapter()
    source = active_store.get_source(source_id, include_text=False)
    if source is None:
        raise ValueError(f"Source not found: {source_id}")
    text = serialize_source_for_cognee(source_id, store=active_store)
    node_set = node_sets_for_source(source)
    result = active_adapter.remember_text(
        text,
        dataset_name=active_settings.brain_cognee_sources_dataset,
        node_set=node_set,
        settings=active_settings,
    )
    return {
        "object_type": "source",
        "object_id": source_id,
        "dataset": active_settings.brain_cognee_sources_dataset,
        "projection_hash": content_hash(text, node_set),
        "cognee_reference": _reference_text(result),
        "result": result,
    }


def enqueue_projection(
    object_type: str,
    object_id: str,
    *,
    dataset: str,
    store: BrainStore,
    projection_hash: str,
) -> None:
    store.mark_cognee_pending(
        object_type=object_type,
        object_id=object_id,
        dataset=dataset,
        projection_hash=projection_hash,
    )


def mark_projection_stale(
    object_type: str,
    object_id: str,
    *,
    store: BrainStore,
    dataset: str | None = None,
    projection_hash: str | None = None,
) -> int:
    return store.mark_cognee_stale(
        object_type=object_type,
        object_id=object_id,
        dataset=dataset,
        projection_hash=projection_hash,
    )


def _reference_text(result: Any) -> str | None:
    if result is None:
        return None
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("id", "reference", "name"):
            if key in result:
                return str(result[key])
    return str(result)
