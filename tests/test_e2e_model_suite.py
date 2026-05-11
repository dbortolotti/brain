from __future__ import annotations

import re
from typing import Any

from fastapi.testclient import TestClient

from memory_stack.brain_store import BrainStore
from memory_stack.evals.e2e_model_suite import (
    E2E_MODEL_OUTPUT_SCHEMA,
    E2E_RECALL_CASES,
    seed_e2e_database,
    settings_for_e2e_database,
    run_e2e_model_suite,
)
from memory_stack.evals.model_matrix import ModelCandidate
from memory_stack.evals.provider_client import ModelCallResult
from memory_stack.mcp_server import app
from memory_stack import mcp_server


PASSING_MODEL_RESPONSES = {
    "e2e_recall_daughters": {
        "answer": "Nur and Sara are Daniele's daughters.",
        "citations": ["mem_606293e20cef058e"],
        "memory_ids": ["mem_606293e20cef058e"],
    },
    "e2e_recall_current_work": {
        "answer": "Sam left Goldman and joined Point72, so the current workplace evidence is Point72.",
        "citations": ["sam_work_current"],
        "memory_ids": ["sam_work_current"],
    },
    "e2e_recall_music_deleted_filter": {
        "answer": "Sam likes Bill Evans.",
        "citations": ["sam_jazz"],
        "memory_ids": ["sam_jazz"],
    },
    "e2e_recall_open_loop_filter": {
        "answer": "Open loop: Daniele wants to learn more about knowledge graphs.",
        "citations": ["knowledge_graphs_open_loop"],
        "memory_ids": ["knowledge_graphs_open_loop"],
    },
    "e2e_recall_brain_cognee_conclusions": {
        "answer": "The conclusion was that Brain DB remains the source of truth, while Cognee is a rebuildable projection for semantic search.",
        "citations": ["brain_cognee"],
        "memory_ids": ["brain_cognee"],
    },
    "e2e_recall_ai_memory_articles": {
        "answer": "The saved AI memory article says AI memory systems need durable source evidence.",
        "citations": ["ai_memory_article"],
        "memory_ids": ["ai_memory_article"],
    },
}


class FixtureAwareFakeModelClient:
    def __init__(self, overrides: dict[str, dict[str, Any]] | None = None) -> None:
        self.overrides = overrides or {}
        self.prompts: list[str] = []

    def complete_json(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> ModelCallResult:
        assert candidate.kind == "llm"
        assert schema == E2E_MODEL_OUTPUT_SCHEMA
        self.prompts.append(prompt)
        fixture_id = fixture_id_from_prompt(prompt)
        payload = self.overrides.get(fixture_id, PASSING_MODEL_RESPONSES[fixture_id])
        return ModelCallResult(
            status="ok",
            payload=payload,
            raw_text=str(payload),
            error=None,
            latency_ms=1,
            input_tokens=10,
            output_tokens=10,
            estimated_cost_usd=0.0,
        )


def test_e2e_model_suite_seeds_sqlite_database_and_scores_full_runtime_prompts(
    tmp_path,
) -> None:
    database_path = tmp_path / "brain-e2e.db"
    settings = settings_for_e2e_database(database_path)
    client = FixtureAwareFakeModelClient()

    result = run_e2e_model_suite(settings, client=client)

    store = BrainStore(settings)
    assert database_path.exists()
    assert result["record_count"] == len(E2E_RECALL_CASES)
    assert result["pass_count"] == len(E2E_RECALL_CASES)
    assert result["fail_count"] == 0
    assert len(store.list_memory_cards(include_deleted=True, limit=100)) >= 9
    assert len(store.list_sources(limit=100)) == 3
    assert any(
        memory["status"] == "deleted" and "Taylor Swift" in memory["statement"]
        for memory in store.list_memory_cards(include_deleted=True, limit=100)
    )
    assert all("runtime_facts" in prompt for prompt in client.prompts)
    assert all(record["scores"]["recall_quality"] == 1.0 for record in result["records"])


def test_e2e_model_suite_flags_deleted_or_irrelevant_model_answers(tmp_path) -> None:
    settings = settings_for_e2e_database(tmp_path / "brain-e2e.db")
    client = FixtureAwareFakeModelClient(
        {
            "e2e_recall_music_deleted_filter": {
                "answer": "Sam likes Bill Evans and Taylor Swift.",
                "citations": ["sam_jazz", "sam_music_deleted"],
                "memory_ids": ["sam_jazz", "sam_music_deleted"],
            }
        }
    )

    result = run_e2e_model_suite(settings, client=client)
    bad_record = next(
        record
        for record in result["records"]
        if record["fixture_id"] == "e2e_recall_music_deleted_filter"
    )

    assert result["fail_count"] == 1
    assert bad_record["status"] == "fail"
    assert bad_record["scores"]["recall_quality"] == 0.0
    assert bad_record["zero_tolerance"] is True
    assert "deleted_memory_returned" in bad_record["notes"]


def test_seeded_e2e_database_is_available_to_app_http_endpoints(tmp_path) -> None:
    settings = settings_for_e2e_database(tmp_path / "brain-e2e.db")
    seed_e2e_database(settings)
    previous_settings = mcp_server.settings
    mcp_server.settings = settings
    try:
        client = TestClient(app)
        response = client.post(
            "/memory/recall",
            json={"query": "Who are my daughters?", "mode": "auto"},
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()
    assert "Nur and Sara" in payload["answer"]
    assert payload["facts"][0]["status"] == "current"


def fixture_id_from_prompt(prompt: str) -> str:
    match = re.search(r'"fixture_id": "([^"]+)"', prompt)
    assert match is not None
    return match.group(1)
