from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from memory_stack.cfg import Settings


def list_profile_context(settings: Settings) -> list[dict[str, Any]]:
    path = _path(settings)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Profile context file must contain a list: {path}")
    return [record for record in payload if isinstance(record, dict) and record.get("statement")]


def remember_profile_context(
    settings: Settings,
    *,
    statement: str,
    scope: str = "answer_tailoring",
    source: str | None = None,
) -> dict[str, Any]:
    normalized = _normalize_statement(statement)
    if not normalized:
        raise ValueError("statement must not be blank.")
    normalized_scope = str(scope or "answer_tailoring").strip() or "answer_tailoring"
    context_id = _context_id(normalized, normalized_scope)
    records = list_profile_context(settings)
    now = datetime.now(UTC).isoformat()
    for record in records:
        if record.get("id") == context_id:
            record.update(
                {
                    "statement": normalized,
                    "scope": normalized_scope,
                    "source": source,
                    "updated_at": now,
                }
            )
            _write(settings, records)
            return {**record, "created": False}
    record = {
        "id": context_id,
        "statement": normalized,
        "scope": normalized_scope,
        "source": source,
        "created_at": now,
        "updated_at": now,
    }
    records.append(record)
    _write(settings, records)
    return {**record, "created": True}


def forget_profile_context(settings: Settings, *, context_id: str) -> dict[str, Any]:
    normalized_id = str(context_id).strip()
    if not normalized_id:
        raise ValueError("context_id must not be blank.")
    records = list_profile_context(settings)
    kept = [record for record in records if record.get("id") != normalized_id]
    if len(kept) == len(records):
        return {"id": normalized_id, "status": "not_found"}
    _write(settings, kept)
    return {"id": normalized_id, "status": "deleted"}


def _normalize_statement(statement: str) -> str:
    return " ".join(str(statement).strip().split())


def _context_id(statement: str, scope: str) -> str:
    digest = hashlib.sha256(f"{scope}\0{statement.lower()}".encode("utf-8")).hexdigest()[:16]
    return f"profile_context_{digest}"


def _path(settings: Settings) -> Path:
    return Path(settings.brain_profile_context_path).expanduser()


def _write(settings: Settings, records: list[dict[str, Any]]) -> None:
    path = _path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
