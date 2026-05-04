from __future__ import annotations

from typing import Any

from memory_stack.io import to_jsonable


def result_to_text(result: Any) -> str:
    value = to_jsonable(result)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(result_to_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {result_to_text(val)}" for key, val in value.items())
    return str(value)


def score_must_include(result_text: str, must_include: list[str]) -> float:
    if not must_include:
        return 1.0
    lower = result_text.lower()
    hits = sum(1 for term in must_include if term.lower() in lower)
    return hits / len(must_include)


def score_result(result: Any, must_include: list[str]) -> dict[str, Any]:
    result_text = result_to_text(result)
    inclusion_score = score_must_include(result_text, must_include)
    missing = [term for term in must_include if term.lower() not in result_text.lower()]
    return {
        "score": inclusion_score,
        "method": "must_include_v1",
        "missing": missing,
        "notes": "Manual rubric review still required for contradiction/current-state quality.",
    }

