from __future__ import annotations

from typing import Any

from sqlalchemy import func, inspect, select

from memory_stack import brain_schema as schema
from memory_stack import brain_service
from memory_stack.brain_models import IngestSourceRequest, RememberRequest
from memory_stack.brain_service import (
    ingest_source,
    remember,
)
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.cognee_adapter import run_async


def test_remember_commits_directly_to_cognee_without_projection_rows(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)

    assert receipt.cognee_sync_status == "synced"
    assert calls[0]["dataset_name"] == settings.brain_cognee_memory_dataset
    assert "brain" in calls[0]["node_set"]
    assert "brain_memory" not in calls[0]["node_set"]
    assert calls[0]["text"] == "Sam likes Bill Evans."
    assert_legacy_semantic_counts(settings)


def test_ingest_source_commits_source_and_memory_directly_to_cognee(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Source\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            title="Knowledge graph note",
        ),
        settings,
    )

    assert receipt.cognee_sync_status == "synced"
    assert [call["dataset_name"] for call in calls] == [settings.brain_cognee_memory_dataset]
    assert calls[0]["text"] == "# Source\nKnowledge graphs matter for Brain."
    assert "brain_source" not in calls[0]["node_set"]
    assert "brain_memory" not in calls[0]["node_set"]
    assert BrainStore(settings).list_external_receipts()[0]["cognee_dataset"] == "memory"
    assert_legacy_semantic_counts(settings)


def test_run_async_reuses_background_loop() -> None:
    loop_ids: list[int] = []

    async def capture_loop_id() -> int:
        import asyncio

        loop_id = id(asyncio.get_running_loop())
        loop_ids.append(loop_id)
        return loop_id

    first = run_async(capture_loop_id())
    second = run_async(capture_loop_id())

    assert first == second
    assert loop_ids == [first, first]


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

def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_llm_enabled=False,
        brain_taste_enabled=False,
        **overrides,
    )
