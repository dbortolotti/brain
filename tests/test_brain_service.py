from __future__ import annotations

from typing import Any

from sqlalchemy import inspect

from memory_stack import brain_service
from memory_stack.brain_models import IngestSourceRequest, RememberRequest
from memory_stack.brain_service import ingest_source, remember
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings


def test_family_fact_is_sent_to_cognee_as_raw_text_without_legacy_rows(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = remember(RememberRequest(input="Nur and Sara are my twin daughters."), settings)

    assert calls[0]["text"] == "Nur and Sara are my twin daughters."
    assert receipt.entities == []
    assert calls[0]["dataset_name"] == "memory"
    assert_legacy_semantic_counts(settings)


def test_ingest_source_request_writes_raw_source_text_to_cognee(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    source_text = "# AI Memory\nAI memory systems need durable source evidence."

    ingest_source(
        IngestSourceRequest(
            source=source_text,
            source_kind="markdown",
        ),
        settings,
    )
    assert [call["dataset_name"] for call in calls] == [settings.brain_cognee_memory_dataset]
    assert calls[0]["text"] == source_text
    assert "brain" in calls[0]["node_set"]
    assert "brain_source" not in calls[0]["node_set"]
    assert "brain_memory" not in calls[0]["node_set"]
    assert_legacy_semantic_counts(settings)


def test_ingest_source_uses_cognee_remember_once(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Archive\nKeep as evidence only.",
            source_kind="markdown",
        ),
        settings,
    )
    assert [call["dataset_name"] for call in calls] == [settings.brain_cognee_memory_dataset]
    assert calls[0]["text"] == "# Archive\nKeep as evidence only."
    assert "brain_source" not in calls[0]["node_set"]
    assert "brain_memory" not in calls[0]["node_set"]
    receipt_row = BrainStore(settings).get_external_receipt(receipt.ingestion_run_id)
    assert receipt_row["cognee_result_json"]["objects"][0]["operation"] == "remember"
    assert_legacy_semantic_counts(settings)


def test_ingest_source_dry_run_does_not_call_cognee_or_write_rows(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Brain note\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            dry_run=True,
        ),
        settings,
    )

    assert receipt.dry_run is True
    assert receipt.cognee_sync_status == "not_applicable"
    assert calls == []
    assert BrainStore(settings).list_external_receipts() == []
    assert_legacy_semantic_counts(settings)


def test_ingest_source_background_returns_queued_receipt_without_control_rows(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    submitted: list[IngestSourceRequest] = []

    def fake_submit_background_ingest(request, active_settings, *, llm_client=None):
        del llm_client
        assert active_settings is settings
        submitted.append(request)
        return None

    monkeypatch.setattr(
        brain_service,
        "_submit_background_ingest",
        fake_submit_background_ingest,
    )

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Brain note\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            run_in_background=True,
        ),
        settings,
    )

    assert receipt.classification == "queued"
    assert receipt.cognee_sync_status == "queued"
    assert submitted
    assert submitted[0].run_in_background is False
    assert BrainStore(settings).list_external_receipts() == []
    assert_legacy_semantic_counts(settings)


def test_ingest_source_normalizes_before_background_decision(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path)
    submitted: list[IngestSourceRequest] = []
    seen_remember_requests: list[RememberRequest] = []

    def fake_should_run_in_background(request, remember_request, active_settings):
        assert active_settings is settings
        assert request.source == "Document text"
        seen_remember_requests.append(remember_request)
        return True

    def fake_submit_background_ingest(request, active_settings, *, llm_client=None):
        del llm_client
        assert active_settings is settings
        submitted.append(request)
        return None

    monkeypatch.setattr(
        brain_service,
        "_should_run_ingest_in_background",
        fake_should_run_in_background,
    )
    monkeypatch.setattr(
        brain_service,
        "_submit_background_ingest",
        fake_submit_background_ingest,
    )

    receipt = ingest_source(
        IngestSourceRequest(
            source="Document text",
            source_kind="markdown",
            metadata={"doc": "demo"},
            context={"client_session_id": "session-1"},
        ),
        settings,
    )

    assert receipt.classification == "queued"
    assert submitted
    assert seen_remember_requests
    normalized = seen_remember_requests[0]
    assert normalized.input == "Document text"
    assert normalized.input_type == "markdown"
    assert normalized.context["taste_skip"] is True
    assert normalized.context["source_ingest"] is True
    assert normalized.context["source_kind"] == "markdown"
    assert normalized.context["metadata"] == {"doc": "demo"}
    assert normalized.context["client_session_id"] == "session-1"


