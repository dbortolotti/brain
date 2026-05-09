from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any
import pytest

from memory_stack.config import Settings
from memory_stack.evals.model_fixtures import ModelEvalFixture, fixture_prompt, output_schema_for_fixture, select_fixtures
from memory_stack.evals.model_matrix import ModelCandidate, load_model_registry, select_model_candidates
from memory_stack.evals.model_runner import (
    ModelEvalRunConfig,
    build_work_items,
    merge_rerun_records,
    read_eval_records,
    raw_call_for_record,
    render_report,
    run_rescore,
    run_model_evals,
    run_rerun_failed,
    validate_against_schema,
    write_parsed_output,
    write_raw_output,
)
from memory_stack.evals.provider_client import LiveProviderClient, ModelCallResult, ProviderCallError, openai_reasoning_effort
from memory_stack.evals import provider_client as provider_client_module
from memory_stack.provider_auth import OpenAICodexCredential, upsert_openai_codex_profile
from memory_stack.evals.scoring import (
    EvalRecord,
    FailureClass,
    Summary,
    aggregate,
    aggregate_model_role_records,
    capability_coverage,
    is_stack_deployable,
    model_role_eligibility,
    pairwise_quality,
    score_model_output,
    semantic_quality_score_for_role,
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


class SemanticEmbeddingEvalClient(FakeEvalClient):
    def embed(self, candidate: Any, *, text: str) -> ModelCallResult:
        lowered = text.casefold()
        if any(term in lowered for term in ("goldman", "bill evans", "jazz piano")):
            vector = [1.0, 0.0, 0.0]
        elif any(term in lowered for term in ("cognee", "article", "semantic projection")):
            vector = [0.0, 1.0, 0.0]
        elif any(term in lowered for term in ("hijas", "gemelas", "daniele", "twin daughters")):
            vector = [0.0, 0.0, 1.0]
        else:
            vector = [0.05, 0.05, 0.05]
        return ModelCallResult(
            status="ok",
            payload={"embedding_vector_size": len(vector), "embedding_vector": vector},
            raw_text=json.dumps({"embedding_vector_size": len(vector), "embedding_vector": vector}),
            error=None,
            latency_ms=3,
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
    ]


def test_fine_grained_explicit_model_inherits_matrix_roles() -> None:
    registry = load_model_registry(REGISTRY_PATH)

    candidate = select_model_candidates(
        registry,
        model_refs=["openai:gpt-5.5-high"],
        roles=set(),
        scope="core",
        include_judge=True,
        mode="fine-grained",
    )[0]

    assert set(candidate.roles) == {
        "atomic_card_extractor",
        "entity_candidate_ranker",
        "source_takeaway_extractor",
        "conflict_candidate_detector",
        "recall_synthesizer",
        "groundedness_checker",
        "eval_judge",
    }


def test_select_fixtures_derives_fine_grained_roles() -> None:
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"intent_router"},
        mode="fine-grained",
    )

    assert fixtures
    assert all(fixture.role == "intent_router" for fixture in fixtures)


def test_source_classifier_fine_grained_fixtures_use_classifier_only_zero_tolerance() -> None:
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"source_classifier"},
        mode="fine-grained",
    )

    checks = {
        check
        for fixture in fixtures
        for check in fixture.zero_tolerance_checks
    }

    assert checks <= {
        "article_url_not_classified_as_source",
        "email_not_classified_as_email",
        "junk_not_rejected",
        "long_source_classified_as_memory",
        "table_not_classified_as_table",
    }
    assert "small_table_must_not_drop_values" not in checks
    assert "raw_email_exposed" not in checks


def test_conflict_fine_grained_fixtures_are_backend_policy_bound() -> None:
    candidate_fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"conflict_candidate_detector"},
        mode="fine-grained",
    )
    explainer_fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"conflict_explainer"},
        mode="fine-grained",
    )

    assert candidate_fixtures
    assert all(fixture.expected["detection_only"] is True for fixture in candidate_fixtures)
    assert all("decision" not in fixture.expected for fixture in candidate_fixtures)
    assert all("decision_any" not in fixture.expected for fixture in candidate_fixtures)
    assert explainer_fixtures
    assert {fixture.context["source_role"] for fixture in explainer_fixtures} == {"conflict_classifier"}

    action_space_by_fixture = {
        fixture.id: fixture.expected["safe_action_space"]
        for fixture in explainer_fixtures
    }
    assert action_space_by_fixture["duplicate_sam_bill_evans_001"] == [
        "link_duplicate",
        "keep_existing",
        "add_anyway",
        "edit",
        "cancel",
    ]
    assert action_space_by_fixture["additive_sam_preferences_001"] == [
        "add_new",
        "keep_existing",
        "edit",
        "cancel",
    ]
    assert action_space_by_fixture["supersession_sam_job_001"] == [
        "approve_supersession",
        "keep_both",
        "reject_new",
        "edit",
    ]


def test_entity_candidate_ranker_uses_entity_resolution_fixtures_only() -> None:
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"entity_candidate_ranker"},
        mode="fine-grained",
    )

    assert fixtures
    assert {fixture.context["source_role"] for fixture in fixtures} == {"entity_resolution"}


def test_durability_filter_derives_explicit_expected_durable_value() -> None:
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"durability_filter"},
        mode="fine-grained",
    )

    assert fixtures
    assert all("expected_durable" in fixture.expected for fixture in fixtures)


def test_success_receipt_generator_is_not_a_fine_grained_model_fixture() -> None:
    fixtures = select_fixtures(
        fixture_set="brain-model-test-v2",
        roles={"success_receipt_generator"},
        mode="fine-grained",
    )

    assert fixtures == []


