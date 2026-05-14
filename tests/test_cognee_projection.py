from __future__ import annotations

from typing import Any

from memory_stack.brain_models import IngestSourceRequest, RememberRequest
from memory_stack.brain_service import ingest_source, remember
from memory_stack.brain_store import BrainStore
from memory_stack.cognee.projector import project_memory, project_source
from memory_stack.cognee.sync_worker import sync_pending_cognee
from memory_stack.cfg import Settings


class FakeProjectionAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def remember_text(
        self,
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> dict[str, str]:
        del settings
        if self.fail:
            raise RuntimeError("cognee unavailable")
        self.calls.append(
            {
                "text": text,
                "dataset_name": dataset_name,
                "node_set": node_set or [],
            }
        )
        return {"id": f"fake-{len(self.calls)}"}


def test_memory_projection_contains_memory_id(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    adapter = FakeProjectionAdapter()

    projection = project_memory(
        receipt.memory_cards[0].id,
        settings=settings,
        adapter=adapter,
    )

    assert receipt.memory_cards[0].id in adapter.calls[0]["text"]
    assert "brain_memory" in adapter.calls[0]["node_set"]
    assert projection["cognee_reference"] == "fake-1"


def test_source_projection_contains_source_id(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = ingest_source(
        IngestSourceRequest(
            source="# Source\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            title="Knowledge graph note",
        ),
        settings,
    )
    adapter = FakeProjectionAdapter()

    project_source(receipt.source.source_id, settings=settings, adapter=adapter)

    assert receipt.source.source_id in adapter.calls[0]["text"]
    assert "brain_source" in adapter.calls[0]["node_set"]


def test_pending_sync_row_becomes_synced_after_fake_success(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    adapter = FakeProjectionAdapter()

    result = sync_pending_cognee(settings=settings, adapter=adapter)

    row = BrainStore(settings).get_cognee_sync(receipt.memory_cards[0].id)[0]
    assert result["succeeded"] == 1
    assert row["status"] == "synced"
    assert row["cognee_reference"] == "fake-1"


def test_failed_adapter_marks_sync_failed_and_preserves_brain_db(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    adapter = FakeProjectionAdapter(fail=True)

    result = sync_pending_cognee(settings=settings, adapter=adapter)

    store = BrainStore(settings)
    row = store.get_cognee_sync(receipt.memory_cards[0].id)[0]
    assert result["failed"] == 1
    assert row["status"] == "failed"
    assert "cognee unavailable" in row["error_message"]
    assert store.get_memory(receipt.memory_cards[0].id)["statement"] == "Sam likes Bill Evans."


def test_deleted_memory_sync_row_is_not_projected(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    store = BrainStore(settings)
    store.update_memory_status(receipt.memory_cards[0].id, "deleted")
    adapter = FakeProjectionAdapter()

    result = sync_pending_cognee(settings=settings, adapter=adapter)

    row = store.get_cognee_sync(receipt.memory_cards[0].id)[0]
    assert result["processed"] == 1
    assert result["skipped"] == 1
    assert result["succeeded"] == 0
    assert result["results"][0]["status"] == "skipped"
    assert "Memory is deleted" in result["results"][0]["skip_reason"]
    assert row["status"] == "deleted"
    assert "Memory is deleted" in row["error_message"]
    assert adapter.calls == []


def test_deleted_source_sync_row_is_not_projected(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    store = BrainStore(settings)
    source, _ = store.upsert_source(
        {
            "kind": "markdown",
            "title": "Knowledge graph note",
            "raw_text": "# Source\nKnowledge graphs matter for Brain.",
        }
    )
    store.mark_cognee_pending(
        object_type="source",
        object_id=source["id"],
        dataset=settings.brain_cognee_sources_dataset,
        projection_hash="sha256:test",
    )
    store.update_source_status(source["id"], "deleted")
    adapter = FakeProjectionAdapter()

    result = sync_pending_cognee(settings=settings, adapter=adapter)

    row = store.get_cognee_sync(source["id"])[0]
    assert result["processed"] == 1
    assert result["skipped"] == 1
    assert result["succeeded"] == 0
    assert result["results"][0]["status"] == "skipped"
    assert "Source is deleted" in result["results"][0]["skip_reason"]
    assert row["status"] == "deleted"
    assert "Source is deleted" in row["error_message"]
    assert adapter.calls == []


def test_source_creation_creates_pending_source_record_sync_row(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = ingest_source(
        IngestSourceRequest(
            source="# Source\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            title="Knowledge graph note",
        ),
        settings,
    )

    sync_rows = BrainStore(settings).get_cognee_sync(receipt.memory_cards[0].id)
    assert {
        (row["object_type"], row["dataset"], row["status"])
        for row in sync_rows
    } == {("memory", "memory", "pending")}


def test_memory_update_marks_projection_stale(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    store = BrainStore(settings)

    store.update_memory_status(receipt.memory_cards[0].id, "superseded")

    row = store.get_cognee_sync(receipt.memory_cards[0].id)[0]
    assert row["status"] == "stale"


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}", **overrides)
