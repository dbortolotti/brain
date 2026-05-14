from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from memory_stack import mcp_server
from memory_stack.agents.role_specs import role_spec_role_names
from memory_stack.brain_store import BrainStore
from memory_stack.evals.e2e_model_suite import (
    E2E_RECALL_CASES,
    EXPECTED_E2E_ROLES,
    build_e2e_model_fixtures,
    run_e2e_model_suite,
    seed_e2e_database,
    settings_for_e2e_database,
)
from memory_stack.mcp_server import app


def test_e2e_database_seed_populates_real_sqlite_runtime_state(tmp_path) -> None:
    database_path = tmp_path / "brain-e2e.db"
    settings = settings_for_e2e_database(database_path)

    seed = seed_e2e_database(settings)

    store = BrainStore(settings)
    memories = store.list_memory_cards(include_deleted=True, limit=100)
    sources = store.list_sources(limit=100)
    assert database_path.exists()
    assert len(memories) >= 9
    assert len(sources) == 3
    assert seed.memory_ids["sam_work_old"] in {
        memory["id"] for memory in memories if memory["status"] == "superseded"
    }
    assert seed.memory_ids["sam_music_deleted"] in {
        memory["id"] for memory in memories if memory["status"] == "deleted"
    }
    assert store.list_open_loops(topic="knowledge graphs")[
        0
    ]["id"] == seed.open_loop_ids["knowledge_graphs"]


def test_e2e_model_fixture_matrix_covers_runtime_role_specs(tmp_path) -> None:
    settings = settings_for_e2e_database(tmp_path / "brain-e2e.db")
    seed = seed_e2e_database(settings)

    fixtures = build_e2e_model_fixtures(settings, seed)
    roles = {fixture.role for fixture in fixtures}

    assert roles == set(EXPECTED_E2E_ROLES)
    assert roles == role_spec_role_names()
    assert len(fixtures) == len(EXPECTED_E2E_ROLES) + len(E2E_RECALL_CASES)
    assert sum(1 for fixture in fixtures if fixture.scenario_group == "e2e_runtime_recall") == len(
        E2E_RECALL_CASES
    )


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
