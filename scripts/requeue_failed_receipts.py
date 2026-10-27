"""Replay brain_remember receipts whose Cognee write failed.

Brain keeps the original request on every background receipt
(``metadata_json.queued_request``) and requeues a failed receipt only when
the identical request is sent again. After an LLM outage (2026-09-08..28
gpt-5.4-mini, 2026-10-21..25 gpt-5.5 dropped by the Codex backend) nothing
re-sends those requests, so the notes stay out of Cognee while their
receipts read ``failed``. This script requeues them from the stored payload
and processes them one at a time in this process, so the server's own
ingest pool and event loop are untouched.

Receipts without a stored payload (older code) are reported and skipped.

Usage (on the host, as the service user, with the service env):
    python scripts/requeue_failed_receipts.py --user daniele --dry-run
    python scripts/requeue_failed_receipts.py --user daniele --limit 5
    python scripts/requeue_failed_receipts.py --user daniele --since 2026-10-21
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable

from memory_stack.brain_service import _process_queued_remember
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings, load_settings

REQUEUE_SUMMARY = "Requeued by scripts/requeue_failed_receipts.py."


def failed_remember_receipts(
    store: BrainStore,
    *,
    since: datetime | None,
    limit: int,
) -> list[dict[str, Any]]:
    rows = store.list_external_receipts(status="failed", action="remember", limit=5000)
    rows = [r for r in rows if r.get("tool_name") == "brain_remember"]
    if since is not None:
        rows = [r for r in rows if _created_at(r) is not None and _created_at(r) >= since]
    rows.sort(key=lambda r: str(r.get("created_at")))  # oldest first
    return rows[:limit]


def _created_at(row: dict[str, Any]) -> datetime | None:
    value = row.get("created_at")
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def requeue_failed(
    settings: Settings,
    *,
    since: datetime | None = None,
    limit: int = 1000,
    dry_run: bool = False,
    receipt_ids: list[str] | None = None,
    process: Callable[[str, Settings], Any] = _process_queued_remember,
    log: Callable[[str], None] = print,
) -> dict[str, int]:
    store = BrainStore(settings)
    if receipt_ids:
        rows = [r for rid in receipt_ids if (r := store.get_external_receipt(rid)) is not None]
    else:
        rows = failed_remember_receipts(store, since=since, limit=limit)
    counts = {"candidates": len(rows), "skipped_no_payload": 0, "synced": 0, "failed": 0}
    for row in rows:
        receipt_id = str(row["id"])
        metadata = row.get("metadata_json")
        metadata = metadata if isinstance(metadata, dict) else {}
        if not isinstance(metadata.get("queued_request"), dict):
            counts["skipped_no_payload"] += 1
            log(f"skip  {receipt_id} {row.get('created_at')} no stored request payload")
            continue
        if dry_run:
            log(f"would {receipt_id} {row.get('created_at')} {metadata.get('classification')}")
            continue
        store.update_external_receipt(
            receipt_id,
            status="queued",
            summary=REQUEUE_SUMMARY,
            warnings_json=[],
        )
        started = time.perf_counter()
        try:
            result = process(receipt_id, settings)
        except Exception as exc:  # the receipt is already marked failed by the processor
            counts["failed"] += 1
            log(f"fail  {receipt_id} {type(exc).__name__}: {str(exc)[:160]}")
            continue
        status = getattr(result, "cognee_sync_status", "?")
        if status == "synced":
            counts["synced"] += 1
        else:
            counts["failed"] += 1
        log(f"{status:5s} {receipt_id} {metadata.get('classification')} {time.perf_counter() - started:.0f}s")
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--user", default=None, help="Brain user id whose receipts to replay (default: settings).")
    parser.add_argument("--since", default=None, help="Only receipts created on/after this date (YYYY-MM-DD).")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--ids", default=None, help="Comma-separated receipt ids (overrides --since/--limit).")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    settings = load_settings()
    if args.user:
        settings = settings.model_copy(update={"brain_user_id": args.user})
    since = (
        datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since else None
    )
    ids = [x.strip() for x in args.ids.split(",") if x.strip()] if args.ids else None
    counts = requeue_failed(settings, since=since, limit=args.limit, dry_run=args.dry_run, receipt_ids=ids)
    print(f"done user={settings.brain_user_id} {counts}")
    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
