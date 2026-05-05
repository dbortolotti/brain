from __future__ import annotations

from typing import Any


def render_open_loops(loops: list[dict[str, Any]]) -> str:
    if not loops:
        return "No open loops found."
    lines = ["Open loops"]
    for loop in loops:
        lines.append(f"- {loop['statement']} [{loop['memory_id']}]")
    return "\n".join(lines)


def render_memory_answer(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return "No matching memories found."
    lines = ["Known memories"]
    for memory in memories:
        lines.append(
            f"- {memory['statement']} "
            f"[{memory['id']}; {memory['kind']}; {memory['confidence']}]"
        )
    return "\n".join(lines)
