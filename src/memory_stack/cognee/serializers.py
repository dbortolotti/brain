from __future__ import annotations

import json
from typing import Any

from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings, load_settings


def serialize_memory_for_cognee(
    memory_id: str,
    *,
    store: BrainStore | None = None,
    settings: Settings | None = None,
) -> str:
    active_store = store or BrainStore(settings or load_settings())
    memory = active_store.get_memory(memory_id)
    if memory is None:
        raise ValueError(f"Memory not found: {memory_id}")
    payload = {
        "brain_object_type": "memory",
        "memory_id": memory["id"],
        "kind": memory["kind"],
        "status": memory["status"],
        "confidence": memory["confidence"],
        "statement": memory["statement"],
        "summary": memory.get("summary"),
        "observed_at": memory.get("observed_at"),
        "source_id": memory.get("source_id"),
        "source_quote": memory.get("source_quote"),
        "topics": (memory.get("metadata_json") or {}).get("topics", []),
        "metadata": memory.get("metadata_json") or {},
        "entities": memory.get("entities", []),
        "relationships": memory.get("relationships", []),
        "links": memory.get("links", []),
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def serialize_source_for_cognee(
    source_id: str,
    *,
    store: BrainStore | None = None,
    settings: Settings | None = None,
    max_chars: int = 50_000,
) -> str:
    active_store = store or BrainStore(settings or load_settings())
    source = active_store.get_source(source_id, include_text=True, max_chars=max_chars)
    if source is None:
        raise ValueError(f"Source not found: {source_id}")
    payload = {
        "brain_object_type": "source",
        "source_id": source["id"],
        "kind": source["kind"],
        "status": source["status"],
        "title": source.get("title"),
        "uri": source.get("uri"),
        "file_path": source.get("file_path"),
        "summary": source.get("summary"),
        "content_hash": source.get("content_hash"),
        "metadata": source.get("metadata_json") or {},
        "text": source.get("text"),
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def node_sets_for_memory(memory: dict[str, Any]) -> list[str]:
    metadata = memory.get("metadata_json") or {}
    node_sets = [
        "brain_memory",
        f"memory_kind:{memory.get('kind')}",
        f"memory_status:{memory.get('status')}",
    ]
    for topic in metadata.get("topics", []):
        node_sets.append(f"topic:{topic}")
    for entity in memory.get("entities", []):
        node_sets.append(f"entity:{entity.get('entity_id')}")
    return _dedupe_node_sets(node_sets)


def node_sets_for_source(source: dict[str, Any]) -> list[str]:
    node_sets = [
        "brain_source",
        f"source_kind:{source.get('kind')}",
        f"source_status:{source.get('status')}",
    ]
    metadata = source.get("metadata_json") or {}
    for topic in metadata.get("topics", []):
        node_sets.append(f"topic:{topic}")
    return _dedupe_node_sets(node_sets)


def _dedupe_node_sets(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
