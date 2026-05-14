from __future__ import annotations

from typing import Any

from memory_stack.brain_store import BrainStore, now_utc
from memory_stack.cognee.projector import (
    ProjectionAdapter,
    project_memory,
    project_memory_async,
    project_source,
    project_source_async,
)
from memory_stack.cognee_adapter import ensure_datasources_ready, run_async
from memory_stack.cfg import Settings, load_settings


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

    sync_ids = [row["id"] for row in rows]
    if not sync_ids:
        return _summary([])

    if adapter is None:
        return run_async(
            _sync_pending_cognee_async(
                rows,
                settings=active_settings,
                store=active_store,
            )
        )

    results = [
        sync_one(
            sync_id,
            settings=active_settings,
            store=active_store,
            adapter=adapter,
        )
        for sync_id in sync_ids
    ]
    return _summary(results)


async def _sync_pending_cognee_async(
    rows: list[dict[str, Any]],
    *,
    settings: Settings,
    store: BrainStore,
) -> dict[str, Any]:
    await ensure_datasources_ready(
        sorted({row["dataset"] for row in rows}),
        settings=settings,
    )
    results = []
    for row in rows:
        results.append(
            await _sync_row_async(
                row,
                settings=settings,
                store=store,
            )
        )
    return _summary(results)


async def _sync_row_async(
    row: dict[str, Any],
    *,
    settings: Settings,
    store: BrainStore,
) -> dict[str, Any]:
    skip_reason = _deleted_projection_reason(row, store=store)
    if skip_reason is not None:
        store.update_cognee_sync_status(
            row["id"],
            status="deleted",
            error_message=skip_reason,
        )
        return {
            "sync_id": row["id"],
            "object_type": row["object_type"],
            "object_id": row["object_id"],
            "dataset": row["dataset"],
            "status": "skipped",
            "skip_reason": skip_reason,
        }

    try:
        projection = await _project_row_async(
            row,
            settings=settings,
            store=store,
        )
        store.update_cognee_sync_status(
            row["id"],
            status="synced",
            projection_hash=projection["projection_hash"],
            cognee_reference=projection.get("cognee_reference"),
            error_message=None,
            last_synced_at=now_utc(),
        )
        return {
            "sync_id": row["id"],
            "object_type": row["object_type"],
            "object_id": row["object_id"],
            "dataset": row["dataset"],
            "status": "synced",
            "projection_hash": projection["projection_hash"],
            "cognee_reference": projection.get("cognee_reference"),
        }
    except Exception as exc:
        store.update_cognee_sync_status(
            row["id"],
            status="failed",
            error_message=str(exc),
        )
        return {
            "sync_id": row["id"],
            "object_type": row["object_type"],
            "object_id": row["object_id"],
            "dataset": row["dataset"],
            "status": "failed",
            "error_message": str(exc),
        }


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

    skip_reason = _deleted_projection_reason(row, store=active_store)
    if skip_reason is not None:
        active_store.update_cognee_sync_status(
            sync_id,
            status="deleted",
            error_message=skip_reason,
        )
        return {
            "sync_id": sync_id,
            "object_type": row["object_type"],
            "object_id": row["object_id"],
            "dataset": row["dataset"],
            "status": "skipped",
            "skip_reason": skip_reason,
        }

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
    sync_ids = [row["id"] for row in rows]
    if not sync_ids:
        return _summary([])
    if adapter is None:
        return run_async(
            _sync_pending_cognee_async(
                rows,
                settings=active_settings,
                store=active_store,
            )
        )
    results = [
        sync_one(
            sync_id,
            settings=active_settings,
            store=active_store,
            adapter=adapter,
        )
        for sync_id in sync_ids
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


async def _project_row_async(
    row: dict[str, Any],
    *,
    settings: Settings,
    store: BrainStore,
) -> dict[str, Any]:
    if row["object_type"] == "memory":
        return await project_memory_async(
            row["object_id"],
            settings=settings,
            store=store,
        )
    if row["object_type"] == "source":
        return await project_source_async(
            row["object_id"],
            settings=settings,
            store=store,
        )
    raise ValueError(f"Unsupported Cognee object_type: {row['object_type']}")


def _deleted_projection_reason(row: dict[str, Any], *, store: BrainStore) -> str | None:
    if row["object_type"] == "memory":
        memory = store.get_memory(row["object_id"])
        if memory is None:
            return f"Memory not found: {row['object_id']}"
        if memory.get("status") == "deleted":
            return f"Memory is deleted: {row['object_id']}"
        return None
    if row["object_type"] == "source":
        source = store.get_source(row["object_id"], include_text=False)
        if source is None:
            return f"Source not found: {row['object_id']}"
        if source.get("status") == "deleted":
            return f"Source is deleted: {row['object_id']}"
    return None


def _summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    succeeded = len([result for result in results if result.get("status") == "synced"])
    failed = len([result for result in results if result.get("status") == "failed"])
    skipped = len([result for result in results if result.get("status") == "skipped"])
    return {
        "status": "complete" if failed == 0 else "partial_failure",
        "processed": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }
