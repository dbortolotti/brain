from __future__ import annotations

from datetime import datetime
from typing import Any

from memory_stack.config import Settings
from memory_stack.workers.reminders import find_relevant_open_loops, list_due_open_loops


def scheduled_digest(
    *,
    settings: Settings,
    now: datetime | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    loops = list_due_open_loops(settings=settings, now=now, limit=limit)
    return {
        "kind": "open_loop_digest",
        "count": len(loops),
        "open_loops": loops,
        "text": render_digest(loops),
    }


def opportunistic_reminders(
    query: str,
    *,
    settings: Settings,
    now: datetime | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    loops = find_relevant_open_loops(query, settings=settings, now=now, limit=limit)
    return {
        "kind": "opportunistic_open_loops",
        "query": query,
        "count": len(loops),
        "open_loops": loops,
        "text": render_digest(loops),
    }


def render_digest(loops: list[dict[str, Any]]) -> str:
    if not loops:
        return "No open loops due."
    lines = ["Open loops due"]
    for loop in loops:
        lines.append(f"- {loop['statement']} [{loop['memory_id']}]")
    return "\n".join(lines)
