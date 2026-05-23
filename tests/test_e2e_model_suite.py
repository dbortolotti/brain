from __future__ import annotations

import os
from typing import Any

import pytest

from memory_stack.agents.role_specs import role_spec_role_names
from memory_stack.brain_models import RecallResponse
from memory_stack.evals.e2e_model_suite import (
    E2E_RECALL_CASES,
    EXPECTED_E2E_ROLES,
    E2EDatabaseSeed,
    build_e2e_model_fixtures,
    build_role_e2e_fixtures,
    run_e2e_model_suite,
    settings_for_e2e_database,
)


def test_e2e_role_fixture_matrix_covers_runtime_role_specs_without_db_seed() -> None:
    fixtures = build_role_e2e_fixtures(synthetic_seed())
    roles = {fixture.role for fixture in fixtures}

    assert roles == set(EXPECTED_E2E_ROLES)
    assert roles == role_spec_role_names()
    assert len(fixtures) == len(EXPECTED_E2E_ROLES)


def test_e2e_model_fixture_matrix_uses_cognee_recall_payloads(
    tmp_path,
    monkeypatch,
) -> None:
    from memory_stack.evals import e2e_model_suite

    calls: list[dict[str, Any]] = []

    def fake_recall(request, settings):
        calls.append({"request": request, "settings": settings})
        return RecallResponse(
            answer=f"Cognee answer for {request.query}",
            facts=[
                {
                    "memory_id": "mem_current",
                    "statement": "Cognee owns durable semantic memory.",
                    "status": "current",
                }
            ],
            evidence=[{"source_id": "src_brain_cognee", "title": "Brain/Cognee design chat"}],
            open_loops=[
                {"id": "loop_knowledge_graphs", "statement": "Review Cognee graph APIs."}
            ]
            if request.mode == "open_loops"
            else [],
        )

    monkeypatch.setattr(e2e_model_suite, "recall", fake_recall)
    settings = settings_for_e2e_database(tmp_path / "brain-e2e.db")
    fixtures = build_e2e_model_fixtures(settings, synthetic_seed())

    roles = {fixture.role for fixture in fixtures}
    recall_fixtures = [
        fixture for fixture in fixtures if fixture.scenario_group == "e2e_runtime_recall"
    ]
    assert roles == set(EXPECTED_E2E_ROLES)
    assert len(fixtures) == len(EXPECTED_E2E_ROLES) + len(E2E_RECALL_CASES)
    assert len(recall_fixtures) == len(E2E_RECALL_CASES)
    assert len(calls) == len(E2E_RECALL_CASES)
    assert all("Cognee owns durable semantic memory." in fixture.input_text for fixture in recall_fixtures)


@pytest.mark.skipif(
    os.getenv("BRAIN_RUN_LIVE_E2E_MODEL_TESTS") != "1",
    reason="Set BRAIN_RUN_LIVE_E2E_MODEL_TESTS=1 to run live model E2E tests.",
)
def test_live_e2e_model_suite_runs_configured_model_front_to_back(tmp_path) -> None:
    settings = settings_for_e2e_database(tmp_path / "brain-live-e2e.db")

    result = run_e2e_model_suite(settings)

    assert result["model"] == "openai:gpt-5.4-mini"
    assert result["record_count"] == len(EXPECTED_E2E_ROLES) + len(E2E_RECALL_CASES)
    assert {record["role"] for record in result["records"]} == set(EXPECTED_E2E_ROLES)
    assert result["fail_count"] == 0


def synthetic_seed() -> E2EDatabaseSeed:
    return E2EDatabaseSeed(
        memory_ids={
            "daughters": "mem_daughters",
            "sam_jazz": "mem_sam_jazz",
            "knowledge_graphs_open_loop": "mem_knowledge_graphs_open_loop",
            "python_closed_loop": "mem_python_closed_loop",
            "sam_work_old": "mem_sam_work_old",
            "sam_work_current": "mem_sam_work_current",
            "sam_music_deleted": "mem_sam_music_deleted",
            "brain_cognee": "mem_brain_cognee",
            "ai_memory_article": "mem_ai_memory_article",
            "preference_table": "mem_preference_table",
        },
        source_ids={
            "brain_cognee": "src_brain_cognee",
            "ai_memory_article": "src_ai_memory_article",
            "preference_table": "src_preference_table",
        },
        open_loop_ids={
            "knowledge_graphs": "loop_knowledge_graphs",
            "python": "loop_python",
        },
    )
