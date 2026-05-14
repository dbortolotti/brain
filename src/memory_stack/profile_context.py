from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from memory_stack.brain_store import BrainStore, content_hash, normalize_name
from memory_stack.cfg import Settings


def list_profile_context(settings: Settings) -> list[dict[str, Any]]:
    path = _path(settings)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Profile context file must contain a list: {path}")
    records = [record for record in payload if isinstance(record, dict) and record.get("statement")]
    changed = False
    for record in records:
        if "sync_status" not in record:
            record["sync_status"] = "pending"
            changed = True
    if changed:
        _write(settings, records)
    return records


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
            old_memory_id = record.get("memory_id")
            record.update(
                {
                    "statement": normalized,
                    "scope": normalized_scope,
                    "source": source,
                    "sync_status": "pending",
                    "updated_at": now,
                }
            )
            if old_memory_id:
                record["previous_memory_id"] = old_memory_id
                record.pop("memory_id", None)
            _write(settings, records)
            synced = sync_profile_context_record(settings, record)
            return {**synced, "created": False}
    record = {
        "id": context_id,
        "statement": normalized,
        "scope": normalized_scope,
        "source": source,
        "sync_status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    records.append(record)
    _write(settings, records)
    synced = sync_profile_context_record(settings, record)
    return {**synced, "created": True}


def forget_profile_context(settings: Settings, *, context_id: str) -> dict[str, Any]:
    normalized_id = str(context_id).strip()
    if not normalized_id:
        raise ValueError("context_id must not be blank.")
    records = list_profile_context(settings)
    kept = [record for record in records if record.get("id") != normalized_id]
    if len(kept) == len(records):
        return {"id": normalized_id, "status": "not_found"}
    removed = next(record for record in records if record.get("id") == normalized_id)
    memory_id = removed.get("memory_id")
    if memory_id:
        BrainStore(settings).update_memory_status(str(memory_id), "deleted")
    _write(settings, kept)
    return {"id": normalized_id, "status": "deleted"}


def sync_profile_context(settings: Settings) -> dict[str, Any]:
    records = list_profile_context(settings)
    synced: list[dict[str, Any]] = []
    for record in records:
        synced.append(sync_profile_context_record(settings, record))
    _write(settings, synced)
    return {
        "profile_context_count": len(synced),
        "synced_count": len([record for record in synced if record.get("sync_status") == "synced"]),
        "owner_entity_id": synced[0].get("owner_entity_id") if synced else ensure_owner_entity(settings)["id"],
        "profile_context": synced,
    }


def sync_profile_context_record(settings: Settings, record: dict[str, Any]) -> dict[str, Any]:
    store = BrainStore(settings)
    owner_entity = ensure_owner_entity(settings, store=store)
    previous_memory_id = record.pop("previous_memory_id", None)
    if previous_memory_id:
        store.update_memory_status(str(previous_memory_id), "deleted")
    memory, _created = store.upsert_memory_card(
        {
            "kind": "person_fact",
            "statement": record["statement"],
            "confidence": "high",
            "status": "current",
            "metadata_json": {
                "profile_context_id": record["id"],
                "profile_context_scope": record.get("scope"),
                "profile_context_source": record.get("source"),
                "profile_owner_entity_id": owner_entity["id"],
                "is_profile_context_projection": True,
            },
            "content_hash": content_hash("profile_context", record["id"], record["statement"]),
        }
    )
    store.link_memory_entity(
        memory_id=memory["id"],
        entity_id=owner_entity["id"],
        role="profile_owner",
        confidence="high",
    )
    projection_hash = content_hash(memory["id"], memory["statement"], memory["status"])
    store.mark_cognee_pending(
        object_type="memory",
        object_id=memory["id"],
        dataset=settings.brain_cognee_memory_dataset,
        projection_hash=projection_hash,
    )
    updated = {
        **record,
        "memory_id": memory["id"],
        "owner_entity_id": owner_entity["id"],
        "sync_status": "synced",
        "sync_error": None,
        "synced_at": datetime.now(UTC).isoformat(),
    }
    records = list_profile_context(settings)
    replaced = False
    for index, existing in enumerate(records):
        if existing.get("id") == updated["id"]:
            records[index] = updated
            replaced = True
            break
    if not replaced:
        records.append(updated)
    _write(settings, records)
    return updated


def ensure_owner_entity(settings: Settings, *, store: BrainStore | None = None) -> dict[str, Any]:
    active_store = store or BrainStore(settings)
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
            "profile_owner_id": "default",
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
