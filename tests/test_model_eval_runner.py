from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from memory_stack.config import Settings
from memory_stack.evals.model_fixtures import ModelEvalFixture, select_fixtures
from memory_stack.evals.model_matrix import load_model_registry, select_model_candidates
from memory_stack.evals.model_runner import (
    ModelEvalRunConfig,
    build_work_items,
    read_eval_records,
    render_report,
    run_model_evals,
    run_rerun_failed,
    write_parsed_output,
    write_raw_output,
)
from memory_stack.evals.provider_client import LiveProviderClient, ModelCallResult, ProviderCallError, openai_reasoning_effort
from memory_stack.evals.scoring import (
    EvalRecord,
    FailureClass,
    Summary,
    aggregate,
    aggregate_model_role_records,
    is_stack_deployable,
    pairwise_quality,
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


class ConcurrencyTrackingClient(FakeEvalClient):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_by_endpoint: dict[str, int] = {}
        self.max_active_by_endpoint: dict[str, int] = {}

    def complete_json(self, candidate: Any, *args: Any, **kwargs: Any) -> ModelCallResult:
        endpoint = candidate.endpoint_key
        with self._lock:
            active = self._active_by_endpoint.get(endpoint, 0) + 1
            self._active_by_endpoint[endpoint] = active
            self.max_active_by_endpoint[endpoint] = max(self.max_active_by_endpoint.get(endpoint, 0), active)
        try:
            time.sleep(0.01)
            return super().complete_json(candidate, *args, **kwargs)
        finally:
            with self._lock:
                self._active_by_endpoint[endpoint] -= 1


class AlwaysFailClient(FakeEvalClient):
    def complete_json(self, *args: Any, **kwargs: Any) -> ModelCallResult:
        return ModelCallResult(
            status="fail",
            payload=None,
            raw_text="",
            error="HTTP 503: provider unavailable",
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
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


def test_model_matrix_selects_gpt_5_5_xhigh_inventory_variant() -> None:
    registry = load_model_registry(REGISTRY_PATH)

    candidate = select_model_candidates(
        registry,
        model_refs=["openai:gpt-5.5-xhigh"],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )[0]

    assert candidate.ref == "openai:gpt-5.5-xhigh"
    assert candidate.model == "gpt-5.5-xhigh"
    assert candidate.api_model == "gpt-5.5"
    assert candidate.reasoning_effort == "xhigh"


def test_model_matrix_selects_gpt_5_4_and_gemini_3_1_pro_thinking_variants() -> None:
    registry = load_model_registry(REGISTRY_PATH)

    candidates = select_model_candidates(
        registry,
        model_refs=["openai:gpt-5.4-high", "google:gemini-3.1-pro-preview-medium"],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )

    assert candidates[0].api_model == "gpt-5.4"
    assert candidates[0].reasoning_effort == "high"
    assert candidates[1].api_model == "gemini-3.1-pro-preview"
    assert candidates[1].reasoning_effort == "medium"


def test_model_matrix_selects_openrouter_quantized_variants() -> None:
    registry = load_model_registry(REGISTRY_PATH)

    candidates = select_model_candidates(
        registry,
        model_refs=[
            "openrouter:qwen/qwen3.5-9b-fp8",
            "openrouter:google/gemma-3n-e4b-it",
            "openrouter:google/gemma-4-31b-it-fp8",
            "openrouter:qwen/qwen3.5-27b-fp8",
        ],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )

    assert [(candidate.api_model, candidate.quantizations) for candidate in candidates] == [
        ("qwen/qwen3.5-9b", ("fp8",)),
        ("google/gemma-3n-e4b-it", ()),
        ("google/gemma-4-31b-it", ("fp8",)),
        ("qwen/qwen3.5-27b", ("fp8",)),
    ]


def test_fine_grained_model_matrix_selects_targeted_role_models() -> None:
    registry = load_model_registry(REGISTRY_PATH)

    candidates = select_model_candidates(
        registry,
        model_refs=None,
        roles={"intent_router"},
        scope="core",
        include_judge=False,
        mode="fine-grained",
    )

    assert [candidate.ref for candidate in candidates] == [
        "openai:gpt-5-nano",
        "google:gemini-2.5-flash-lite",
        "openrouter:qwen/qwen3.5-9b-fp8",
        "openrouter:google/gemma-3n-e4b-it",
        "openrouter:google/gemma-4-31b-it-fp8",
        "openrouter:qwen/qwen3.5-27b-fp8",
    ]


def test_select_fixtures_derives_fine_grained_roles() -> None:
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"intent_router"},
        mode="fine-grained",
    )

    assert fixtures
    assert all(fixture.role == "intent_router" for fixture in fixtures)


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
    assert notes == ["entity_overmerge"]


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


