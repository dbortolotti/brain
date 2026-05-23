from __future__ import annotations

import json
from typing import Any

from sqlalchemy import inspect

from memory_stack import brain_schema as schema
from memory_stack import brain_service
from memory_stack.brain_models import RememberRequest
from memory_stack.brain_service import (
    remember,
    review_recent,
    undo_last,
)
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.profile_context import remember_profile_context


def test_review_recent_returns_control_receipts_and_context_records(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    context = remember_profile_context(settings, statement="Daniele prefers concise plans.")

    review = review_recent(settings)

    assert review["external_receipts"][0]["id"] == receipt.ingestion_run_id
    assert review["context_records"][0]["id"] == context["id"]
    assert "ingestion_runs" not in review
    assert "memory_datapoints" not in review
    assert "sources" not in review
    assert_legacy_semantic_tables_absent(settings)


def test_undo_last_uses_cognee_forget_and_keeps_status_event_as_audit(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    forget_calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))
    monkeypatch.setattr(brain_service, "_cognee_forget", fake_cognee_forget(forget_calls))
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)

    result = undo_last(settings)

    assert result["status"] == "undone"
    assert result["source_receipt_id"] == receipt.ingestion_run_id
    assert result["forget_results"][0]["status"] == "forgotten"
    assert forget_calls == [
        {
            "data_id": "00000000-0000-0000-0000-000000000001",
            "dataset": settings.brain_cognee_memory_dataset,
            "everything": False,
            "memory_only": False,
        }
    ]
    assert json.loads(calls[-1]["text"])["datapoint_type"] == "BrainStatusEventDataPoint"
    undo_receipt = BrainStore(settings).get_external_receipt(result["receipt_id"])
    assert undo_receipt["tool_name"] == "brain_undo_last"
    assert undo_receipt["metadata_json"]["brain_db_semantic_rows_written"] is False
    assert result["deleted_objects"]
    assert_legacy_semantic_tables_absent(settings)


def fake_cognee(calls: list[dict[str, Any]]):
    def remember_text(
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> dict[str, Any]:
        del settings
        calls.append(
            {
                "text": text,
                "dataset_name": dataset_name,
                "node_set": node_set or [],
            }
        )
        return {"items": [{"id": f"00000000-0000-0000-0000-{len(calls):012d}"}]}

    return remember_text


def fake_cognee_forget(calls: list[dict[str, Any]]):
    def forget_cognee(
        *,
        data_id: str | None = None,
        dataset: str | None = None,
        everything: bool = False,
        memory_only: bool = False,
        settings: Settings | None = None,
    ) -> dict[str, Any]:
        del settings
        call = {
            "data_id": str(data_id) if data_id else None,
            "dataset": dataset,
            "everything": everything,
            "memory_only": memory_only,
        }
        calls.append(call)
        return {"status": "forgotten", **call}

    return forget_cognee


def assert_legacy_semantic_tables_absent(settings: Settings) -> None:
    store = BrainStore(settings)
    tables = set(inspect(store.engine).get_table_names())
    assert not {
        "ingestion_runs",
        "sources",
        "memory_cards",
        "relationships",
        "open_loops",
        "cognee_sync",
        "recall_logs",
    } & tables


def brain_test_settings(tmp_path) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_cognee_recall_enabled=True,
        brain_llm_enabled=False,
        brain_taste_enabled=False,
    )