def test_ingest_source_auto_backgrounds_large_sources(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path).model_copy(
        update={"brain_ingest_background_auto_chars": 10}
    )
    submitted: list[IngestSourceRequest] = []

    def fake_submit_background_ingest(request, active_settings, *, llm_client=None):
        del llm_client
        assert active_settings is settings
        submitted.append(request)
        return None

    monkeypatch.setattr(
        brain_service,
        "_submit_background_ingest",
        fake_submit_background_ingest,
    )

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Brain note\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
        ),
        settings,
    )

    assert receipt.classification == "queued"
    assert receipt.cognee_sync_status == "queued"
    assert submitted
    assert submitted[0].run_in_background is False
    assert BrainStore(settings).list_external_receipts() == []


def test_ingest_source_explicit_false_overrides_auto_background(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path).model_copy(
        update={"brain_ingest_background_auto_chars": 10}
    )
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Brain note\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            run_in_background=False,
        ),
        settings,
    )

    assert receipt.classification == "markdown"
    assert receipt.cognee_sync_status == "synced"
    assert calls
    assert [call["dataset_name"] for call in calls] == [settings.brain_cognee_memory_dataset]
    assert calls[0]["text"] == "# Brain note\nKnowledge graphs matter for Brain."


def test_ingest_source_dry_run_overrides_auto_background(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path).model_copy(
        update={"brain_ingest_background_auto_chars": 10}
    )

    def fail_submit_background_ingest(*args, **kwargs):
        raise AssertionError("dry-run ingestion should not be queued")

    monkeypatch.setattr(
        brain_service,
        "_submit_background_ingest",
        fail_submit_background_ingest,
    )

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Brain note\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            dry_run=True,
        ),
        settings,
    )

    assert receipt.dry_run is True
    assert receipt.cognee_sync_status == "not_applicable"
    assert receipt.classification == "markdown"


def test_external_receipts_are_scoped_by_user_id(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'brain.db'}"
    settings_a = Settings(
        brain_database_url=db_url,
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_user_id="user_a",
        brain_llm_enabled=False,
        brain_taste_enabled=False,
    )
    settings_b = Settings(
        brain_database_url=db_url,
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_user_id="user_b",
        brain_llm_enabled=False,
        brain_taste_enabled=False,
    )
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt_a = remember(RememberRequest(input="Daniele prefers green tea."), settings_a)
    receipt_b = remember(RememberRequest(input="Daniele prefers green tea."), settings_b)

    assert receipt_a.ingestion_run_id != receipt_b.ingestion_run_id
    assert [
        receipt["id"] for receipt in BrainStore(settings_a).list_external_receipts()
    ] == [receipt_a.ingestion_run_id]
    assert [
        receipt["id"] for receipt in BrainStore(settings_b).list_external_receipts()
    ] == [receipt_b.ingestion_run_id]
    assert_legacy_semantic_counts(settings_a)
    assert_legacy_semantic_counts(settings_b)


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


def assert_legacy_semantic_counts(settings: Settings) -> None:
    table_names = set(inspect(BrainStore(settings).engine).get_table_names())
    assert {
        "sources",
        "memory_cards",
        "memory_entities",
        "memory_links",
        "relationships",
        "open_loops",
        "cognee_sync",
    }.isdisjoint(table_names)

def brain_test_settings(tmp_path) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_llm_enabled=False,
        brain_taste_enabled=False,
    )
