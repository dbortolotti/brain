from __future__ import annotations

import importlib.util
from pathlib import Path

from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings


def _load_script():
    path = Path("scripts/requeue_failed_receipts.py")
    spec = importlib.util.spec_from_file_location("requeue_failed_receipts", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}", brain_user_id="daniele")


def _failed_receipt(store: BrainStore, receipt_id: str, *, with_payload: bool) -> None:
    metadata = {"classification": "note"}
    if with_payload:
        metadata["queued_request"] = {"input": "replay me", "input_type": "note", "run_in_background": False}
    store.get_or_create_external_receipt(
        receipt_id=receipt_id,
        surface="api",
        tool_name="brain_remember",
        action="remember",
        status="failed",
        summary="Cognee write failed for note.",
        cognee_dataset="memory",
        metadata_json=metadata,
    )


def test_requeue_replays_failed_receipts_with_payload_and_skips_the_rest(tmp_path) -> None:
    script = _load_script()
    settings = _settings(tmp_path)
    store = BrainStore(settings)
    _failed_receipt(store, "rcpt_with_payload", with_payload=True)
    _failed_receipt(store, "rcpt_no_payload", with_payload=False)
    processed: list[str] = []

    class Result:
        cognee_sync_status = "synced"

    def fake_process(receipt_id: str, active_settings: Settings):
        # The script must hand the processor a receipt it already requeued.
        row = store.get_external_receipt(receipt_id)
        assert row is not None and row["status"] == "queued"
        assert row["summary"] == script.REQUEUE_SUMMARY
        processed.append(receipt_id)
        store.update_external_receipt(receipt_id, status="synced", summary="ok")
        return Result()

    logged: list[str] = []
    counts = script.requeue_failed(settings, process=fake_process, log=logged.append)

    assert processed == ["rcpt_with_payload"]
    assert counts == {"candidates": 2, "skipped_no_payload": 1, "synced": 1, "failed": 0}
    assert store.get_external_receipt("rcpt_no_payload")["status"] == "failed"
    assert any(line.startswith("skip  rcpt_no_payload") for line in logged)


def test_requeue_dry_run_changes_nothing(tmp_path) -> None:
    script = _load_script()
    settings = _settings(tmp_path)
    store = BrainStore(settings)
    _failed_receipt(store, "rcpt_with_payload", with_payload=True)
    calls: list[str] = []

    counts = script.requeue_failed(
        settings, dry_run=True, process=lambda rid, s: calls.append(rid), log=lambda _: None
    )

    assert calls == []
    assert counts["candidates"] == 1
    assert store.get_external_receipt("rcpt_with_payload")["status"] == "failed"


def test_requeue_counts_processor_failures(tmp_path) -> None:
    script = _load_script()
    settings = _settings(tmp_path)
    store = BrainStore(settings)
    _failed_receipt(store, "rcpt_a", with_payload=True)

    def boom(receipt_id: str, active_settings: Settings):
        store.update_external_receipt(receipt_id, status="failed", summary="still broken")
        raise RuntimeError("LLM down")

    counts = script.requeue_failed(settings, process=boom, log=lambda _: None)
    assert counts["failed"] == 1 and counts["synced"] == 0
    assert store.get_external_receipt("rcpt_a")["status"] == "failed"
