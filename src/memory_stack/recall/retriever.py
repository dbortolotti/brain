from __future__ import annotations

import json
import re
from typing import Any

from memory_stack.brain_store import BrainStore, content_hash
from memory_stack.cognee_adapter import recall_text, run_async
from memory_stack.cfg import Settings


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
    del store, include_superseded, include_conflicts
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
    return raw_memories_from_cognee_result(result, limit=limit)


def cognee_payloads_from_result(result: Any) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    _collect_cognee_payloads(result, payloads)
    return payloads


def raw_memories_from_cognee_result(result: Any, *, limit: int = 20) -> list[dict[str, Any]]:
    memories: list[dict[str, Any]] = []
    seen: set[str] = set()
    for text in _iter_raw_text_chunks(result):
        normalized = _normalize_raw_text(text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        memories.append(
            {
                "id": f"cognee_raw_{content_hash(normalized)[:16]}",
                "kind": "cognee_raw",
                "statement": normalized,
                "status": "current",
                "confidence": "medium",
                "metadata_json": {"source": "cognee_raw_result"},
            }
        )
        if len(memories) >= limit:
            break
    return memories


def _collect_cognee_payloads(value: Any, payloads: list[dict[str, Any]]) -> None:
    if value is None:
        return
    if isinstance(value, dict):
        if isinstance(value.get("datapoint_type"), str):
            payloads.append(value)
        for key in ("text", "content", "chunk_text", "payload", "data", "document", "result"):
            if key in value:
                _collect_cognee_payloads(value[key], payloads)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _collect_cognee_payloads(item, payloads)
        return
    if isinstance(value, str):
        parsed = _parse_json_string(value)
        if parsed is not None:
            _collect_cognee_payloads(parsed, payloads)


def _iter_raw_text_chunks(value: Any) -> list[str]:
    chunks: list[str] = []
    _collect_raw_text_chunks(value, chunks)
    return chunks


def _collect_raw_text_chunks(value: Any, chunks: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        chunks.append(value)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _collect_raw_text_chunks(item, chunks)
        return
    if isinstance(value, dict):
        if isinstance(value.get("datapoint_type"), str):
            return
        for key in ("text", "content", "chunk_text", "payload", "data", "document", "result", "answer"):
            if key in value:
                _collect_raw_text_chunks(value[key], chunks)


def _normalize_raw_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    parsed = _parse_json_string(normalized)
    if parsed is not None:
        return json.dumps(parsed, ensure_ascii=True, sort_keys=True, default=str)
    return normalized


def _parse_json_string(value: str) -> Any | None:
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
