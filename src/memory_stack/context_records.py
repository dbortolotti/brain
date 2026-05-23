from __future__ import annotations

import hashlib
from typing import Any, Literal

from memory_stack.brain_store import BrainStore, normalize_user_id
from memory_stack.cfg import Settings

ContextKind = Literal["profile", "bias"]


def list_context_records(
    settings: Settings,
    *,
    kind: ContextKind,
    user_id: str | None = None,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    store = BrainStore(settings, user_id=active_user_id)
    return [
        context_record_payload(record)
        for record in store.list_context_records(
            kind=kind,
            include_deleted=include_deleted,
            limit=10_000,
        )
    ]


def remember_context_record(
    settings: Settings,
    *,
    kind: ContextKind,
    statement: str,
    scope: str,
    source: str | None = None,
    user_id: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    normalized = normalize_statement(statement)
    if not normalized:
        raise ValueError("statement must not be blank.")
    normalized_scope = str(scope or default_scope(kind)).strip() or default_scope(kind)
    record_id = context_id(kind, normalized, normalized_scope, user_id=active_user_id)
    store = BrainStore(settings, user_id=active_user_id)
    existing = store.get_context_record(record_id)
    record = upsert_context_record(
        store,
        record_id=record_id,
        kind=kind,
        statement=normalized,
        scope=normalized_scope,
        source=source,
        metadata_json={
            **(metadata_json or {}),
            "source_surface": f"brain_{kind}_context_remember",
        },
    )
    return {
        **context_record_payload(record),
        "created": existing is None or existing.get("status") == "deleted",
    }


def forget_context_record(
    settings: Settings,
    *,
    kind: ContextKind,
    context_id: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    normalized_id = str(context_id).strip()
    if not normalized_id:
        raise ValueError("context_id must not be blank.")
    store = BrainStore(settings, user_id=active_user_id)
    record = store.get_context_record(normalized_id)
    if record is None or record.get("kind") != kind:
        return {"id": normalized_id, "status": "not_found"}
    if not store.update_context_record_status(normalized_id, "deleted"):
        return {"id": normalized_id, "status": "not_found"}
    return {"id": normalized_id, "status": "deleted"}


def upsert_context_record(
    store: BrainStore,
    *,
    record_id: str,
    kind: ContextKind,
    statement: str,
    scope: str,
    source: str | None,
    metadata_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return store.create_context_record(
        record_id=record_id,
        kind=kind,
        statement=statement,
        scope=scope,
        source=source,
        status="current",
        metadata_json={
            **(metadata_json or {}),
            "control_store": "brain_context_records",
            "semantic_projection": "cognee_optional",
        },
    )


def context_record_payload(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata_json") if isinstance(record.get("metadata_json"), dict) else {}
    return {
        "id": record["id"],
        "user_id": record.get("user_id"),
        "kind": record.get("kind"),
        "statement": record["statement"],
        "scope": record.get("scope") or default_scope(record.get("kind")),
        "source": record.get("source"),
        "status": record.get("status") or "current",
        "sync_status": "control_store",
        "cognee_reference": record.get("cognee_reference"),
        "metadata": metadata,
        "created_at": isoformat(record.get("created_at")),
        "updated_at": isoformat(record.get("updated_at")),
    }


def normalize_statement(statement: str) -> str:
    return " ".join(str(statement).strip().split())


def context_id(kind: str, statement: str, scope: str, *, user_id: str) -> str:
    prefix = "profile_context" if kind == "profile" else "bias_context"
    digest = hashlib.sha256(f"{user_id}\0{kind}\0{scope}\0{statement.lower()}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def default_scope(kind: str | None) -> str:
    if kind == "bias":
        return "response_style"
    return "answer_tailoring"


def isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)