def test_provider_error_is_not_semantic_zero() -> None:
    summary = aggregate(
        [
            EvalRecord(
                model="a",
                role="router",
                operational_success=False,
                failure_class=FailureClass.PROVIDER_ERROR,
                schema_valid=False,
                semantic_evaluable=False,
                quality_score=None,
            )
        ],
        bootstrap_samples=0,
    )

    assert summary.operational_success_rate == 0
    assert summary.semantic_score_mean is None


def test_schema_failure_is_distinct_from_provider_failure() -> None:
    summary = aggregate(
        [
            EvalRecord(
                model="a",
                role="router",
                operational_success=True,
                failure_class=FailureClass.SCHEMA_INVALID,
                schema_valid=False,
                json_parseable=True,
                semantic_evaluable=False,
            )
        ],
        bootstrap_samples=0,
    )

    assert summary.operational_success_rate == 1
    assert summary.schema_validity_rate == 0
    assert summary.semantic_score_mean is None


def test_statistical_aggregation_outputs_ci_and_zero_bound() -> None:
    records = [
        EvalRecord(
            model="openai:gpt-5.4-nano",
            provider="openai",
            role="slack_intake",
            scenario_group="a",
            fixture_id="f1",
            variant_id="base",
            operational_success=True,
            schema_valid=True,
            json_parseable=True,
            semantic_evaluable=True,
            subscores={"decision_correctness": 1.0, "repair_quality": 1.0},
            quality_score=1.0,
            estimated_cost_usd=0.1,
            latency_ms=100,
        ),
        EvalRecord(
            model="openai:gpt-5.4-nano",
            provider="openai",
            role="slack_intake",
            scenario_group="b",
            fixture_id="f2",
            variant_id="base",
            operational_success=True,
            schema_valid=True,
            json_parseable=True,
            semantic_evaluable=True,
            subscores={"decision_correctness": 0.0, "repair_quality": 1.0},
            quality_score=0.5,
            estimated_cost_usd=0.2,
            latency_ms=200,
        ),
    ]

    summary = aggregate_model_role_records(records, bootstrap_samples=100)[0]

    assert summary["records_total"] == 2
    assert summary["records_semantic_evaluable"] == 2
    assert summary["subscores"]["decision_correctness"]["method"] == "hierarchical_bootstrap_by_scenario_fixture_variant"
    assert zero_tolerance_upper_bound(0, 10) == 0.3


def test_embeddings_do_not_satisfy_runtime_roles() -> None:
    eligible = [
        Summary(role="embeddings", eligible=True),
    ]

    deployable, missing = is_stack_deployable(eligible)

    assert deployable is False
    assert "slack_intake" in missing


def test_missing_mandatory_role_marks_stack_non_deployable() -> None:
    eligible = [
        Summary(role="router", eligible=True),
        Summary(role="memory_compiler", eligible=True),
        Summary(role="conflict_classifier", eligible=True),
        Summary(role="recall_synthesizer", eligible=True),
        Summary(role="embeddings", eligible=True),
    ]

    deployable, missing = is_stack_deployable(eligible)

    assert deployable is False
    assert missing == ["slack_intake"]


def test_pairwise_comparison_uses_shared_fixtures() -> None:
    comparison = pairwise_quality(
        [
            EvalRecord(
                model="a",
                role="router",
                fixture_id="router_1",
                variant_id="base",
                scenario_group="router",
                operational_success=True,
                schema_valid=True,
                json_parseable=True,
                semantic_evaluable=True,
                quality_score=1.0,
                subscores={"decision_correctness": 1.0},
                estimated_cost_usd=0.1,
                latency_ms=10,
            )
        ],
        [
            EvalRecord(
                model="b",
                role="router",
                fixture_id="router_1",
                variant_id="base",
                scenario_group="router",
                operational_success=True,
                schema_valid=True,
                json_parseable=True,
                semantic_evaluable=True,
                quality_score=0.0,
                subscores={"decision_correctness": 0.0},
                estimated_cost_usd=0.2,
                latency_ms=10,
            )
        ],
        bootstrap_samples=10,
    )

    assert comparison.model_a == "a"
    assert comparison.model_b == "b"
    assert comparison.shared_variants_total == 1
    assert comparison.semantic_score_diff_mean is not None
    assert comparison.semantic_score_diff_mean > 0


