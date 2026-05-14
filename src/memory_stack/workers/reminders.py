from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from memory_stack.brain_store import BrainStore, normalize_name, now_utc
from memory_stack.cfg import Settings, load_settings


def list_due_open_loops(
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    now: datetime | None = None,
    include_recently_reminded: bool = False,
    recent_seconds: int = 60 * 60 * 24,
    limit: int = 20,
) -> list[dict[str, Any]]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    return active_store.list_due_open_loops(
        now=now,
        include_recently_reminded=include_recently_reminded,
        recent_seconds=recent_seconds,
        limit=limit,
    )


def mark_reminded(
    loop_id: str,
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    reminded_at: datetime | None = None,
    next_review_after: timedelta | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    active_reminded_at = reminded_at or now_utc()
    next_review_at = (
        active_reminded_at + next_review_after if next_review_after is not None else None
    )
    updated = active_store.mark_open_loop_reminded(
        loop_id,
        reminded_at=active_reminded_at,
        next_review_at=next_review_at,
    )
    return {
        "loop_id": loop_id,
        "status": "reminded" if updated else "not_found",
        "last_reminded_at": active_reminded_at,
        "next_review_at": next_review_at,
    }


def find_relevant_open_loops(
    query: str,
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    now: datetime | None = None,
    include_recently_reminded: bool = False,
    recent_seconds: int = 60 * 60 * 24,
    min_overlap: float = 0.15,
    limit: int = 20,
) -> list[dict[str, Any]]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    query_terms = _expanded_terms(normalize_name(query).split())
    if not query_terms:
        return []

    candidates = active_store.list_due_open_loops(
        now=now,
        include_recently_reminded=include_recently_reminded,
        recent_seconds=recent_seconds,
        limit=limit * 5,
    )
    scored: list[tuple[float, dict[str, Any]]] = []
    for loop in candidates:
        terms = _loop_terms(loop)
        if not terms:
            continue
        overlap = len(query_terms & terms) / len(query_terms | terms)
        topic_hit = bool(query_terms & set(loop.get("topics") or []))
        score = max(overlap, 1.0 if topic_hit else 0.0)
        if score >= min_overlap:
            scored.append((score, {**loop, "relevance_score": score}))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [loop for _score, loop in scored[:limit]]


def _loop_terms(loop: dict[str, Any]) -> set[str]:
    terms = _expanded_terms(normalize_name(loop.get("statement") or "").split())
    for topic in loop.get("topics") or []:
        terms.update(_expanded_terms(normalize_name(str(topic).replace("_", " ")).split()))
        terms.add(str(topic))
    return terms


def _expanded_terms(values: list[str]) -> set[str]:
    terms = set(values)
    for value in values:
        if len(value) > 3 and value.endswith("s"):
            terms.add(value[:-1])
    return terms
