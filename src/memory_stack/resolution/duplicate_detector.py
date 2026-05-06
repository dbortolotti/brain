from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from memory_stack.brain_store import BrainStore


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class DuplicateMatch:
    target_memory_id: str
    target_statement: str
    confidence: str
    reason: str


def normalized_statement(value: str) -> str:
    return " ".join(TOKEN_RE.findall(value.casefold()))


def statement_tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.casefold()))


def lexical_overlap(left: str, right: str) -> float:
    left_tokens = statement_tokens(left)
    right_tokens = statement_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def find_duplicate_memory(
    store: BrainStore,
    memory: dict[str, Any],
    *,
    entity_ids: list[str],
    limit: int = 100,
) -> DuplicateMatch | None:
    statement = memory["statement"]
    normalized = normalized_statement(statement)
    if not normalized:
        return None

    candidates = _candidate_memories(store, entity_ids=entity_ids, limit=limit)
    for candidate in candidates:
        if candidate["id"] == memory["id"]:
            continue
        if normalized_statement(candidate["statement"]) == normalized:
            return DuplicateMatch(
                target_memory_id=candidate["id"],
                target_statement=candidate["statement"],
                confidence="high",
                reason="same_normalized_statement",
            )
    return None


def _candidate_memories(
    store: BrainStore,
    *,
    entity_ids: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for entity_id in entity_ids:
        for memory in store.list_memories_by_entity(entity_id, limit=limit):
            if memory["id"] in seen:
                continue
            seen.add(memory["id"])
            results.append(memory)
            if len(results) >= limit:
                return results
    return results
