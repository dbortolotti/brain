from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from memory_stack.models import EvalQuery, MemoryItem


def load_memory_items(path: str | Path) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(MemoryItem.model_validate(json.loads(line)))
            except Exception as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
    return items


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(data), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return to_jsonable(value.dict())
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def load_eval_queries(path: str | Path) -> list[EvalQuery]:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    return [EvalQuery.model_validate(query) for query in payload.get("queries", [])]

