from __future__ import annotations

from typing import Any

from memory_stack.brain_store import BrainStore, now_utc
from memory_stack.cognee.projector import ProjectionAdapter, project_memory, project_source
from memory_stack.config import Settings, load_settings


def sync_pending_cognee(
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    limit: int = 100,
    adapter: ProjectionAdapter | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    rows = active_store.list_cognee_sync(statuses=("pending", "stale"), limit=limit)
    if not active_settings.brain_cognee_enabled and adapter is None:
        return {
            "status": "disabled",
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": len(rows),
            "results": [],
        }

    results = [
        sync_one(
            row["id"],
            settings=active_settings,
            store=active_store,
            adapter=adapter,
        )
        for row in rows
    ]
    return _summary(results)


def sync_one(
    sync_id: str,
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    adapter: ProjectionAdapter | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    row = active_store.get_cognee_sync_by_id(sync_id)
    if row is None:
        raise ValueError(f"Cognee sync row not found: {sync_id}")

    try:
        projection = _project_row(
            row,
            settings=active_settings,
            store=active_store,
            adapter=adapter,
        )
        active_store.update_cognee_sync_status(
            sync_id,
            status="synced",
            projection_hash=projection["projection_hash"],
            cognee_reference=projection.get("cognee_reference"),
            error_message=None,
            last_synced_at=now_utc(),
        )
        return {
            "sync_id": sync_id,
            "object_type": row["object_type"],
            "object_id": row["object_id"],
            "dataset": row["dataset"],
            "status": "synced",
            "projection_hash": projection["projection_hash"],
            "cognee_reference": projection.get("cognee_reference"),
        }
    except Exception as exc:
        active_store.update_cognee_sync_status(
            sync_id,
            status="failed",
            error_message=str(exc),
        )
        return {
            "sync_id": sync_id,
            "object_type": row["object_type"],
            "object_id": row["object_id"],
            "dataset": row["dataset"],
            "status": "failed",
            "error_message": str(exc),
        }


def retry_failed(
    *,
    settings: Settings | None = None,
    store: BrainStore | None = None,
    limit: int = 100,
    adapter: ProjectionAdapter | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_settings()
    active_store = store or BrainStore(active_settings)
    rows = active_store.list_cognee_sync(statuses=("failed",), limit=limit)
    results = [
        sync_one(
            row["id"],
            settings=active_settings,
            store=active_store,
            adapter=adapter,
        )
        for row in rows
    ]
    return _summary(results)


def _project_row(
    row: dict[str, Any],
    *,
    settings: Settings,
    store: BrainStore,
    adapter: ProjectionAdapter | None,
) -> dict[str, Any]:
    if row["object_type"] == "memory":
        return project_memory(
            row["object_id"],
            settings=settings,
            store=store,
            adapter=adapter,
        )
    if row["object_type"] == "source":
        return project_source(
            row["object_id"],
            settings=settings,
            store=store,
            adapter=adapter,
        )
    raise ValueError(f"Unsupported Cognee object_type: {row['object_type']}")


def _summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    succeeded = len([result for result in results if result.get("status") == "synced"])
    failed = len([result for result in results if result.get("status") == "failed"])
    return {
        "status": "complete" if failed == 0 else "partial_failure",
        "processed": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": 0,
        "results": results,
    }