def test_pairwise_semantic_excludes_provider_errors() -> None:
    comparison = pairwise_quality(
        [
            EvalRecord(
                model="a",
                role="router",
                fixture_id="f1",
                operational_success=False,
                failure_class=FailureClass.PROVIDER_ERROR,
                semantic_evaluable=False,
            )
        ],
        [
            EvalRecord(
                model="b",
                role="router",
                fixture_id="f1",
                operational_success=True,
                schema_valid=True,
                json_parseable=True,
                semantic_evaluable=True,
                quality_score=0.9,
                subscores={"decision_correctness": 0.9},
            )
        ],
        bootstrap_samples=10,
    )

    assert comparison.shared_variants_semantic_evaluable == 0
    assert comparison.recommendation == "insufficient_semantic_overlap"


def test_non_deployable_report_suppresses_production_defaults() -> None:
    report = render_report(
        deployable_stack=False,
        missing_roles=["slack_intake"],
        partial_recommendations={"router": "model_x"},
    )

    assert "Deployable stack: **NO**" in report
    assert "Partial recommendations" in report
    assert "Production defaults" not in report


def test_openai_reasoning_effort_matches_model_family() -> None:
    assert openai_reasoning_effort("gpt-5-nano") == "minimal"
    assert openai_reasoning_effort("gpt-5.4-nano") == "low"
    assert openai_reasoning_effort("gpt-5.4-mini") == "low"
    assert openai_reasoning_effort("gpt-5.5") == "low"


def test_live_provider_client_uses_reasoning_effort_override() -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.last_json: dict[str, Any] | None = None

        def post(self, _url: str, *, headers: dict[str, str], json: dict[str, Any]) -> Any:
            self.last_json = json

            class Response:
                status_code = 200

                @staticmethod
                def json() -> dict[str, Any]:
                    return {"output_text": "{}"}

            return Response()

    http_client = RecordingClient()
    client = LiveProviderClient(Settings(openai_api_key="test-key"), http_client=http_client)
    candidate = select_model_candidates(
        load_model_registry(REGISTRY_PATH),
        model_refs=["openai:gpt-5.5-xhigh"],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )[0]

    client.complete_json(candidate, prompt="test", schema={})

    assert http_client.last_json is not None
    assert http_client.last_json["model"] == "gpt-5.5"
    assert http_client.last_json["reasoning"] == {"effort": "xhigh"}


def test_live_provider_client_maps_google_reasoning_effort_to_thinking_level() -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.last_json: dict[str, Any] | None = None

        def post(self, _url: str, *, headers: dict[str, str], json: dict[str, Any]) -> Any:
            self.last_json = json

            class Response:
                status_code = 200

                @staticmethod
                def json() -> dict[str, Any]:
                    return {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [{"text": "{}"}],
                                }
                            }
                        ]
                    }

            return Response()

    http_client = RecordingClient()
    client = LiveProviderClient(Settings(gemini_api_key="test-key"), http_client=http_client)
    candidate = select_model_candidates(
        load_model_registry(REGISTRY_PATH),
        model_refs=["google:gemini-3.1-pro-preview-medium"],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )[0]

    client.complete_json(candidate, prompt="test", schema={})

    assert http_client.last_json is not None
    assert http_client.last_json["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "medium"}


def test_live_provider_client_uses_openrouter_quantization_override() -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.last_json: dict[str, Any] | None = None
            self.last_url: str | None = None

        def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> Any:
            self.last_url = url
            self.last_json = json

            class Response:
                status_code = 200

                @staticmethod
                def json() -> dict[str, Any]:
                    return {"choices": [{"message": {"content": "{}"}}]}

            return Response()

    http_client = RecordingClient()
    client = LiveProviderClient(Settings(openrouter_api_key="test-key"), http_client=http_client)
    candidate = select_model_candidates(
        load_model_registry(REGISTRY_PATH),
        model_refs=["openrouter:google/gemma-4-31b-it-fp8"],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )[0]

    client.complete_json(candidate, prompt="test", schema={})

    assert http_client.last_url == "https://openrouter.ai/api/v1/chat/completions"
    assert http_client.last_json is not None
    assert http_client.last_json["model"] == "google/gemma-4-31b-it"
    assert http_client.last_json["provider"] == {"quantizations": ["fp8"]}


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
    )

    result = run_model_evals(Settings(), config, client=FakeEvalClient())

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert result["record_count"] >= 3
    assert "slack_intake_family_twins" in {row["fixture_id"] for row in rows}
    assert rows[0]["status"] == "ok"
    assert report.read_text().startswith("# Executive verdict")