def test_fixture_prompt_includes_role_specific_zero_tolerance_contracts() -> None:
    conflict_fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"conflict_candidate_detector"},
            mode="fine-grained",
        )
        if fixture.id == "conflict_employment_transition"
    )
    atomic_fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"atomic_card_extractor"},
            mode="fine-grained",
        )
        if fixture.id == "conversation_transcript_sam_001"
    )
    recall_fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"recall_synthesizer"},
            mode="fine-grained",
        )
        if fixture.id == "recall_absence_scoped"
    )

    conflict_prompt = fixture_prompt(conflict_fixture)
    atomic_prompt = fixture_prompt(atomic_fixture)
    recall_prompt = fixture_prompt(recall_fixture)

    assert "Detection-only role" in conflict_prompt
    assert "do not decide ask/keep/link/supersede behavior" in conflict_prompt
    assert "allowed values are: supersedes" in conflict_prompt
    assert "A supersedes classification is not a backend policy action." in conflict_prompt
    assert "do not add unsupported details" in atomic_prompt
    assert "attach ambiguous references to nearby topics" in atomic_prompt
    assert "no current evidence" in recall_prompt
    assert "do not infer a fact from absence" in recall_prompt


def test_conflict_candidate_detector_schema_is_detection_only() -> None:
    fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"conflict_candidate_detector"},
            mode="fine-grained",
        )
        if fixture.id == "conflict_employment_transition"
    )

    schema = output_schema_for_fixture(fixture)

    assert "memory_cards" not in schema["properties"]
    assert schema["properties"]["conflict_classification"]["enum"]
    assert "supersedes" in schema["properties"]["conflict_classification"]["enum"]
    assert schema["additionalProperties"] is False
    assert validate_against_schema(
        {
            "decision": "possible_conflict",
            "conflict_classification": "supersedes",
            "answer": "Existing current employer conflicts with the new employer transition.",
            "citations": ["Existing current fact: Sam works at Goldman."],
            "memory_cards": [{"kind": "conflict_evidence", "statement": "Sam moved."}],
        },
        schema,
        path="$",
    ) == ["$.memory_cards is not allowed"]
    assert validate_against_schema(
        {
            "decision": "possible_conflict",
            "conflict_classification": "employment_transition_conflict_candidate",
            "answer": "Possible conflict.",
            "citations": ["New fact: Sam left Goldman and joined Point72."],
        },
        schema,
        path="$",
    ) == ["$.conflict_classification must be one of supersedes, contradicts, duplicate, additive, correction, project_state_update, none"]


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
    assert result["record_count"] == 15
    assert {row["model"] for row in rows} == {
        "fastembed:intfloat/multilingual-e5-large",
        "openai:text-embedding-3-small",
        "openai:text-embedding-3-large",
        "voyage:voyage-4-lite",
        "voyage:voyage-4",
    }


def test_embedding_retrieval_probes_rank_positive_passage(tmp_path: Path) -> None:
    output = tmp_path / "eval.jsonl"
    config = ModelEvalRunConfig(
        registry_path=REGISTRY_PATH,
        fixture_set="development",
        roles={"embeddings"},
        model_refs=["fastembed:intfloat/multilingual-e5-large"],
        model_set=None,
        scope="core",
        include_judge=False,
        repeat_runs=1,
        bootstrap_samples=0,
        output_path=output,
    )

    result = run_model_evals(Settings(), config, client=SemanticEmbeddingEvalClient())

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    retrieval_rows = [
        row
        for row in rows
        if str(row["fixture_id"]).startswith("embedding_") and row["fixture_id"] != "embedding_retrieval_probe_001"
    ]
    assert result["record_count"] == 12
    assert len(retrieval_rows) == 9
    assert {row["status"] for row in retrieval_rows} == {"ok"}
    assert all(row["subscores"] == {"embedding_quality": 1.0} for row in retrieval_rows)


def test_live_provider_client_fastembed_embedding_uses_local_vector_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        provider_client_module,
        "fastembed_vector",
        lambda model, text: [0.1] * 1024,
    )
    settings = Settings(
        profile="local",
        llm_provider="ollama",
        llm_model="qwen3:8b",
        llm_api_key="ollama",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
        allow_cloud_keys_in_local=True,
    )
    candidate = ModelCandidate(
        provider="fastembed",
        model="intfloat/multilingual-e5-large",
        kind="embedding",
    )

    result = LiveProviderClient(settings).embed(candidate, text="brain eval test")

    assert result.status == "ok"
    assert result.payload == {"embedding_vector_size": 1024, "embedding_vector": [0.1] * 1024}


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


def test_entity_candidate_ranker_accepts_ambiguity_preserving_actions() -> None:
    fixture = ModelEvalFixture(
        id="ambiguous",
        scenario_group="ambiguous_sam",
        role="entity_candidate_ranker",
        input_text="Existing: Sam A and Sam B. New: Sam likes jazz.",
        expected={"entity_action": "needs_clarification"},
        zero_tolerance_checks=("entity_overmerge",),
    )

    scores, zero_tolerance, notes = score_model_output(
        fixture,
        {
            "decision": "defer",
            "entity_resolution": {"action": "ambiguous", "entity_id": None},
            "answer": "Please clarify which Sam this refers to.",
        },
        status="ok",
    )

    assert scores["entity_safety"] == 1.0
    assert zero_tolerance is False
    assert notes == []


def test_intent_router_ignores_table_zero_tolerance_checks() -> None:
    fixture = ModelEvalFixture(
        id="router_table_input",
        role="intent_router",
        scenario_group="router",
        input_text="/brain remember | Person | Preference | ...",
        expected={"intent": "remember"},
        zero_tolerance_checks=(
            "small_table_must_not_drop_values",
            "source_invention",
            "prompt_injection_followed",
        ),
    )

    scores, zero, types = score_model_output(fixture, {"intent": "remember"}, status="ok")

    assert scores["decision_correctness"] == 1.0
    assert zero is False
    assert "small_table_must_not_drop_values" not in types
    assert "source_invention" not in types


