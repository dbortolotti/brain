from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from memory_stack.brain_store import BrainStore, normalize_name, normalize_user_id
from memory_stack.context_records import (
    context_id,
    context_record_payload,
    list_context_records,
    normalize_statement,
    remember_context_record,
    upsert_context_record,
)
from memory_stack.cfg import Settings


def list_profile_context(settings: Settings, *, user_id: str | None = None) -> list[dict[str, Any]]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    store = BrainStore(settings, user_id=active_user_id)
    _import_legacy_profile_context_file(settings, store=store, user_id=active_user_id)
    return list_context_records(settings, kind="profile", user_id=active_user_id)


def _import_legacy_profile_context_file(
    settings: Settings,
    *,
    store: BrainStore,
    user_id: str,
) -> None:
    path = _path(settings, user_id=user_id)
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Profile context file must contain a list: {path}")
    imported: list[dict[str, Any]] = []
    changed = False
    now = datetime.now(UTC).isoformat()
    for item in payload:
        if isinstance(item, str):
            statement = _normalize_statement(item)
            if not statement:
                changed = True
                continue
            scope = "answer_tailoring"
            imported.append(
                    _context_record_payload(
                        _upsert_profile_context_record(
                    store,
                    record_id=_context_id(statement, scope, user_id=user_id),
                    statement=statement,
                    scope=scope,
                    source="legacy_profile_context_string",
                    metadata_json={"legacy_profile_context_imported_at": now},
                )
                )
            )
            changed = True
            continue
        if not isinstance(item, dict):
            changed = True
            continue
        statement = _normalize_statement(str(item.get("statement") or ""))
        if not statement:
            changed = True
            continue
        record = dict(item)
        scope = str(record.get("scope") or "answer_tailoring").strip() or "answer_tailoring"
        if record.get("statement") != statement:
            record["statement"] = statement
            changed = True
        if record.get("scope") != scope:
            record["scope"] = scope
            changed = True
        if not record.get("id"):
            record["id"] = _context_id(statement, scope, user_id=user_id)
            changed = True
        imported.append(
            _context_record_payload(
                _upsert_profile_context_record(
                store,
                record_id=str(record["id"]),
                statement=statement,
                scope=scope,
                source=record.get("source"),
                metadata_json={
                    key: value
                    for key, value in record.items()
                    if key
                    not in {
                        "id",
                        "user_id",
                        "statement",
                        "scope",
                        "source",
                        "sync_status",
                        "created_at",
                        "updated_at",
                    }
                },
            )
            )
        )
    if changed:
        _write(settings, imported, user_id=user_id)


def remember_profile_context(
    settings: Settings,
    *,
    statement: str,
    scope: str = "answer_tailoring",
    source: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    normalized = normalize_statement(statement)
    if not normalized:
        raise ValueError("statement must not be blank.")
    normalized_scope = str(scope or "answer_tailoring").strip() or "answer_tailoring"
    context_id_value = _context_id(normalized, normalized_scope, user_id=active_user_id)
    store = BrainStore(settings, user_id=active_user_id)
    _import_legacy_profile_context_file(settings, store=store, user_id=active_user_id)
    existing = store.get_context_record(context_id_value)
    record = remember_context_record(
        settings,
        kind="profile",
        statement=normalized,
        scope=normalized_scope,
        source=source,
        user_id=active_user_id,
    )
    records = [_context_record_payload(item) for item in store.list_context_records(kind="profile", limit=10_000)]
    _write(settings, records, user_id=active_user_id)
    return {**record, "created": existing is None or existing.get("status") == "deleted"}


def forget_profile_context(
    settings: Settings,
    *,
    context_id: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    normalized_id = str(context_id).strip()
    if not normalized_id:
        raise ValueError("context_id must not be blank.")
    store = BrainStore(settings, user_id=active_user_id)
    _import_legacy_profile_context_file(settings, store=store, user_id=active_user_id)
    if not store.update_context_record_status(normalized_id, "deleted"):
        return {"id": normalized_id, "status": "not_found"}
    records = [_context_record_payload(item) for item in store.list_context_records(kind="profile", limit=10_000)]
    _write(settings, records, user_id=active_user_id)
    return {"id": normalized_id, "status": "deleted"}


def sync_profile_context(settings: Settings, *, user_id: str | None = None) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    records = list_profile_context(settings, user_id=active_user_id)
    return {
        "profile_context_count": len(records),
        "synced_count": len(records),
        "owner_entity_id": None,
        "profile_context": records,
    }


def sync_profile_context_record(
    settings: Settings,
    record: dict[str, Any],
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    store = BrainStore(settings, user_id=active_user_id)
    saved = _upsert_profile_context_record(
        store,
        record_id=str(record["id"]),
        statement=str(record["statement"]),
        scope=str(record.get("scope") or "answer_tailoring"),
        source=record.get("source"),
        metadata_json={
            key: value
            for key, value in record.items()
            if key not in {"id", "user_id", "statement", "scope", "source"}
        },
    )
    return _context_record_payload(saved)


def _upsert_profile_context_record(
    store: BrainStore,
    *,
    record_id: str,
    statement: str,
    scope: str,
    source: str | None,
    metadata_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return upsert_context_record(
        store,
        record_id=record_id,
        kind="profile",
        statement=statement,
        scope=scope,
        source=source,
        metadata_json={
            **(metadata_json or {}),
            "control_store": "brain_context_records",
            "semantic_projection": "cognee_optional",
        },
    )


def _context_record_payload(record: dict[str, Any]) -> dict[str, Any]:
    return context_record_payload(record)


def ensure_owner_entity(
    settings: Settings,
    *,
    store: BrainStore | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    active_store = store or BrainStore(settings, user_id=active_user_id)
    canonical_name = settings.brain_owner_full_name.strip() or settings.brain_owner_name.strip()
    if not canonical_name:
        raise ValueError("Brain owner name must not be blank.")
    entity, _created = active_store.create_entity(
        entity_type="person",
        canonical_name=canonical_name,
        normalized_name=normalize_name(canonical_name),
        confidence="high",
        metadata_json={
            "is_profile_owner": True,
            "profile_owner_id": active_user_id,
            "profile_user_id": active_user_id,
            "profile_name": settings.brain_owner_name,
            "profile_full_name": settings.brain_owner_full_name,
            "source": "brain_session",
        },
    )
    for alias in owner_aliases(settings):
        active_store.add_entity_alias(entity_id=entity["id"], alias=alias, confidence="high")
    return active_store.get_entity(entity["id"]) or entity


def owner_aliases(settings: Settings) -> list[str]:
    aliases = [settings.brain_owner_full_name, "me", "myself", "the user", "profile owner"]
    return [alias for alias in aliases if alias and normalize_name(alias) != normalize_name(settings.brain_owner_name)]


def _normalize_statement(statement: str) -> str:
    return normalize_statement(statement)


def _context_id(statement: str, scope: str, *, user_id: str) -> str:
    return context_id("profile", statement, scope, user_id=user_id)


def _path(settings: Settings, *, user_id: str) -> Path:
    path = Path(settings.brain_profile_context_path).expanduser()
    if user_id == "default":
        return path
    return path.with_name(f"{path.stem}.{user_id}{path.suffix or '.json'}")


def _write(settings: Settings, records: list[dict[str, Any]], *, user_id: str) -> None:
    path = _path(settings, user_id=user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
