from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from memory_stack.brain_store import BrainStore
from memory_stack.resolution.duplicate_detector import (
    find_duplicate_memory,
    normalized_statement,
)


LIKE_RE = re.compile(r"^(?P<subject>.+?)\s+likes\s+(?P<object>[^.]+)\.?$", re.IGNORECASE)
LIKE_CORRECTION_RE = re.compile(
    r"^Actually,\s+(?P<subject>.+?)\s+likes\s+(?P<object>.+?),\s+not\s+(?P<negated>[^.]+)\.?$",
    re.IGNORECASE,
)
INTERACTION_LIKES_RE = re.compile(
    r"^(?P<subject>.+?)\s+mentioned\s+that\s+(?:he|she|they)\s+likes?\s+(?P<object>[^.]+)\.?$",
    re.IGNORECASE,
)
WORKS_AT_RE = re.compile(
    r"^(?P<subject>.+?)\s+works\s+at\s+(?P<org>[^.]+)\.?$",
    re.IGNORECASE,
)
LEFT_JOINED_RE = re.compile(
    r"^(?P<subject>.+?)\s+left\s+(?P<old_org>.+?)\s+and\s+joined\s+(?P<new_org>[^.]+)\.?$",
    re.IGNORECASE,
)
CHILDREN_RE = re.compile(
    r"^(?P<subject>.+?)\s+has\s+(?P<count>no|zero|one|two|three|four|five|\d+)\s+children\.?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedFact:
    fact_type: str
    subject: str
    value: str | None = None
    negated_value: str | None = None
    previous_value: str | None = None
    count: int | None = None


def detect_and_apply_memory_resolution(
    store: BrainStore,
    memory_id: str,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    memory = store.get_memory(memory_id)
    if memory is None:
        return []

    all_entity_ids = [entity["entity_id"] for entity in memory.get("entities", [])]
    subject_entity_ids = [
        entity["entity_id"]
        for entity in memory.get("entities", [])
        if entity.get("role") == "subject"
    ] or all_entity_ids

    duplicate = find_duplicate_memory(
        store,
        memory,
        entity_ids=all_entity_ids,
        limit=limit,
    )
    if duplicate is not None:
        link, created = store.create_memory_link(
            from_memory_id=memory_id,
            relation="duplicates",
            to_memory_id=duplicate.target_memory_id,
            confidence=duplicate.confidence,
            metadata_json={"reason": duplicate.reason},
        )
        store.update_memory_status(memory_id, "archived")
        return [
            {
                "type": "duplicate",
                "relation": "duplicates",
                "memory_id": memory_id,
                "target_memory_id": duplicate.target_memory_id,
                "target_statement": duplicate.target_statement,
                "confidence": duplicate.confidence,
                "reason": duplicate.reason,
                "link_id": link["id"],
                "link_created": created,
                "status": "archived",
            }
        ]

    fact = parse_fact(memory["statement"])
    if fact is None or not subject_entity_ids:
        return []

    candidates = _candidate_memories(
        store,
        entity_ids=subject_entity_ids,
        current_memory_id=memory_id,
        limit=limit,
    )
    detections: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_fact = parse_fact(candidate["statement"])
        detection = classify_fact_pair(fact, candidate_fact)
        if detection is None:
            continue
        relation, reason, target_status = detection
        link, created = store.create_memory_link(
            from_memory_id=memory_id,
            relation=relation,
            to_memory_id=candidate["id"],
            confidence="high",
            metadata_json={"reason": reason},
        )
        if target_status is not None:
            store.update_memory_status(candidate["id"], target_status)
        detections.append(
            {
                "type": "conflict" if relation == "contradicts" else "supersession",
                "relation": relation,
                "memory_id": memory_id,
                "target_memory_id": candidate["id"],
                "target_statement": candidate["statement"],
                "confidence": "high",
                "reason": reason,
                "link_id": link["id"],
                "link_created": created,
                "target_status": target_status,
            }
        )
        if relation == "supersedes":
            break
    return detections


def classify_fact_pair(
    new_fact: ParsedFact,
    old_fact: ParsedFact | None,
) -> tuple[str, str, str | None] | None:
    if old_fact is None:
        return None
    if new_fact.fact_type == "like_correction" and old_fact.fact_type == "likes":
        if _same_value(new_fact.negated_value, old_fact.value):
            return ("supersedes", "explicit_correction_negates_prior_like", "superseded")
    if new_fact.fact_type == "employment_transition" and old_fact.fact_type == "works_at":
        if _same_value(new_fact.previous_value, old_fact.value):
            return ("supersedes", "employment_transition_replaces_prior_workplace", "superseded")
    if new_fact.fact_type == "children_count" and old_fact.fact_type == "children_count":
        if new_fact.count != old_fact.count:
            return ("contradicts", "children_count_mismatch", None)
    return None


def parse_fact(statement: str) -> ParsedFact | None:
    text = statement.strip()
    correction_match = LIKE_CORRECTION_RE.match(text)
    if correction_match:
        return ParsedFact(
            fact_type="like_correction",
            subject=correction_match.group("subject"),
            value=correction_match.group("object"),
            negated_value=correction_match.group("negated"),
        )
    interaction_match = INTERACTION_LIKES_RE.match(text)
    if interaction_match:
        return ParsedFact(
            fact_type="likes",
            subject=interaction_match.group("subject"),
            value=interaction_match.group("object"),
        )
    likes_match = LIKE_RE.match(text)
    if likes_match:
        return ParsedFact(
            fact_type="likes",
            subject=likes_match.group("subject"),
            value=likes_match.group("object"),
        )
    transition_match = LEFT_JOINED_RE.match(text)
    if transition_match:
        return ParsedFact(
            fact_type="employment_transition",
            subject=transition_match.group("subject"),
            value=transition_match.group("new_org"),
            previous_value=transition_match.group("old_org"),
        )
    works_match = WORKS_AT_RE.match(text)
    if works_match:
        return ParsedFact(
            fact_type="works_at",
            subject=works_match.group("subject"),
            value=works_match.group("org"),
        )
    children_match = CHILDREN_RE.match(text)
    if children_match:
        return ParsedFact(
            fact_type="children_count",
            subject=children_match.group("subject"),
            count=_count_value(children_match.group("count")),
        )
    return None


def _candidate_memories(
    store: BrainStore,
    *,
    entity_ids: list[str],
    current_memory_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    seen: set[str] = {current_memory_id}
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


def _same_value(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    return normalized_statement(left) == normalized_statement(right)


def _count_value(value: str) -> int:
    numbers = {
        "no": 0,
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }
    lowered = value.casefold()
    if lowered in numbers:
        return numbers[lowered]
    return int(value)
