from __future__ import annotations

from typing import Any


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