def test_entity_mention_extractor_ignores_receipt_checks() -> None:
    fixture = ModelEvalFixture(
        id="entity_mentions",
        role="entity_mention_extractor",
        scenario_group="entities",
        input_text="Sam from Goldman likes Bill Evans.",
        expected={"must_include": ["Sam", "Goldman", "Bill Evans"]},
        zero_tolerance_checks=("success_receipt_missing", "entity_overmerge"),
    )

    payload = {
        "memory_cards": [
            {
                "kind": "person_interaction",
                "statement": "Sam from Goldman likes Bill Evans.",
                "entities": [
                    {"name": "Sam", "type": "person"},
                    {"name": "Goldman", "type": "organization"},
                    {"name": "Bill Evans", "type": "person"},
                ],
            }
        ]
    }

    _scores, _zero, types = score_model_output(fixture, payload, status="ok")

    assert "success_receipt_missing" not in types


def test_success_receipt_generator_fails_missing_receipt() -> None:
    fixture = ModelEvalFixture(
        id="receipt",
        role="success_receipt_generator",
        scenario_group="receipt",
        input_text="Stored memory mem_1.",
        expected={"receipt_terms": ["mem_1", "Undo"]},
        zero_tolerance_checks=("success_receipt_missing",),
    )

    _scores, zero, types = score_model_output(fixture, {"decision": "commit_success"}, status="ok")

    assert zero is True
    assert "success_receipt_missing" in types


def test_memory_kinds_any_accepts_any_expected_kind() -> None:
    fixture = ModelEvalFixture(
        id="research_question",
        role="memory_kind_classifier",
        scenario_group="kind",
        input_text="Need to research the relationship between language and intelligence.",
        expected={"memory_kinds_any": ["research_question", "open_question"]},
    )

    scores, zero, types = score_model_output(
        fixture,
        {"memory_cards": [{"kind": "open_question", "statement": "Research language and intelligence."}]},
        status="ok",
    )

    assert scores["memory_card_quality"] == 1.0
    assert zero is False
    assert types == []


def test_recall_daughters_fixture_does_not_require_twins_for_direct_question() -> None:
    fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"recall_synthesizer"},
        )
        if fixture.id == "recall_daughters_001"
    )

    scores, zero, types = score_model_output(
        fixture,
        {"answer": "Your daughters are Nur and Sara.", "citations": ["mem_family"]},
        status="ok",
    )

    assert scores["recall_quality"] == 1.0
    assert zero is False
    assert types == []


def test_recall_absence_allows_uncertain_repetition_of_query_phrase() -> None:
    fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"recall_synthesizer"},
        )
        if fixture.id == "recall_absence_scoped"
    )

    scores, zero, types = score_model_output(
        fixture,
        {"answer": "I don’t have any current memory indicating whether Sara prefers morning flights."},
        status="ok",
    )

    assert scores["recall_quality"] == 1.0
    assert zero is False
    assert types == []


def test_recall_irrelevant_dump_zero_tolerance_requires_irrelevant_content() -> None:
    fixture = ModelEvalFixture(
        id="recall_relevance",
        role="recall_synthesizer",
        scenario_group="recall",
        input_text="Question: What did I conclude about Brain and Cognee?",
        expected={
            "must_include": ["Brain DB", "Cognee"],
            "must_not_include": ["Bill Evans"],
        },
        zero_tolerance_checks=("irrelevant_memory_dump",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {"answer": "Cognee should be a rebuildable projection."},
        status="ok",
    )

    assert scores["recall_quality"] < 1.0
    assert zero is False
    assert types == []

    _bad_scores, bad_zero, bad_types = score_model_output(
        fixture,
        {"answer": "Cognee should be rebuildable. Bill Evans is Sam's music preference."},
        status="ok",
    )

    assert bad_zero is True
    assert bad_types == ["irrelevant_memory_dump"]


def test_deleted_memory_returned_zero_tolerance_is_enforced_for_recall() -> None:
    fixture = ModelEvalFixture(
        id="recall_deleted",
        role="recall_synthesizer",
        scenario_group="recall",
        input_text="Current: Sam likes Bill Evans. Deleted: Sam likes Taylor Swift.",
        expected={
            "must_include": ["Bill Evans"],
            "must_not_include": ["Taylor Swift"],
        },
        zero_tolerance_checks=("deleted_memory_returned",),
    )

    _scores, zero, types = score_model_output(
        fixture,
        {"answer": "Sam likes Bill Evans and Taylor Swift."},
        status="ok",
    )

    assert zero is True
    assert types == ["deleted_memory_returned"]


def test_deleted_memory_exclusion_is_not_returned_as_current() -> None:
    fixture = ModelEvalFixture(
        id="recall_deleted",
        role="recall_synthesizer",
        scenario_group="recall",
        input_text="Current: Sam likes Bill Evans. Deleted: Sam likes Taylor Swift.",
        expected={
            "must_include": ["Bill Evans"],
            "must_not_include": ["Taylor Swift"],
        },
        zero_tolerance_checks=("deleted_memory_returned",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {"answer": "Sam likes Bill Evans. There is no current evidence that Sam likes Taylor Swift."},
        status="ok",
    )

    assert scores["recall_quality"] == 1.0
    assert zero is False
    assert types == []


def test_unsupported_inference_zero_tolerance_requires_forbidden_content() -> None:
    fixture = ModelEvalFixture(
        id="atomic_missing_expected_term",
        role="atomic_card_extractor",
        scenario_group="atomic",
        input_text="Sam still listens to Bill Evans. Sam should be sent an article.",
        expected={
            "must_include": ["Bill Evans", "article"],
            "must_not_include": ["hates Bill Evans"],
        },
        zero_tolerance_checks=("unsupported_inference",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "memory_cards": [
                {
                    "kind": "music_preference",
                    "statement": "Sam still listens to Bill Evans.",
                }
            ],
        },
        status="ok",
    )

    assert scores["memory_card_quality"] < 1.0
    assert zero is False
    assert types == []

    _bad_scores, bad_zero, bad_types = score_model_output(
        fixture,
        {
            "memory_cards": [
                {
                    "kind": "music_preference",
                    "statement": "Sam hates Bill Evans.",
                }
            ],
        },
        status="ok",
    )

    assert bad_zero is True
    assert bad_types == ["unsupported_inference"]


def test_intent_router_scores_router_aliases_from_source_role() -> None:
    fixture = ModelEvalFixture(
        id="router_from_slack",
        role="intent_router",
        scenario_group="slack_intake",
        input_text="/brain remember Sam likes jazz",
        expected={"decision": "commit_success"},
        context={"source_role": "slack_intake"},
    )

    scores, zero, _types = score_model_output(fixture, {"intent": "store_fact"}, status="ok")

    assert zero is False
    assert scores["decision_correctness"] == 1.0


def test_source_classifier_semantic_score_uses_source_split_not_downstream_decision() -> None:
    score = semantic_quality_score_for_role(
        "source_classifier",
        {
            "decision_correctness": 0.0,
            "source_memory_split": 1.0,
        },
    )

    assert score == 1.0


def test_source_classifier_ignores_extraction_zero_tolerance_checks() -> None:
    fixture = ModelEvalFixture(
        id="source_classifier_table",
        role="source_classifier",
        scenario_group="source",
        input_text="| Person | Preference |\n| --- | --- |\n| Sam | Bill Evans |",
        expected={"source_memory_split": True},
        zero_tolerance_checks=("small_table_must_not_drop_values", "raw_email_exposed"),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "input_class": "source",
            "source_kind": "table",
            "should_create_source": True,
            "should_extract_memories": True,
            "memory_cards": [{"statement": "wrong downstream extraction"}],
        },
        status="ok",
    )

    assert scores["source_memory_split"] == 1.0
    assert zero is False
    assert types == []


def test_source_classifier_catches_classifier_specific_failures() -> None:
    fixture = ModelEvalFixture(
        id="source_classifier_table",
        role="source_classifier",
        scenario_group="source",
        input_text="| Person | Preference |\n| --- | --- |\n| Sam | Bill Evans |",
        expected={"source_memory_split": True},
        zero_tolerance_checks=("table_not_classified_as_table",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {"input_class": "memory", "source_kind": None, "should_create_source": False},
        status="ok",
    )

    assert scores["source_memory_split"] < 1.0
    assert zero is True
    assert types == ["table_not_classified_as_table"]


def test_source_classifier_zero_tolerance_ignores_downstream_extraction_boolean() -> None:
    fixture = ModelEvalFixture(
        id="source_classifier_article",
        role="source_classifier",
        scenario_group="source",
        input_text="Remember this article: https://example.com/a Mock fetched article: Graph memory helps recall.",
        expected={"source_memory_split": True},
        zero_tolerance_checks=("article_url_not_classified_as_source",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "input_class": "source",
            "source_kind": "article",
            "should_create_source": True,
            "should_extract_memories": False,
            "answer": "Classified as an article source.",
            "citations": ["https://example.com/a"],
        },
        status="ok",
    )

    assert scores["source_memory_split"] < 1.0
    assert zero is False
    assert types == []


def test_source_classifier_long_source_zero_tolerance_allows_source_subtype_miss() -> None:
    fixture = ModelEvalFixture(
        id="source_classifier_markdown",
        role="source_classifier",
        scenario_group="source",
        input_text=(
            "# Chat Summary\n"
            "Brain DB remains source of truth. Cognee is a rebuildable projection. "
            "Slack should be a strict intake agent. Telegram may be considered later."
        ),
        expected={"source_memory_split": True},
        zero_tolerance_checks=("long_source_classified_as_memory",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "input_class": "source",
            "source_kind": "article",
            "should_create_source": True,
            "should_extract_memories": True,
            "answer": "Classified as a source, though with the wrong subtype.",
            "citations": [],
        },
        status="ok",
    )

    assert scores["source_memory_split"] < 1.0
    assert zero is False
    assert types == []


def test_table_policy_zero_tolerance_checks_expected_values_directly() -> None:
    fixture = ModelEvalFixture(
        id="small_table",
        role="table_policy_handler",
        scenario_group="small_table",
        input_text="| Person | Preference |\n| Sam | Bill Evans |\n| Daniele | Knowledge graphs |",
        expected={
            "memory_kinds": ["table_note"],
            "must_include": ["Bill Evans", "Knowledge graphs"],
            "source_memory_split": True,
        },
        zero_tolerance_checks=("small_table_must_not_drop_values",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "decision": "commit",
            "memory_cards": [
                {"kind": "preference", "statement": "Sam prefers Bill Evans."},
                {"kind": "preference", "statement": "Daniele prefers Knowledge graphs."},
            ],
        },
        status="ok",
    )

    assert scores["memory_card_quality"] == 1.0
    assert zero is False
    assert types == []


def test_numeric_exactness_does_not_match_forbidden_numeric_prefix() -> None:
    fixture = ModelEvalFixture(
        id="numeric_table",
        role="table_policy_handler",
        scenario_group="numeric_table",
        input_text="| Run | Reward | Sharpe |\n| PPO-002 | 0.18 | 0.51 |",
        expected={
            "must_include": ["0.18", "0.51"],
            "must_not_include": ["0.5"],
        },
        zero_tolerance_checks=("numeric_values_altered",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "decision": "preserve_small_table_exactly",
            "memory_cards": [{"kind": "table_note", "statement": "PPO-002 reward 018 and Sharpe 051."}],
        },
        status="ok",
    )

    assert scores["memory_card_quality"] == 1.0
    assert zero is False
    assert types == []


def test_durability_filter_scores_durable_vs_non_durable_decision() -> None:
    fixture = ModelEvalFixture(
        id="durability_weather",
        role="durability_filter",
        scenario_group="durability",
        input_text="It is raining outside.",
        expected={},
        zero_tolerance_checks=("no_durable_value_junk_committed",),
    )

    bad_scores, _bad_zero, _bad_types = score_model_output(
        fixture,
        {"memory_cards": [{"statement": "It is raining outside."}]},
        status="ok",
    )
    good_scores, _good_zero, _good_types = score_model_output(
        fixture,
        {"decision": "reject", "memory_cards": []},
        status="ok",
    )

    assert bad_scores["durability_decision"] == 0.0
    assert good_scores["durability_decision"] == 1.0


def test_conflict_candidate_detector_rejects_auto_commit_policy_decision() -> None:
    fixture = ModelEvalFixture(
        id="conflict_candidate",
        role="conflict_candidate_detector",
        scenario_group="conflict",
        input_text="Existing: Sam works at Goldman. New: Sam left Goldman and joined Point72.",
        expected={
            "conflict_classification_any": ["supersedes", "possible_supersession"],
            "requires_user_choice": True,
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    _scores, zero, types = score_model_output(
        fixture,
        {
            "possible_conflict": True,
            "conflict_type": "possible_supersession",
            "requires_user_choice": False,
            "decision": "commit_success",
        },
        status="ok",
    )

    assert zero is True
    assert types == ["silent_high_confidence_overwrite"]


def test_conflict_candidate_detector_classification_miss_is_not_overwrite_zero_tolerance() -> None:
    fixture = ModelEvalFixture(
        id="conflict_candidate",
        role="conflict_candidate_detector",
        scenario_group="conflict",
        input_text="Existing: Sam works at Goldman. New: Sam left Goldman and joined Point72.",
        expected={
            "conflict_classification": "supersedes",
            "detection_only": True,
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "conflict_type": "employment_transition_conflict_candidate",
            "decision": "possible_conflict",
            "memory_cards": [],
            "repair_options": [],
        },
        status="ok",
    )

    assert scores["conflict_safety"] == 0.0
    assert zero is False
    assert types == []


def test_conflict_explainer_rejects_actions_outside_backend_safe_space() -> None:
    fixture = ModelEvalFixture(
        id="conflict_explainer",
        role="conflict_explainer",
        scenario_group="conflict",
        input_text="Explain conflict.",
        expected={
            "safe_action_space": ["approve_supersession", "keep_both", "reject_new", "edit"],
            "repair_terms": ["approve", "keep", "reject", "edit"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {"repair_options": ["approve_supersession", "overwrite_current"]},
        status="ok",
    )

    assert scores["repair_quality"] == 0.0
    assert zero is True
    assert types == ["silent_high_confidence_overwrite"]


def test_conflict_explainer_classification_miss_is_not_overwrite_zero_tolerance() -> None:
    fixture = ModelEvalFixture(
        id="conflict_explainer",
        role="conflict_explainer",
        scenario_group="conflict",
        input_text="Existing: Sam works at Goldman. New: Sam left Goldman and joined Point72.",
        expected={
            "conflict_classification": "supersedes",
            "safe_action_space": ["approve_supersession", "keep_both", "reject_new", "edit"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "decision": "needs_user_choice",
            "conflict_classification": "employment_transition_conflict",
            "answer": "Use approve_supersession, keep_both, reject_new, or edit.",
        },
        status="ok",
    )

    assert scores["conflict_safety"] == 0.0
    assert zero is False
    assert types == []


def test_repair_option_generator_accepts_colon_prefixed_safe_actions() -> None:
    fixture = ModelEvalFixture(
        id="additive_sam_preferences_001",
        role="repair_option_generator",
        scenario_group="additive_preference",
        input_text="Existing memory: Sam from Goldman likes Bill Evans. New: Sam from Goldman also likes Sonny Rollins.",
        expected={
            "safe_action_space": ["add_new", "keep_existing", "edit", "cancel"],
            "must_include": ["Bill Evans", "Sonny Rollins"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "answer": "The new fact is additive.",
            "repair_options": [
                "add_new: Add Sonny Rollins as an additional liked artist.",
                "keep_existing: Keep only the existing Bill Evans preference.",
                "edit: Revise the preference wording manually.",
                "cancel: Do not make changes.",
            ],
        },
        status="ok",
    )

    assert scores["repair_quality"] == 1.0
    assert zero is False
    assert types == []


def test_repair_option_generator_scores_action_id_coverage() -> None:
    fixture = ModelEvalFixture(
        id="supersession_sam_job_001",
        role="repair_option_generator",
        scenario_group="employment_transition",
        input_text="Existing memory: Sam works at Goldman. New memory: Sam left Goldman and joined Point72.",
        expected={
            "safe_action_space": ["approve_supersession", "keep_both", "reject_new", "edit"],
            "repair_terms": ["approve", "keep both", "reject", "edit"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "answer": "Choose one repair option.",
            "repair_options": ["approve_supersession", "keep_both", "reject_new", "edit"],
        },
        status="ok",
    )

    assert scores["repair_quality"] == 1.0
    assert zero is False
    assert types == []


def test_repair_option_generator_uses_base_fixture_terms_for_variants() -> None:
    fixture = next(
        fixture
        for fixture in select_fixtures(
            fixture_set="brain-model-test-v2",
            roles={"repair_option_generator"},
            mode="fine-grained",
        )
        if fixture.id == "vague_memory_001__punctuation" and fixture.context.get("variant") == "punctuation"
    )

    assert fixture.context["base_fixture_id"] == "vague_memory_001"
    assert fixture.expected["repair_terms"] == ["specif"]


def test_repair_option_generator_accepts_pronoun_specific_rewrite_options() -> None:
    fixture = ModelEvalFixture(
        id="unresolved_pronoun_001",
        role="repair_option_generator",
        scenario_group="ambiguous_reference",
        input_text="Remember he prefers the other one.",
        expected={"repair_terms": ["he", "other one"]},
        zero_tolerance_checks=("unresolved_pronoun_committed",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "answer": "Ask for a self-contained rewrite because “he” and “the other one” are ambiguous.",
            "repair_options": [
                "Specify who “he” refers to.",
                "Specify the two options/items being compared.",
                "Rewrite the full preference as a complete statement.",
            ],
        },
        status="ok",
    )

    assert scores["repair_quality"] == 1.0
    assert zero is False
    assert types == []


def test_repair_option_generator_accepts_validator_pronoun_repair_options() -> None:
    fixture = ModelEvalFixture(
        id="validator_blocks_unresolved_pronoun_001",
        role="repair_option_generator",
        scenario_group="validator_blocks_pronoun",
        input_text='LLM proposal: {"memory_cards":[{"statement":"He prefers the other one."}]}',
        expected={"repair_terms": ["he", "other one"]},
        zero_tolerance_checks=("unresolved_pronoun_committed",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "answer": "The proposed memory is too ambiguous to save because the pronoun and comparison target are unresolved.",
            "repair_options": [
                "Ask the user who “he” refers to before saving anything.",
                "Ask the user what “the other one” refers to before saving anything.",
                "Ask the user to restate the preference with explicit names or items.",
            ],
        },
        status="ok",
    )

    assert scores["repair_quality"] == 1.0
    assert zero is False
    assert types == []


def test_repair_option_generator_accepts_clarification_prose_for_sara_niece() -> None:
    fixture = ModelEvalFixture(
        id="conflict_sara_niece_001",
        role="repair_option_generator",
        scenario_group="high_confidence_family_conflict",
        input_text="Existing high-confidence memory: Sara is Daniele's daughter and Nur's twin. New: Sara is my niece.",
        expected={
            "safe_action_space": ["ask_clarification", "add_new", "keep_existing", "reject_new", "edit"],
            "must_include": ["daughter", "niece"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "answer": "Ask for clarification before changing the existing memory.",
            "repair_options": [
                "Ask for clarification: when you say Sara is your niece, how are you related?",
                "If confirmed, add: Sara is the user's niece.",
                "Keep existing memory unchanged: Sara is Daniele's daughter and Nur's twin.",
            ],
        },
        status="ok",
    )

    assert scores["repair_quality"] == 1.0
    assert zero is False
    assert types == []


def test_repair_option_generator_rejects_supersession_for_sara_niece() -> None:
    fixture = ModelEvalFixture(
        id="conflict_sara_niece_001",
        role="repair_option_generator",
        scenario_group="high_confidence_family_conflict",
        input_text="Existing high-confidence memory: Sara is Daniele's daughter and Nur's twin. New: Sara is my niece.",
        expected={
            "safe_action_space": ["ask_clarification", "add_new", "keep_existing", "reject_new", "edit"],
            "must_include": ["daughter", "niece"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    )

    scores, zero, types = score_model_output(
        fixture,
        {
            "answer": "Choose a repair option.",
            "repair_options": [
                "approve_supersession: Replace the existing Sara relationship memory with Sara is my niece.",
                "edit: Clarify the relationship.",
            ],
        },
        status="ok",
    )

    assert scores["repair_quality"] == 0.0
    assert zero is True
    assert types == ["silent_high_confidence_overwrite"]


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


def test_zero_tolerance_failure_is_operational_success() -> None:
    summary = aggregate(
        [
            EvalRecord(
                model="a",
                role="recall_synthesizer",
                operational_success=True,
                json_parseable=True,
                schema_valid=True,
                semantic_evaluable=True,
                zero_tolerance_failure=True,
                failure_class=FailureClass.ZERO_TOLERANCE_FAILURE,
                quality_score=0.8,
            )
        ],
        bootstrap_samples=0,
    )

    assert summary.records_operational_success == 1
    assert summary.records_json_parseable == 1
    assert summary.records_schema_valid == 1
    assert summary.records_semantic_evaluable == 1
    assert summary.zero_tolerance_failures == 1


def test_model_role_eligibility_uses_observed_gate_and_state() -> None:
    summary = Summary(
        model="m",
        role="entity_mention_extractor",
        records_total=66,
        records_operational_success=66,
        records_json_parseable=66,
        records_schema_valid=66,
        records_semantic_evaluable=66,
        records_quality_passed=30,
        operational_success_rate=1.0,
        json_parse_success_rate=1.0,
        schema_validity_rate=1.0,
        semantic_score_mean=0.903,
        zero_tolerance_failures=0,
        subscores={"entity_safety": {"mean": 0.95}},
    )

    eligible, reasons, state = model_role_eligibility(summary)

    assert eligible is True
    assert reasons == []
    assert state == "eligible"


def test_model_role_eligibility_reports_insufficient_sample() -> None:
    summary = Summary(
        model="m",
        role="eval_judge",
        records_total=10,
        records_operational_success=10,
        records_json_parseable=10,
        records_schema_valid=10,
        records_semantic_evaluable=10,
        operational_success_rate=1.0,
        json_parse_success_rate=1.0,
        schema_validity_rate=1.0,
        semantic_score_mean=0.95,
        zero_tolerance_failures=0,
    )

    eligible, reasons, state = model_role_eligibility(summary)

    assert eligible is False
    assert "semantic_evaluable_below_minimum" in reasons
    assert state == "insufficient_sample"


def test_intent_router_low_risk_gate_allows_observed_rate_candidate() -> None:
    summary = Summary(
        model="m",
        role="intent_router",
        records_total=171,
        records_operational_success=171,
        records_json_parseable=165,
        records_schema_valid=165,
        records_semantic_evaluable=165,
        records_quality_passed=142,
        operational_success_rate=1.0,
        json_parse_success_rate=165 / 171,
        schema_validity_rate=1.0,
        quality_pass_rate=142 / 165,
        semantic_score_mean=0.861,
        zero_tolerance_failures=0,
        subscores={"decision_correctness": {"mean": 0.861}},
    )

    eligible, reasons, state = model_role_eligibility(summary)

    assert eligible is True
    assert reasons == []
    assert state == "eligible"


def test_legacy_zero_latency_is_unknown_not_successful_latency(tmp_path) -> None:
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "payload": {"intent": "remember"},
                "raw_text": '{"intent":"remember"}',
                "latency_ms": 0,
            }
        ),
        encoding="utf-8",
    )

    call = raw_call_for_record({"raw_output_path": str(raw_path), "latency_ms": 0})

    assert call.latency_ms is None


def test_quality_failure_not_counted_as_provider_failure() -> None:
    summary = aggregate(
        [
            EvalRecord(
                model="a",
                role="intent_router",
                operational_success=True,
                json_parseable=True,
                schema_valid=True,
                semantic_evaluable=True,
                failure_class=FailureClass.QUALITY_FAILURE,
                quality_score=0.5,
            )
        ],
        bootstrap_samples=0,
    )

    assert summary.records_operational_success == 1
    assert summary.records_json_parseable == 1
    assert summary.records_schema_valid == 1
    assert summary.records_semantic_evaluable == 1
    assert summary.semantic_score_mean == 0.5


def test_intent_router_semantic_score_uses_role_weighting() -> None:
    summary = aggregate(
        [
            EvalRecord(
                model="a",
                role="intent_router",
                operational_success=True,
                json_parseable=True,
                schema_valid=True,
                semantic_evaluable=True,
                subscores={
                    "decision_correctness": 0.0,
                    "memory_card_quality": 1.0,
                    "repair_quality": 1.0,
                    "recall_quality": 1.0,
                },
                quality_score=None,
            )
        ],
        bootstrap_samples=0,
    )

    assert summary.semantic_score_mean == 0.0


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
    assert summary["records_json_parseable"] == 2
    assert summary["records_semantic_evaluable"] == 2
    assert summary["records_quality_passed"] == 1
    assert summary["cost_per_1k_attempted"] == pytest.approx(150.0)
    assert summary["cost_per_1k_successful"] == pytest.approx(150.0)
    assert summary["cost_per_1k_semantic"] == pytest.approx(150.0)
    assert summary["latency_p50_ms"] is not None
    assert summary["subscores"]["decision_correctness"]["method"] == "hierarchical_bootstrap_by_scenario_fixture_variant"
    assert zero_tolerance_upper_bound(0, 10) == 0.3


def test_embeddings_do_not_satisfy_runtime_roles() -> None:
    eligible = [
        Summary(role="embeddings", eligible=True),
    ]

    deployable, missing = is_stack_deployable(eligible)

    assert deployable is False
    assert "slack_intake" in missing


def test_router_capability_satisfied_by_intent_router() -> None:
    summaries = [
        Summary(role="intent_router", model="openai:gpt-5-nano", eligible=True),
    ]

    coverage = capability_coverage(summaries)

    assert coverage["router"]["status"] == "eligible"


def test_slack_intake_uses_deterministic_success_receipts() -> None:
    summaries = [
        Summary(role="source_classifier", model="m1", eligible=True),
        Summary(role="durability_filter", model="m1", eligible=True),
        Summary(role="memory_kind_classifier", model="m1", eligible=True),
        Summary(role="repair_option_generator", model="m1", eligible=True),
    ]

    coverage = capability_coverage(summaries)

    assert coverage["slack_intake"]["status"] == "eligible"
    assert "success_receipt_template" in coverage["slack_intake"]["deterministic_roles"]


def test_embeddings_optional_if_not_tested() -> None:
    summaries = [
        Summary(role="intent_router", model="m1", eligible=True),
    ]

    coverage = capability_coverage(summaries)
    deployable, missing = is_stack_deployable(summaries, mode="fine-grained")

    assert coverage["embeddings"]["status"] == "not_tested"
    assert "embeddings" not in missing
    assert deployable is False


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
    client = LiveProviderClient(
        Settings(openai_api_key="test-key", openai_auth_mode="api_key"),
        http_client=http_client,
    )
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
    assert "instructions" in http_client.last_json
    assert http_client.last_json["input"][0]["role"] == "user"
    assert http_client.last_json["store"] is False
    assert http_client.last_json["stream"] is False
    assert http_client.last_json["reasoning"] == {"effort": "xhigh"}


def test_live_provider_client_defaults_openai_text_to_oauth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.last_headers: dict[str, str] | None = None
            self.last_url: str | None = None
            self.last_json: dict[str, Any] | None = None

        def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> Any:
            self.last_url = url
            self.last_headers = headers
            self.last_json = json

            class Response:
                status_code = 200
                text = 'data: {"type":"response.output_text.delta","delta":"{}"}\n\ndata: [DONE]\n\n'

                @staticmethod
                def json() -> dict[str, Any]:
                    return {"output_text": "{}"}

            return Response()

    empty_codex_home = tmp_path / "empty-codex"
    empty_codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(empty_codex_home))
    settings = Settings(
        openai_api_key="sk-should-not-be-used",
        brain_provider_auth_profiles_path=str(tmp_path / "profiles.json"),
        brain_provider_auth_state_dir=str(tmp_path / "state"),
    )
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="oauth-access",
            refresh="oauth-refresh",
            expires=int(time.time() * 1000) + 600_000,
        ),
    )
    http_client = RecordingClient()
    client = LiveProviderClient(settings, http_client=http_client)
    candidate = select_model_candidates(
        load_model_registry(REGISTRY_PATH),
        model_refs=["openai:gpt-5.5"],
        roles={"eval_judge"},
        scope="core",
        include_judge=True,
    )[0]

    client.complete_json(candidate, prompt="test", schema={})

    assert http_client.last_url == "https://chatgpt.com/backend-api/codex/responses"
    assert http_client.last_headers == {"Authorization": "Bearer oauth-access"}
    assert http_client.last_json is not None
    assert http_client.last_json["store"] is False
    assert http_client.last_json["stream"] is True
    assert "max_output_tokens" not in http_client.last_json


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

    assert len(items) >= 2
    first_wave = items[:2]
    assert {item.candidate.endpoint_key for item in first_wave} == {
        "openai:gpt-5-nano:llm",
        "google:gemini-2.5-flash-lite:llm",
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
    assert any(before_by_id[record_id]["status"] == "provider_fail" for record_id in before_by_id)
    assert all(after_by_id[record_id]["run_id"] == rerun_failed["run_id"] for record_id in after_by_id)
    assert all(after_by_id[record_id]["rerun_of_run_id"] == initial["run_id"] for record_id in after_by_id)


def test_merge_rerun_records_replaces_record_by_id() -> None:
    original = [
        {"record_id": "abc", "status": "fail", "failure_class": "json_parse_error"},
        {"record_id": "def", "status": "ok", "failure_class": "none"},
    ]
    rerun = [
        {"record_id": "abc", "status": "ok", "failure_class": "none"},
    ]

    merged = merge_rerun_records(original, rerun)

    assert len(merged) == 2
    assert next(row for row in merged if row["record_id"] == "abc")["status"] == "ok"


def test_merge_rerun_records_preserves_non_rerun_records() -> None:
    original = [
        {"record_id": "abc", "status": "fail"},
        {"record_id": "def", "status": "ok"},
    ]
    rerun = [
        {"record_id": "abc", "status": "ok"},
    ]

    merged = merge_rerun_records(original, rerun)

    assert next(row for row in merged if row["record_id"] == "def")["status"] == "ok"


def test_rescore_removes_router_table_failure_and_regenerates_artifacts(tmp_path) -> None:
    raw_dir = tmp_path / "raw" / "eval_1"
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "openai_gpt-5-nano__intent_router__router_remember_plain__0.json"
    raw_path.write_text(
        json.dumps(
            {
                "run_id": "eval_1",
                "model": "openai:gpt-5-nano",
                "role": "intent_router",
                "fixture_id": "router_remember_plain",
                "status": "ok",
                "error": None,
                "payload": {"intent": "remember"},
                "raw_text": '{"intent":"remember"}',
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "results.json"
    output.write_text(
        json.dumps(
            [
                {
                    "record_id": "router-1",
                    "run_id": "eval_1",
                    "fixture_set_version": "brain-model-test-v2",
                    "policy_version": "memory-policy-v1",
                    "model": "openai:gpt-5-nano",
                    "provider": "openai",
                    "role": "intent_router",
                    "fixture_id": "router_remember_plain",
                    "variant_id": "base",
                    "repeat_idx": 0,
                    "status": "ok",
                    "failure_class": "zero_tolerance_failure",
                    "failure_reason_codes": ["small_table_must_not_drop_values"],
                    "failure_message": None,
                    "operational_success": True,
                    "json_parseable": True,
                    "schema_valid": True,
                    "semantic_evaluable": True,
                    "zero_tolerance_failure": True,
                    "zero_tolerance_failure_types": ["small_table_must_not_drop_values"],
                    "quality_score": 0.0,
                    "subscores": {"decision_correctness": 0.0},
                    "raw_output_path": str(raw_path),
                    "parsed_output_path": None,
                    "scenario_group": "router_remember",
                    "notes": ["small_table_must_not_drop_values"],
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    result = run_rescore(
        registry_path=REGISTRY_PATH,
        source_path=output,
        output_path=output,
        overwrite=True,
        bootstrap_samples=0,
    )

    rescored = read_eval_records(output)
    router = rescored[0]

    assert router["zero_tolerance_failure"] is False
    assert "small_table_must_not_drop_values" not in router["zero_tolerance_failure_types"]
    assert router["operational_success"] is True
    assert router["semantic_evaluable"] is True
    assert router["failure_class"] == "none"
    assert router["status"] == "ok"
    assert Path(result["failed_manifest_jsonl_path"]).exists()
    assert Path(result["report_md_path"]).exists()
    assert Path(result["report_html_path"]).exists()


def test_rescore_rejects_semantic_to_provider_transition(tmp_path) -> None:
    raw_path = tmp_path / "raw_fail.json"
    raw_path.write_text(
        json.dumps(
            {
                "run_id": "eval_1",
                "model": "openai:gpt-5-nano",
                "role": "intent_router",
                "fixture_id": "router_remember_plain",
                "status": "fail",
                "error": "missing provider API key for openai",
                "payload": None,
                "raw_text": "",
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "results.json"
    output.write_text(
        json.dumps(
            [
                {
                    "record_id": "router-1",
                    "run_id": "eval_1",
                    "fixture_set_version": "brain-model-test-v2",
                    "policy_version": "memory-policy-v1",
                    "model": "openai:gpt-5-nano",
                    "provider": "openai",
                    "role": "intent_router",
                    "fixture_id": "router_remember_plain",
                    "variant_id": "base",
                    "repeat_idx": 0,
                    "status": "quality_fail",
                    "failure_class": "quality_failure",
                    "failure_reason_codes": ["wrong_intent_for_explicit_command"],
                    "failure_message": None,
                    "operational_success": True,
                    "json_parseable": True,
                    "schema_valid": True,
                    "semantic_evaluable": True,
                    "quality_passed": False,
                    "zero_tolerance_failure": False,
                    "zero_tolerance_failure_types": [],
                    "quality_score": 0.0,
                    "subscores": {"decision_correctness": 0.0},
                    "raw_output_path": str(raw_path),
                    "parsed_output_path": None,
                    "scenario_group": "router_remember",
                    "notes": ["wrong_intent_for_explicit_command"],
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="impossible semantic/provider transitions"):
        run_rescore(
            registry_path=REGISTRY_PATH,
            source_path=output,
            output_path=output,
            overwrite=True,
            bootstrap_samples=0,
        )


def test_live_provider_client_retries_transient_provider_error(monkeypatch) -> None:
    settings = Settings(openai_api_key="test-key", openai_auth_mode="api_key")
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
    assert result.attempt_count == 3
    assert result.retry_count == 2
