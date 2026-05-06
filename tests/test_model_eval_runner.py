from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from memory_stack.config import Settings
from memory_stack.evals.model_fixtures import ModelEvalFixture
from memory_stack.evals.model_matrix import load_model_registry, select_model_candidates
from memory_stack.evals.model_runner import ModelEvalRunConfig, run_model_evals
from memory_stack.evals.provider_client import ModelCallResult, openai_reasoning_effort
from memory_stack.evals.scoring import (
    aggregate_model_role_records,
    paired_model_comparisons,
    score_model_output,
    zero_tolerance_upper_bound,
)


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "brain_model_registry.yaml"


class FakeEvalClient:
    def complete_json(self, *args: Any, **kwargs: Any) -> ModelCallResult:
        return ModelCallResult(
            status="ok",
            payload={
                "intent": "remember",
                "decision": "commit_success",
                "memory_cards": [
                    {
                        "kind": "family_fact",
                        "statement": "Nur and Sara are Daniele's twin daughters.",
                        "relationships": [
                            {"subject": "Nur", "predicate": "daughter_of", "object": "Daniele"},
                            {"subject": "Nur", "predicate": "twin_of", "object": "Sara"},
                        ],
                    }
                ],
                "receipt": {
                    "success": True,
                    "details": ["family_fact", "Nur", "Sara", "confidence high"],
                },
                "answer": "Nur and Sara are Daniele's twin daughters.",
            },
            raw_text="{}",
            error=None,
            latency_ms=12,
            input_tokens=100,
            output_tokens=20,
            estimated_cost_usd=0.0001,
        )

    def embed(self, *args: Any, **kwargs: Any) -> ModelCallResult:
        return ModelCallResult(
            status="ok",
            payload={"embedding_vector_size": 1536},
            raw_text='{"embedding_vector_size":1536}',
            error=None,
            latency_ms=7,
            input_tokens=5,
            output_tokens=0,
            estimated_cost_usd=0.00001,
        )


def test_model_matrix_selects_explicit_alias_and_embeddings() -> None:
    registry = load_model_registry(REGISTRY_PATH)

    candidates = select_model_candidates(
        registry,
        model_refs=["anthropic:claude-haiku-4-5", "openai:text-embedding-3-small"],
        roles={"embeddings"},
        scope="core",
        include_judge=False,
    )

    assert [(candidate.provider, candidate.model, candidate.kind) for candidate in candidates] == [
        ("anthropic", "claude-haiku-4-5-20251001", "llm"),
        ("openai", "text-embedding-3-small", "embedding"),
    ]


def test_model_test_initial_model_set_runs_through_config(tmp_path) -> None:
    output = tmp_path / "eval.jsonl"
    config = ModelEvalRunConfig(
        registry_path=REGISTRY_PATH,
        fixture_set="smoke",
        roles={"embeddings"},
        model_refs=None,
        model_set="model-test-initial",
        scope="core",
        include_judge=False,
        repeat_runs=1,
        bootstrap_samples=0,
        output_path=output,
    )

    result = run_model_evals(Settings(), config, client=FakeEvalClient())

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert result["record_count"] == 4
    assert {row["model"] for row in rows} == {
        "openai:text-embedding-3-small",
        "openai:text-embedding-3-large",
        "voyage:voyage-4-lite",
        "voyage:voyage-4",
    }


def test_fixture_scoring_detects_zero_tolerance_overmerge() -> None:
    fixture = ModelEvalFixture(
        id="ambiguous",
        scenario_group="ambiguous_sam",
        role="entity_resolution",
        input_text="Existing: Sam A and Sam B. New: Sam likes jazz.",
        expected={"entity_action": "needs_clarification"},
        zero_tolerance_checks=("entity_overmerge",),
    )

    scores, zero_tolerance, notes = score_model_output(
        fixture,
        {"entity_resolution": {"action": "use_existing", "entity_id": "sam_a"}},
        status="ok",
    )

    assert scores["entity_safety"] == 0.0
    assert zero_tolerance is True
    assert notes == ["zero_tolerance_failed"]


def test_provider_failure_is_not_counted_as_zero_tolerance() -> None:
    fixture = ModelEvalFixture(
        id="provider_down",
        scenario_group="provider",
        role="router",
        input_text="remember Sam likes jazz",
        expected={"intent": "remember"},
        zero_tolerance_checks=("malformed_json_unrepairable",),
    )

    _scores, zero_tolerance, notes = score_model_output(fixture, None, status="fail")

    assert zero_tolerance is False
    assert notes == ["provider_failure"]


def test_statistical_aggregation_outputs_ci_and_zero_bound() -> None:
    records = [
        {
            "model": "openai:gpt-5.4-nano",
            "role": "slack_intake",
            "scenario_group": "a",
            "status": "ok",
            "zero_tolerance_failure": False,
            "scores": {"schema_validity": 1.0, "decision_correctness": 1.0},
            "estimated_cost_usd": 0.1,
            "latency_ms": 100,
        },
        {
            "model": "openai:gpt-5.4-nano",
            "role": "slack_intake",
            "scenario_group": "b",
            "status": "ok",
            "zero_tolerance_failure": False,
            "scores": {"schema_validity": 1.0, "decision_correctness": 0.0},
            "estimated_cost_usd": 0.2,
            "latency_ms": 200,
        },
    ]

    summary = aggregate_model_role_records(records, bootstrap_samples=100)[0]

    assert summary["overall_score"]["method"] == "hierarchical_bootstrap_by_scenario_group"
    assert summary["n_scenario_groups"] == 2
    assert zero_tolerance_upper_bound(0, 10) == 0.3


def test_pairwise_comparison_uses_shared_fixtures() -> None:
    base = {
        "role": "router",
        "scenario_group": "router",
        "fixture_id": "router_1",
        "repeat_idx": 0,
        "status": "ok",
        "zero_tolerance_failure": False,
        "estimated_cost_usd": 0.1,
        "latency_ms": 10,
    }
    records = [
        {**base, "model": "a", "scores": {"schema_validity": 1.0}},
        {**base, "model": "b", "scores": {"schema_validity": 0.0}, "estimated_cost_usd": 0.2},
    ]

    comparison = paired_model_comparisons(records, bootstrap_samples=10)[0]

    assert comparison["model_a"] == "a"
    assert comparison["model_b"] == "b"
    assert comparison["n_paired_fixtures"] == 1
    assert comparison["score_diff_a_minus_b"]["mean"] > 0


def test_openai_reasoning_effort_matches_model_family() -> None:
    assert openai_reasoning_effort("gpt-5-nano") == "minimal"
    assert openai_reasoning_effort("gpt-5.4-nano") == "low"
    assert openai_reasoning_effort("gpt-5.4-mini") == "low"
    assert openai_reasoning_effort("gpt-5.5") == "low"


def test_model_eval_runner_writes_jsonl_and_markdown(tmp_path) -> None:
    output = tmp_path / "eval.jsonl"
    report = tmp_path / "report.md"
    config = ModelEvalRunConfig(
        registry_path=REGISTRY_PATH,
        fixture_set="smoke",
        roles={"slack_intake"},
        model_refs=["openai:gpt-5.4-nano"],
        scope="core",
        include_judge=False,
        repeat_runs=1,
        bootstrap_samples=10,
        output_path=output,
        report_md_path=report,
        max_workers=2,
    )

    result = run_model_evals(Settings(), config, client=FakeEvalClient())

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert result["record_count"] >= 3
    assert "slack_intake_family_twins" in {row["fixture_id"] for row in rows}
    assert rows[0]["status"] == "ok"
    assert report.read_text().startswith("# Brain Model Eval Report")