def test_model_eval_runner_caps_concurrency_per_shared_endpoint(tmp_path) -> None:
    output = tmp_path / "eval.jsonl"
    config = ModelEvalRunConfig(
        registry_path=REGISTRY_PATH,
        fixture_set="brain-model-test-v2",
        roles={"eval_judge"},
        model_refs=["openai:gpt-5.5", "openai:gpt-5.5-high"],
        scope="core",
        include_judge=True,
        repeat_runs=2,
        bootstrap_samples=0,
        output_path=output,
        endpoint_max_concurrency=3,
    )

    client = ConcurrencyTrackingClient()
    run_model_evals(Settings(), config, client=client)

    assert client.max_active_by_endpoint["openai:gpt-5.5:llm"] <= 3
    assert client.max_active_by_endpoint["openai:gpt-5.5:llm"] > 1


def test_build_work_items_makes_repeat_the_outer_loop() -> None:
    registry = load_model_registry(REGISTRY_PATH)
    candidates = select_model_candidates(
        registry,
        model_refs=["openai:gpt-5.4-nano"],
        roles={"slack_intake"},
        scope="core",
        include_judge=False,
    )
    fixtures = select_fixtures(
        fixture_set="smoke",
        roles={"slack_intake"},
        mode="broad",
    )

    items = build_work_items(candidates, {"slack_intake"}, fixtures, 2)

    assert items
    first_repeat_count = sum(1 for item in items if item.repeat_idx == 0)
    assert first_repeat_count * 2 == len(items)
    assert all(item.repeat_idx == 0 for item in items[:first_repeat_count])
    assert all(item.repeat_idx == 1 for item in items[first_repeat_count:])


def test_build_work_items_interleaves_endpoints_within_repeat() -> None:
    registry = load_model_registry(REGISTRY_PATH)
    candidates = select_model_candidates(
        registry,
        model_refs=None,
        roles={"intent_router"},
        scope="core",
        include_judge=False,
        mode="fine-grained",
    )
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"intent_router"},
        mode="fine-grained",
    )

    items = build_work_items(candidates, {"intent_router"}, fixtures, 1)

    assert len(items) >= 6
    first_wave = items[:6]
    assert {item.candidate.endpoint_key for item in first_wave} == {
        "openai:gpt-5-nano:llm",
        "google:gemini-2.5-flash-lite:llm",
        "openrouter:qwen/qwen3.5-9b:llm:fp8",
        "openrouter:google/gemma-3n-e4b-it:llm",
        "openrouter:google/gemma-4-31b-it:llm:fp8",
        "openrouter:qwen/qwen3.5-27b:llm:fp8",
    }


def test_model_eval_runner_generates_failed_manifest_and_stable_record_ids(tmp_path) -> None:
    output = tmp_path / "results.json"
    config = ModelEvalRunConfig(
        registry_path=REGISTRY_PATH,
        fixture_set="smoke",
        mode="broad",
        roles={"slack_intake"},
        model_refs=["openai:gpt-5.4-nano"],
        scope="core",
        include_judge=False,
        repeat_runs=1,
        bootstrap_samples=0,
        output_path=output,
    )

    result = run_model_evals(Settings(), config, client=AlwaysFailClient())

    records = read_eval_records(output)
    failed_manifest = read_eval_records(Path(result["failed_manifest_jsonl_path"]))

    assert records
    assert len(failed_manifest) == len(records)
    assert all(record["record_id"] for record in records)
    assert all(record["failure_number"] is not None for record in records)
    assert Path(result["failed_manifest_md_path"]).exists()


