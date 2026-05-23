from __future__ import annotations

from typing import Any


def build_facts(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": memory["id"],
            "kind": memory["kind"],
            "statement": memory["statement"],
            "status": memory["status"],
            "confidence": memory["confidence"],
        }
        for memory in memories
    ]


def build_evidence(
    memories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": memory["id"],
            "quote": memory["statement"],
            "confidence": memory["confidence"],
            "status": memory["status"],
        }
        for memory in memories
    ]
