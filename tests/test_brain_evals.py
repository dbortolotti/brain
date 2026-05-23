from __future__ import annotations

from typing import Any

from memory_stack import brain_service
from memory_stack.cfg import Settings
from memory_stack.evals.fixtures import GOLDEN_INGESTION_FIXTURES
from memory_stack.evals.golden_queries import GOLDEN_RECALL_QUERIES
from memory_stack.evals.metrics import duplicate_rate, precision_at_k, term_recall
from memory_stack.evals.runner import run_golden_evals


class FakeCogneeSearch:
    def search(
        self,
        query: str,
        *,
        dataset: str,
        top_k: int,
        settings: Settings,
    ) -> list[dict[str, str]]:
        del query, dataset, top_k, settings
        return []


class FakeLLMClient:
    def complete_json(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("Golden eval tests should not require live LLM calls.")


def test_golden_fixtures_and_queries_are_present() -> None:
    assert len(GOLDEN_INGESTION_FIXTURES) >= 8
    assert len(GOLDEN_RECALL_QUERIES) >= 6


def test_metric_helpers_are_deterministic() -> None:
    assert precision_at_k(["a", "b"], {"b"}, k=2) == 1.0
    assert term_recall("Sam likes Bill Evans.", {"Sam", "Point72"}) == 0.5
    assert duplicate_rate(
        [
            {"statement": "Sam likes Bill Evans."},
            {"statement": "Sam likes Bill Evans."},
        ]
    ) == 0.5


def test_golden_evals_run_offline_with_fake_llm_and_fake_cognee(tmp_path, monkeypatch) -> None:
    settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_cognee_recall_enabled=True,
        brain_llm_enabled=False,
        brain_taste_enabled=False,
    )
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    result = run_golden_evals(
        settings,
        llm_client=FakeLLMClient(),
        cognee_searcher=FakeCogneeSearch(),
    )

    assert len(result["ingestion_results"]) == len(GOLDEN_INGESTION_FIXTURES)
    assert len(result["recall_results"]) == len(GOLDEN_RECALL_QUERIES)
    assert {
        "memory_card_extraction_precision",
        "entity_resolution_accuracy",
        "duplicate_rate",
        "conflict_detection_precision",
        "recall_precision_at_k",
        "groundedness",
        "unsupported_claim_count",
        "latency",
        "llm_cost_per_ingestion",
        "cognee_sync_failure_rate",
    } <= set(result["metrics"])
    assert calls


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