def test_raw_and_parsed_artifacts_are_role_scoped_for_same_fixture_id(tmp_path) -> None:
    registry = load_model_registry(REGISTRY_PATH)
    candidate = select_model_candidates(
        registry,
        model_refs=["openai:gpt-5.4-nano"],
        roles={"intent_router", "source_classifier"},
        scope="core",
        include_judge=False,
        mode="fine-grained",
    )[0]
    intent_fixture = ModelEvalFixture(
        id="shared_fixture_id",
        scenario_group="shared",
        role="intent_router",
        input_text="remember this",
        expected={"intent": "remember"},
    )
    source_fixture = ModelEvalFixture(
        id="shared_fixture_id",
        scenario_group="shared",
        role="source_classifier",
        input_text="remember this",
        expected={"intent": "remember"},
    )
    call = ModelCallResult(
        status="ok",
        payload={"intent": "remember"},
        raw_text='{"intent":"remember"}',
        error=None,
        latency_ms=1,
        input_tokens=1,
        output_tokens=1,
        estimated_cost_usd=0.0,
    )

    raw_one = write_raw_output(tmp_path / "raw", run_id="run", candidate=candidate, fixture=intent_fixture, repeat_idx=0, call=call)
    raw_two = write_raw_output(tmp_path / "raw", run_id="run", candidate=candidate, fixture=source_fixture, repeat_idx=0, call=call)
    parsed_one = write_parsed_output(
        tmp_path / "parsed",
        run_id="run",
        candidate=candidate,
        fixture=intent_fixture,
        repeat_idx=0,
        payload=call.payload,
    )
    parsed_two = write_parsed_output(
        tmp_path / "parsed",
        run_id="run",
        candidate=candidate,
        fixture=source_fixture,
        repeat_idx=0,
        payload=call.payload,
    )

    assert raw_one != raw_two
    assert parsed_one != parsed_two
    assert "intent_router" in raw_one.name
    assert "source_classifier" in raw_two.name
    assert "intent_router" in parsed_one.name
    assert "source_classifier" in parsed_two.name
    assert json.loads(raw_one.read_text())["role"] == "intent_router"
    assert json.loads(raw_two.read_text())["role"] == "source_classifier"
    assert json.loads(parsed_one.read_text())["role"] == "intent_router"
    assert json.loads(parsed_two.read_text())["role"] == "source_classifier"


def test_rerun_failed_replaces_records_by_record_id(tmp_path) -> None:
    output = tmp_path / "results.json"
    initial = run_model_evals(
        Settings(),
        ModelEvalRunConfig(
            registry_path=REGISTRY_PATH,
            fixture_set="smoke",
            mode="broad",
            roles={"slack_intake"},
            model_refs=["openai:gpt-5.4-nano"],
            scope="core",
            include_judge=False,
            repeat_runs=1,
            bootstrap_samples=0,
            output_path=output,
        ),
        client=AlwaysFailClient(),
    )

    before = read_eval_records(output)
    before_by_id = {record["record_id"]: record for record in before}

    rerun_failed = run_rerun_failed(
        Settings(),
        registry_path=REGISTRY_PATH,
        source_path=output,
        failed_manifest_path=Path(initial["failed_manifest_jsonl_path"]),
        output_path=output,
        overwrite=True,
        bootstrap_samples=0,
        endpoint_max_concurrency=2,
        retry_attempts=0,
        retry_backoff_seconds=0,
        client=FakeEvalClient(),
    )

    after = read_eval_records(output)
    after_by_id = {record["record_id"]: record for record in after}

    assert len(before) == len(after)
    assert set(before_by_id) == set(after_by_id)
    assert any(before_by_id[record_id]["status"] == "fail" for record_id in before_by_id)
    assert all(after_by_id[record_id]["run_id"] == rerun_failed["run_id"] for record_id in after_by_id)
    assert all(after_by_id[record_id]["rerun_of_run_id"] == initial["run_id"] for record_id in after_by_id)


def test_live_provider_client_retries_transient_provider_error(monkeypatch) -> None:
    settings = Settings(openai_api_key="test-key")
    client = LiveProviderClient(
        settings,
        retry_attempts=2,
        retry_backoff_seconds=0,
    )
    attempts = {"count": 0}

    def fake_complete_text(*args: Any, **kwargs: Any) -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ProviderCallError("HTTP 503: high demand")
        return '{"intent":"remember","decision":"commit_success","memory_cards":[],"receipt":{"success":true,"details":[]},"answer":"ok"}'

    monkeypatch.setattr(client, "_complete_text", fake_complete_text)
    result = client.complete_json(
        type("Candidate", (), {"provider": "openai", "model": "gpt-5.4-nano", "ref": "openai:gpt-5.4-nano", "price_per_1m": {}})(),
        prompt="test",
        schema={},
    )

    assert attempts["count"] == 3
    assert result.status == "ok"
