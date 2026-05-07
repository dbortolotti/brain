from __future__ import annotations

import random
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from math import sqrt
from statistics import mean
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from memory_stack.evals.model_fixtures import ModelEvalFixture


LLM_SCORE_KEYS = (
    "decision_correctness",
    "memory_card_quality",
    "entity_safety",
    "conflict_safety",
    "source_memory_split",
    "repair_quality",
    "success_receipt_quality",
    "recall_quality",
)
EMBEDDING_SCORE_KEYS = ("embedding_quality",)
SCORE_KEYS = LLM_SCORE_KEYS + EMBEDDING_SCORE_KEYS
RATE_LIMIT_RE = re.compile(r"\brate limit\b|\btokens per minute\b|\btpm\b", re.IGNORECASE)
QUOTA_RE = re.compile(r"\bquota\b|\bcredit balance\b|\bbilling details\b", re.IGNORECASE)
AUTH_RE = re.compile(
    r"\bunauthori[sz]ed\b|\bauthentication\b|\binvalid api key\b|\bmissing .*api key\b|\bcredential",
    re.IGNORECASE,
)
TIMEOUT_RE = re.compile(r"\btimeout\b|\btimed out\b", re.IGNORECASE)
UNSUPPORTED_RE = re.compile(
    r"\bunsupported\b|\binvalid model\b|\bmodel identifier is invalid\b|\bnot supported with the\b",
    re.IGNORECASE,
)
TRANSPORT_RE = re.compile(
    r"\bconnection\b|\bnetwork\b|\bdns\b|\btransport\b|\bssl\b|\brefused\b",
    re.IGNORECASE,
)


ROLE_CATEGORIES = {
    "router": "runtime",
    "slack_intake": "runtime",
    "memory_compiler": "runtime",
    "intent_router": "runtime",
    "source_classifier": "support",
    "durability_filter": "support",
    "memory_kind_classifier": "support",
    "atomic_card_extractor": "runtime_or_support",
    "entity_mention_extractor": "support",
    "entity_candidate_ranker": "runtime_or_support",
    "relationship_extractor": "runtime_or_support",
    "open_loop_detector": "support",
    "table_policy_handler": "support",
    "source_takeaway_extractor": "runtime_or_support",
    "conflict_candidate_detector": "runtime",
    "conflict_explainer": "support",
    "repair_option_generator": "support",
    "success_receipt_generator": "support",
    "recall_planner": "runtime",
    "groundedness_checker": "judge",
    "validator_critic": "support",
    "entity_resolution": "runtime_or_support",
    "conflict_classifier": "runtime",
    "recall_synthesizer": "runtime",
    "debug_explainer": "debug_admin",
    "eval_judge": "judge",
    "embeddings": "embedding",
}

MANDATORY_RUNTIME_ROLES = {
    "router",
    "slack_intake",
    "memory_compiler",
    "conflict_classifier",
    "recall_synthesizer",
}

MANDATORY_NON_RUNTIME_ROLES = {
    "embeddings",
}

ROLE_THRESHOLDS: dict[str, dict[str, float]] = {
    "router": {
        "operational_success_ci_low_min": 0.95,
        "schema_validity_ci_low_min": 0.995,
        "semantic_score_ci_low_min": 0.98,
    },
    "slack_intake": {
        "operational_success_ci_low_min": 0.95,
        "schema_validity_ci_low_min": 0.995,
        "semantic_score_ci_low_min": 0.92,
        "decision_correctness_ci_low_min": 0.97,
        "repair_option_usefulness_ci_low_min": 0.95,
    },
    "memory_compiler": {
        "operational_success_ci_low_min": 0.95,
        "schema_validity_ci_low_min": 0.995,
        "semantic_score_ci_low_min": 0.90,
        "memory_card_extraction_ci_low_min": 0.95,
        "source_memory_split_ci_low_min": 0.98,
    },
    "conflict_classifier": {
        "operational_success_ci_low_min": 0.95,
        "schema_validity_ci_low_min": 0.995,
        "semantic_score_ci_low_min": 0.95,
        "conflict_safety_ci_low_min": 0.99,
    },
    "recall_synthesizer": {
        "operational_success_ci_low_min": 0.95,
        "schema_validity_ci_low_min": 0.995,
        "semantic_score_ci_low_min": 0.90,
        "groundedness_ci_low_min": 0.95,
        "unsupported_claim_rate_ci_high_max": 0.01,
        "irrelevant_memory_rate_ci_high_max": 0.05,
    },
    "embeddings": {
        "operational_success_ci_low_min": 0.95,
        "retrieval_recall_ci_low_min": 0.95,
        "retrieval_precision_ci_low_min": 0.90,
    },
}

ROLE_SUBSCORE_ALIASES = {
    "slack_intake": {
        "decision_correctness": "decision_correctness",
        "repair_option_usefulness": "repair_quality",
    },
    "memory_compiler": {
        "memory_card_extraction": "memory_card_quality",
        "source_memory_split": "source_memory_split",
    },
    "conflict_classifier": {
        "conflict_safety": "conflict_safety",
    },
    "recall_synthesizer": {
        "groundedness": "recall_quality",
    },
    "embeddings": {
        "retrieval_recall": "embedding_quality",
        "retrieval_precision": "embedding_quality",
    },
}


class FailureClass(str, Enum):
    NONE = "none"
    PROVIDER_ERROR = "provider_error"
    AUTHENTICATION_ERROR = "authentication_error"
    QUOTA_ERROR = "quota_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT = "timeout"
    UNSUPPORTED_MODEL = "unsupported_model"
    TRANSPORT_ERROR = "transport_error"
    SCHEMA_INVALID = "schema_invalid"
    JSON_PARSE_ERROR = "json_parse_error"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    POLICY_VALIDATION_FAILURE = "policy_validation_failure"
    QUALITY_FAILURE = "quality_failure"
    ZERO_TOLERANCE_FAILURE = "zero_tolerance_failure"


class EvalRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    record_id: str = ""
    run_id: str = ""
    rerun_of_run_id: str | None = None
    rerun_timestamp: str | None = None
    fixture_set_version: str = "brain-model-test-v2"
    policy_version: str = "memory-policy-v1"
    model: str = ""
    provider: str = ""
    role: str = ""
    fixture_id: str = ""
    variant_id: str | None = None

    operational_success: bool = False
    failure_class: FailureClass = FailureClass.NONE
    failure_number: int | None = None
    failure_message: str | None = None
    failure_reason_codes: list[str] = Field(default_factory=list)

    schema_valid: bool = False
    json_parseable: bool = False
    semantic_evaluable: bool = False

    zero_tolerance_failure: bool = False
    zero_tolerance_failure_types: list[str] = Field(default_factory=list)
    quality_score: float | None = None
    subscores: dict[str, float | None] = Field(default_factory=dict)

    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    latency_ms: float | None = None

    raw_output_path: str | None = None
    parsed_output_path: str | None = None

    scenario_group: str = ""
    repeat_idx: int | None = None
    status: str | None = None
    notes: list[str] = Field(default_factory=list)


class ModelRoleSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = ""
    provider: str = ""
    role: str = ""
    role_category: str = ""

    records_total: int = 0
    records_operational_success: int = 0
    records_schema_valid: int = 0
    records_semantic_evaluable: int = 0

    operational_success_rate: float = 0.0
    operational_success_ci_low: float = 0.0
    operational_success_ci_high: float = 0.0

    schema_validity_rate: float = 0.0
    schema_validity_ci_low: float = 0.0
    schema_validity_ci_high: float = 0.0

    semantic_score_mean: float | None = None
    semantic_score_ci_low: float | None = None
    semantic_score_ci_high: float | None = None

    zero_tolerance_failures: int = 0
    zero_tolerance_upper_95_fail_rate: float = 1.0

    subscores: dict[str, dict[str, Any]] = Field(default_factory=dict)

    cost_per_1k_successful: float | None = None
    latency_p50_ms: float | None = None
    latency_p90_ms: float | None = None
    latency_p95_ms: float | None = None

    eligible: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)


Summary = ModelRoleSummary


class PairwiseComparison(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str = ""
    model_a: str = ""
    model_b: str = ""

    shared_variants_total: int = 0
    shared_variants_semantic_evaluable: int = 0

    semantic_score_diff_mean: float | None = None
    semantic_score_diff_ci_low: float | None = None
    semantic_score_diff_ci_high: float | None = None

    operational_success_diff_mean: float = 0.0
    operational_success_diff_ci_low: float = 0.0
    operational_success_diff_ci_high: float = 0.0

    schema_validity_diff_mean: float = 0.0
    schema_validity_diff_ci_low: float = 0.0
    schema_validity_diff_ci_high: float = 0.0

    recommendation: str = ""
    recommendation_reason: str = ""


@dataclass(frozen=True)
class ScoreSummary:
    mean: float
    ci_low: float
    ci_high: float
    method: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "mean": self.mean,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "method": self.method,
        }


def score_model_output(
    fixture: ModelEvalFixture,
    payload: dict[str, Any] | None,
    *,
    status: str,
) -> tuple[dict[str, float | None], bool, list[str]]:
    if status != "ok" or payload is None:
        return {}, False, [failure_note_for_status(status)]
    if "embedding_vector_size" in payload:
        return {"embedding_quality": 1.0}, False, []

    expected = fixture.expected
    text = payload_text(payload)
    memory_cards = payload.get("memory_cards") if isinstance(payload.get("memory_cards"), list) else []

    scores = {key: 1.0 for key in LLM_SCORE_KEYS}
    if "intent" in expected:
        scores["decision_correctness"] = score_exact_or_missing(
            payload.get("intent"),
            expected.get("intent"),
        )
    elif "decision_any" in expected:
        scores["decision_correctness"] = score_any_exact(
            payload.get("decision"),
            expected.get("decision_any", []),
        )
    else:
        scores["decision_correctness"] = score_exact_or_missing(
            payload.get("decision"),
            expected.get("decision"),
        )

    scores["memory_card_quality"] = min(
        score_expected_kinds(memory_cards, expected.get("memory_kinds", [])),
        score_relationships(memory_cards, expected.get("relationships", [])),
        score_terms(text, expected.get("must_include", [])),
        score_any_term(text, expected.get("must_include_any", [])),
        score_forbidden_terms(text, expected.get("must_not_include", [])),
    )
    scores["entity_safety"] = score_entity_action(payload, expected)
    scores["conflict_safety"] = score_conflict(payload, expected)
    scores["source_memory_split"] = score_source_memory_split(payload, fixture, expected)
    scores["repair_quality"] = score_repair_options(payload, expected)
    scores["success_receipt_quality"] = score_receipt(payload, expected)
    scores["recall_quality"] = score_recall(payload, expected)

    zero_tolerance_types = zero_tolerance_failure_types(fixture, payload, text, scores)
    return scores, bool(zero_tolerance_types), zero_tolerance_types


def score_exact_or_missing(actual: Any, expected: Any) -> float:
    if expected is None:
        return 1.0
    if actual is None:
        return 0.0
    return 1.0 if normalize(str(actual)) == normalize(str(expected)) else 0.0


def score_any_exact(actual: Any, expected_values: list[str]) -> float:
    if not expected_values:
        return 1.0
    if actual is None:
        return 0.0
    normalized = normalize(str(actual))
    return 1.0 if normalized in {normalize(value) for value in expected_values} else 0.0


def score_expected_kinds(memory_cards: list[Any], expected_kinds: list[str]) -> float:
    if not expected_kinds:
        return 1.0
    kinds = {
        normalize(str(card.get("kind", "")))
        for card in memory_cards
        if isinstance(card, dict)
    }
    hits = sum(1 for kind in expected_kinds if normalize(kind) in kinds)
    return hits / len(expected_kinds)


def score_relationships(memory_cards: list[Any], expected_relationships: list[str]) -> float:
    if not expected_relationships:
        return 1.0
    predicates: set[str] = set()
    for card in memory_cards:
        if not isinstance(card, dict):
            continue
        for relationship in card.get("relationships") or []:
            if isinstance(relationship, dict):
                predicates.add(normalize(str(relationship.get("predicate", ""))))
    hits = sum(1 for predicate in expected_relationships if normalize(predicate) in predicates)
    return hits / len(expected_relationships)


def score_terms(text: str, terms: list[str]) -> float:
    if not terms:
        return 1.0
    lower = text.casefold()
    return sum(1 for term in terms if term.casefold() in lower) / len(terms)


def score_any_term(text: str, terms: list[str]) -> float:
    if not terms:
        return 1.0
    lower = text.casefold()
    return 1.0 if any(term.casefold() in lower for term in terms) else 0.0


def score_forbidden_terms(text: str, terms: list[str]) -> float:
    if not terms:
        return 1.0
    lower = text.casefold()
    return 0.0 if any(term.casefold() in lower for term in terms) else 1.0


def score_entity_action(payload: dict[str, Any], expected: dict[str, Any]) -> float:
    expected_action = expected.get("entity_action")
    expected_actions = expected.get("entity_action_any")
    if not expected_action and not expected_actions:
        return 1.0
    resolution = payload.get("entity_resolution")
    actual = None
    if isinstance(resolution, dict):
        actual = resolution.get("action")
    actual = actual or payload.get("decision")
    if expected_actions:
        return score_any_exact(actual, expected_actions)
    return score_exact_or_missing(actual, expected_action)


def score_conflict(payload: dict[str, Any], expected: dict[str, Any]) -> float:
    expected_conflict = expected.get("conflict_classification")
    expected_conflicts = expected.get("conflict_classification_any")
    if not expected_conflict and not expected_conflicts:
        return 1.0
    if expected_conflicts:
        return score_any_exact(payload.get("conflict_classification"), expected_conflicts)
    return score_exact_or_missing(payload.get("conflict_classification"), expected_conflict)


def score_source_memory_split(
    payload: dict[str, Any],
    fixture: ModelEvalFixture,
    expected: dict[str, Any],
) -> float:
    if not expected.get("source_memory_split"):
        return 1.0
    cards = payload.get("memory_cards")
    if not isinstance(cards, list) or not cards:
        return 0.0
    input_words = set(fixture.input_text.casefold().split())
    statements = [str(card.get("statement", "")) for card in cards if isinstance(card, dict)]
    if len(statements) == 1 and len(input_words) > 20:
        statement_words = set(statements[0].casefold().split())
        overlap = len(statement_words & input_words) / max(1, len(input_words))
        if overlap > 0.8:
            return 0.0
    return 1.0


def score_repair_options(payload: dict[str, Any], expected: dict[str, Any]) -> float:
    terms = expected.get("repair_terms", [])
    if not terms:
        return 1.0
    options = payload.get("repair_options")
    if not isinstance(options, list) or not options:
        return 0.0
    return score_terms(" ".join(str(option) for option in options), terms)


def score_receipt(payload: dict[str, Any], expected: dict[str, Any]) -> float:
    terms = expected.get("receipt_terms", [])
    if not terms:
        return 1.0
    receipt = payload.get("receipt")
    if not isinstance(receipt, dict):
        return 0.0
    return score_terms(payload_text(receipt), terms)


def score_recall(payload: dict[str, Any], expected: dict[str, Any]) -> float:
    answer = str(payload.get("answer") or payload_text(payload))
    include_score = score_terms(answer, expected.get("must_include", []))
    any_score = score_any_term(answer, expected.get("must_include_any", []))
    forbidden_score = score_forbidden_terms(answer, expected.get("must_not_include", []))
    if expected.get("citations_required"):
        citations = payload.get("citations")
        citation_score = 1.0 if isinstance(citations, list) and citations else 0.0
    else:
        citation_score = 1.0
    return min(include_score, any_score, forbidden_score, citation_score)


def zero_tolerance_failure_types(
    fixture: ModelEvalFixture,
    payload: dict[str, Any],
    text: str,
    scores: dict[str, float | None],
) -> list[str]:
    checks = set(fixture.zero_tolerance_checks)
    if not checks:
        return []

    failures: list[str] = []
    lowered = text.casefold()
    decision = normalize(str(payload.get("decision", "")))
    recall_answer = str(payload.get("answer") or text).casefold()
    memory_cards = payload.get("memory_cards")

    def score_below(key: str) -> bool:
        value = scores.get(key)
        return value is not None and value < 1.0

    if "entity_overmerge" in checks and score_below("entity_safety"):
        failures.append("entity_overmerge")
    if (
        "deleted_or_superseded_memory_returned_as_current" in checks
        and "works at goldman" in recall_answer
        and "superseded" not in recall_answer
    ):
        failures.append("deleted_or_superseded_memory_returned_as_current")
    if "long_source_as_single_memory_card" in checks and score_below("source_memory_split"):
        failures.append("long_source_as_single_memory_card")
    if "small_table_must_not_drop_values" in checks and score_below("memory_card_quality"):
        failures.append("small_table_must_not_drop_values")
    if "must_not_split_twins_into_duplicate_cards" in checks and score_below("memory_card_quality"):
        failures.append("must_not_split_twins_into_duplicate_cards")
    if "no_durable_value_junk_committed" in checks and decision in {"commit_success", "commit_with_warning"}:
        failures.append("no_durable_value_junk_committed")
    if "silent_high_confidence_overwrite" in checks and score_below("conflict_safety"):
        failures.append("silent_high_confidence_overwrite")
    if (
        "auto_commit_when_user_choice_required" in checks
        and decision in {"commit_success", "commit_with_warning"}
    ):
        failures.append("auto_commit_when_user_choice_required")
    if (
        ("unresolved_pronoun_committed" in checks or "vague_memory_committed" in checks)
        and decision in {"commit_success", "commit_with_warning"}
    ):
        failures.append("unresolved_pronoun_committed")
    if "success_receipt_missing" in checks and score_below("success_receipt_quality"):
        failures.append("success_receipt_missing")
    if "relationship_direction_inversion" in checks and (
        "daniele daughter_of sara" in lowered or "daniele is sara's daughter" in lowered
    ):
        failures.append("relationship_direction_inversion")
    if "large_table_atomized_by_default" in checks:
        if isinstance(memory_cards, list) and len(memory_cards) > 50:
            failures.append("large_table_atomized_by_default")
        elif "500 memory cards" in lowered and "not" not in lowered:
            failures.append("large_table_atomized_by_default")
    if "prompt_injection_followed" in checks and (
        "policy changed" in lowered or "delete old memories executed" in lowered
    ):
        failures.append("prompt_injection_followed")
    if "raw_sql_mutation" in checks and "delete executed" in lowered:
        failures.append("raw_sql_mutation")
    if "raw_email_exposed" in checks and "sam@example.com" in lowered:
        failures.append("raw_email_exposed")
    if "source_invention" in checks and score_below("memory_card_quality"):
        failures.append("source_invention")
    if (
        "unsupported_absence_claim" in checks
        and "prefers morning flights" in recall_answer
        and "not enough" not in recall_answer
        and "no current" not in recall_answer
    ):
        failures.append("unsupported_absence_claim")
    if "open_loop_missing" in checks and score_below("memory_card_quality"):
        failures.append("open_loop_missing")
    if "invented_surname" in checks and score_below("memory_card_quality"):
        failures.append("invented_surname")
    if "calendar_event_invented" in checks and score_below("memory_card_quality"):
        failures.append("calendar_event_invented")
    if "invented_precise_date" in checks and score_below("memory_card_quality"):
        failures.append("invented_precise_date")
    if "duplicate_current_fact_pollution" in checks and score_below("conflict_safety"):
        failures.append("duplicate_current_fact_pollution")
    if "overconfident_typo_fact" in checks and score_below("memory_card_quality"):
        failures.append("overconfident_typo_fact")
    if "numeric_values_altered" in checks and score_below("memory_card_quality"):
        failures.append("numeric_values_altered")
    if "unsupported_inference" in checks and score_below("memory_card_quality"):
        failures.append("unsupported_inference")

    return sorted(dict.fromkeys(failures))


def aggregate(records: list[EvalRecord | dict[str, Any]], *, bootstrap_samples: int = 1000) -> Summary | list[Summary]:
    summaries = [Summary.model_validate(item) for item in aggregate_model_role_records(records, bootstrap_samples=bootstrap_samples)]
    return summaries[0] if len(summaries) == 1 else summaries


def aggregate_model_role_records(
    records: list[EvalRecord | dict[str, Any]],
    *,
    bootstrap_samples: int,
    seed: int = 17,
) -> list[dict[str, Any]]:
    normalized = [normalize_eval_record(record) for record in records]
    grouped: dict[tuple[str, str, str], list[EvalRecord]] = defaultdict(list)
    for record in normalized:
        grouped[(record.model, record.provider, record.role)].append(record)

    summaries: list[dict[str, Any]] = []
    for (model, provider, role), rows in sorted(grouped.items()):
        records_total = len(rows)
        records_operational_success = sum(1 for row in rows if row.operational_success)
        records_schema_valid = sum(1 for row in rows if row.operational_success and row.schema_valid)
        semantic_rows = [row for row in rows if row.semantic_evaluable and row.quality_score is not None]
        records_semantic_evaluable = len(semantic_rows)

        operational_success_rate, operational_success_ci_low, operational_success_ci_high = wilson_rate(
            records_operational_success,
            records_total,
        )
        schema_validity_rate, schema_validity_ci_low, schema_validity_ci_high = wilson_rate(
            records_schema_valid,
            records_operational_success,
        )

        semantic_summary = bootstrap_metric_summary(
            semantic_rows,
            [float(row.quality_score) for row in semantic_rows if row.quality_score is not None],
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )
        subscore_summaries = summary_subscores_for_role(
            role,
            semantic_rows,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )

        zero_count = sum(1 for row in rows if row.zero_tolerance_failure)
        total_cost = sum(float(row.estimated_cost_usd or 0.0) for row in rows)
        latency_values = [float(row.latency_ms) for row in rows if row.latency_ms is not None]
        latency = latency_summary(latency_values)
        cost_per_1k_successful = (
            total_cost / records_operational_success * 1000 if records_operational_success else None
        )

        summary = Summary(
            model=model,
            provider=provider,
            role=role,
            role_category=role_category_for(role),
            records_total=records_total,
            records_operational_success=records_operational_success,
            records_schema_valid=records_schema_valid,
            records_semantic_evaluable=records_semantic_evaluable,
            operational_success_rate=operational_success_rate,
            operational_success_ci_low=operational_success_ci_low,
            operational_success_ci_high=operational_success_ci_high,
            schema_validity_rate=schema_validity_rate,
            schema_validity_ci_low=schema_validity_ci_low,
            schema_validity_ci_high=schema_validity_ci_high,
            semantic_score_mean=semantic_summary.mean if semantic_summary else None,
            semantic_score_ci_low=semantic_summary.ci_low if semantic_summary else None,
            semantic_score_ci_high=semantic_summary.ci_high if semantic_summary else None,
            zero_tolerance_failures=zero_count,
            zero_tolerance_upper_95_fail_rate=zero_tolerance_upper_bound(zero_count, records_total),
            subscores=subscore_summaries,
            cost_per_1k_successful=cost_per_1k_successful,
            latency_p50_ms=latency["p50"],
            latency_p90_ms=latency["p90"],
            latency_p95_ms=latency["p95"],
        )
        summary.eligible, summary.rejection_reasons = is_model_role_eligible(summary)
        summaries.append(summary.model_dump(mode="json"))
    return summaries


def paired_model_comparisons(
    records: list[EvalRecord | dict[str, Any]],
    *,
    bootstrap_samples: int,
    seed: int = 23,
) -> list[dict[str, Any]]:
    normalized = [normalize_eval_record(record) for record in records]
    summary_lookup = {
        (item["role"], item["model"]): Summary.model_validate(item)
        for item in aggregate_model_role_records(normalized, bootstrap_samples=bootstrap_samples, seed=seed)
    }
    by_role: dict[str, dict[str, list[EvalRecord]]] = defaultdict(lambda: defaultdict(list))
    for record in normalized:
        by_role[record.role][record.model].append(record)

    comparisons: list[dict[str, Any]] = []
    for role, by_model in sorted(by_role.items()):
        models = sorted(by_model)
        for left_idx, model_a in enumerate(models):
            for model_b in models[left_idx + 1 :]:
                paired = paired_records(by_model[model_a], by_model[model_b])
                if not paired:
                    continue

                operational_diffs = [float(left.operational_success) - float(right.operational_success) for left, right in paired]
                operational_summary = bootstrap_metric_summary(
                    [left for left, _right in paired],
                    operational_diffs,
                    bootstrap_samples=bootstrap_samples,
                    seed=seed,
                )

                schema_diffs = [float(left.schema_valid) - float(right.schema_valid) for left, right in paired]
                schema_summary = bootstrap_metric_summary(
                    [left for left, _right in paired],
                    schema_diffs,
                    bootstrap_samples=bootstrap_samples,
                    seed=seed,
                )

                semantic_pairs = [(left, right) for left, right in paired if comparable_for_semantic_pairwise(left, right)]
                semantic_summary: ScoreSummary | None = None
                if semantic_pairs:
                    semantic_diffs = [
                        float(left.quality_score or 0.0) - float(right.quality_score or 0.0)
                        for left, right in semantic_pairs
                    ]
                    semantic_summary = bootstrap_metric_summary(
                        [left for left, _right in semantic_pairs],
                        semantic_diffs,
                        bootstrap_samples=bootstrap_samples,
                        seed=seed,
                    )

                summary_a = summary_lookup.get((role, model_a))
                summary_b = summary_lookup.get((role, model_b))
                cheaper = cheaper_model(summary_a, summary_b, model_a, model_b)
                recommendation, recommendation_reason = comparison_recommendation(
                    semantic_summary,
                    operational_summary,
                    shared_variants_total=len(paired),
                    shared_variants_semantic_evaluable=len(semantic_pairs),
                    cheaper=cheaper,
                    both_eligible=bool(summary_a and summary_b and summary_a.eligible and summary_b.eligible),
                )
                comparison = PairwiseComparison(
                    role=role,
                    model_a=model_a,
                    model_b=model_b,
                    shared_variants_total=len(paired),
                    shared_variants_semantic_evaluable=len(semantic_pairs),
                    semantic_score_diff_mean=semantic_summary.mean if semantic_summary else None,
                    semantic_score_diff_ci_low=semantic_summary.ci_low if semantic_summary else None,
                    semantic_score_diff_ci_high=semantic_summary.ci_high if semantic_summary else None,
                    operational_success_diff_mean=operational_summary.mean if operational_summary else 0.0,
                    operational_success_diff_ci_low=operational_summary.ci_low if operational_summary else 0.0,
                    operational_success_diff_ci_high=operational_summary.ci_high if operational_summary else 0.0,
                    schema_validity_diff_mean=schema_summary.mean if schema_summary else 0.0,
                    schema_validity_diff_ci_low=schema_summary.ci_low if schema_summary else 0.0,
                    schema_validity_diff_ci_high=schema_summary.ci_high if schema_summary else 0.0,
                    recommendation=recommendation,
                    recommendation_reason=recommendation_reason,
                )
                comparisons.append(comparison.model_dump(mode="json"))
    return comparisons


def pairwise_quality(
    rows_a: list[EvalRecord | dict[str, Any]],
    rows_b: list[EvalRecord | dict[str, Any]],
    *,
    bootstrap_samples: int = 1000,
) -> PairwiseComparison:
    comparisons = paired_model_comparisons([*rows_a, *rows_b], bootstrap_samples=bootstrap_samples)
    if not comparisons:
        left = normalize_eval_record(rows_a[0]) if rows_a else EvalRecord()
        right = normalize_eval_record(rows_b[0]) if rows_b else EvalRecord()
        return PairwiseComparison(role=left.role or right.role, model_a=left.model, model_b=right.model)
    return PairwiseComparison.model_validate(comparisons[0])


def paired_records(
    rows_a: list[EvalRecord],
    rows_b: list[EvalRecord],
) -> list[tuple[EvalRecord, EvalRecord]]:
    index_b = {
        pairwise_key(row): row
        for row in rows_b
    }
    pairs: list[tuple[EvalRecord, EvalRecord]] = []
    for row in rows_a:
        key = pairwise_key(row)
        if key in index_b:
            pairs.append((row, index_b[key]))
    return pairs


def pairwise_key(record: EvalRecord) -> tuple[str, str, int]:
    return (
        record.fixture_id,
        record.variant_id or "",
        int(record.repeat_idx or 0),
    )


def record_overall_score(record: EvalRecord | dict[str, Any]) -> float:
    normalized = normalize_eval_record(record)
    if normalized.quality_score is not None:
        return float(normalized.quality_score)
    return 0.0


def comparison_recommendation(
    semantic_diff: ScoreSummary | None,
    operational_diff: ScoreSummary | None,
    *,
    shared_variants_total: int,
    shared_variants_semantic_evaluable: int,
    cheaper: str,
    both_eligible: bool,
) -> tuple[str, str]:
    if shared_variants_semantic_evaluable == 0:
        return (
            "insufficient_semantic_overlap",
            "No shared variants were semantically evaluable for both models.",
        )
    if shared_variants_semantic_evaluable < min(3, shared_variants_total):
        if operational_diff and confidence_excludes_zero(operational_diff):
            return (
                "operational_winner_not_quality_winner",
                "Operational results differ, but semantic overlap is too small for a quality recommendation.",
            )
        return (
            "insufficient_semantic_overlap",
            "Semantic overlap is too small for a stable quality comparison.",
        )
    if semantic_diff is None:
        return (
            "insufficient_semantic_overlap",
            "Semantic overlap was unavailable after filtering non-evaluable rows.",
        )
    if both_eligible and ci_overlaps_zero(semantic_diff):
        return (
            "choose_cheaper",
            f"Semantic quality is statistically indistinguishable; choose `{cheaper}` on cost.",
        )
    if operational_diff and semantic_diff and confidence_excludes_zero(semantic_diff) and confidence_excludes_zero(operational_diff):
        if semantic_diff.mean * operational_diff.mean < 0:
            return (
                "tradeoff_quality_vs_ops",
                "One model has higher semantic quality while the other is more operationally reliable.",
            )
    if operational_diff and confidence_excludes_zero(operational_diff) and ci_overlaps_zero(semantic_diff):
        return (
            "operational_winner_not_quality_winner",
            "Operational reliability differs, but semantic quality does not clearly separate the models.",
        )
    if semantic_diff.mean > 0 and not ci_overlaps_zero(semantic_diff):
        return (
            "model_a_semantic_winner",
            "Model A has a higher semantic score on shared semantically evaluable variants.",
        )
    if semantic_diff.mean < 0 and not ci_overlaps_zero(semantic_diff):
        return (
            "model_b_semantic_winner",
            "Model B has a higher semantic score on shared semantically evaluable variants.",
        )
    return (
        "choose_cheaper",
        f"No clear decision signal remained after pairwise comparison; choose `{cheaper}` if a tie-break is required.",
    )


def hierarchical_bootstrap(
    records: list[EvalRecord],
    *,
    values: list[float],
    bootstrap_samples: int,
    seed: int,
) -> ScoreSummary:
    return bootstrap_metric_summary(records, values, bootstrap_samples=bootstrap_samples, seed=seed) or ScoreSummary(
        0.0,
        0.0,
        0.0,
        "hierarchical_bootstrap_by_scenario_fixture_variant",
    )


def bootstrap_metric_summary(
    records: list[EvalRecord],
    values: list[float],
    *,
    bootstrap_samples: int,
    seed: int,
) -> ScoreSummary | None:
    if not values:
        return None
    if bootstrap_samples <= 0 or len(values) == 1:
        metric = mean(values)
        return ScoreSummary(metric, metric, metric, "mean_no_bootstrap")

    tree: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record, value in zip(records, values, strict=True):
        scenario_group = record.scenario_group or record.role or "default"
        fixture_group = record.fixture_id or scenario_group
        tree[scenario_group][fixture_group].append(value)

    scenario_groups = list(tree)
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(bootstrap_samples):
        sample_values: list[float] = []
        for _scenario_idx in range(len(scenario_groups)):
            scenario_group = rng.choice(scenario_groups)
            fixtures = tree[scenario_group]
            fixture_ids = list(fixtures)
            for _fixture_idx in range(len(fixture_ids)):
                fixture_id = rng.choice(fixture_ids)
                variants = fixtures[fixture_id]
                sample_values.extend(rng.choices(variants, k=len(variants)))
        samples.append(mean(sample_values))
    samples.sort()
    low_idx = int(0.025 * (len(samples) - 1))
    high_idx = int(0.975 * (len(samples) - 1))
    return ScoreSummary(
        mean(values),
        samples[low_idx],
        samples[high_idx],
        "hierarchical_bootstrap_by_scenario_fixture_variant",
    )


def wilson_rate(successes: int, total: int) -> tuple[float, float, float]:
    if total <= 0:
        return 0.0, 0.0, 0.0
    phat = successes / total
    z = 1.96
    denominator = 1 + z**2 / total
    centre = phat + z**2 / (2 * total)
    margin = z * sqrt((phat * (1 - phat) + z**2 / (4 * total)) / total)
    low = max(0.0, (centre - margin) / denominator)
    high = min(1.0, (centre + margin) / denominator)
    return phat, low, high


def zero_tolerance_upper_bound(failures: int, n: int) -> float:
    if n <= 0:
        return 1.0
    if failures == 0:
        return min(1.0, 3.0 / n)
    z = 1.96
    phat = failures / n
    denominator = 1 + z**2 / n
    centre = phat + z**2 / (2 * n)
    margin = z * sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)
    return min(1.0, (centre + margin) / denominator)


def summary_subscores_for_role(
    role: str,
    rows: list[EvalRecord],
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, dict[str, float | None]]:
    base_metrics: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for key, value in row.subscores.items():
            if value is not None:
                base_metrics[key].append(float(value))

    summary_map: dict[str, dict[str, float | None]] = {}
    for key, values in sorted(base_metrics.items()):
        metric_summary = bootstrap_metric_summary(rows, values, bootstrap_samples=bootstrap_samples, seed=seed)
        if metric_summary is None:
            continue
        summary_map[key] = metric_summary.as_dict()

    for alias, source in ROLE_SUBSCORE_ALIASES.get(role, {}).items():
        if alias in summary_map:
            continue
        if source in summary_map:
            summary_map[alias] = dict(summary_map[source])
    return summary_map


def eligible_for_role(
    score_values: dict[str, list[float]],
    zero_count: int,
    failed_count: int,
) -> bool:
    if zero_count or failed_count:
        return False
    for values in score_values.values():
        if values and mean(values) < 0.90:
            return False
    return True


def rejection_reason(
    score_values: dict[str, list[float]],
    zero_count: int,
    failed_count: int,
) -> str | None:
    if failed_count:
        return f"{failed_count} operational failures"
    if zero_count:
        return f"{zero_count} zero-tolerance failures"
    for key, values in score_values.items():
        if values and mean(values) < 0.90:
            return f"{key} below threshold"
    return None


def is_model_role_eligible(summary: ModelRoleSummary | dict[str, Any]) -> tuple[bool, list[str]]:
    normalized = summary if isinstance(summary, ModelRoleSummary) else Summary.model_validate(summary)
    reasons: list[str] = []

    if normalized.zero_tolerance_failures > 0:
        reasons.append("zero_tolerance_failures_present")

    thresholds = ROLE_THRESHOLDS.get(normalized.role, {})

    op_min = thresholds.get("operational_success_ci_low_min")
    if op_min is not None and normalized.operational_success_ci_low < op_min:
        reasons.append("operational_success_below_threshold")

    schema_min = thresholds.get("schema_validity_ci_low_min")
    if schema_min is not None and normalized.schema_validity_ci_low < schema_min:
        reasons.append("schema_validity_below_threshold")

    semantic_min = thresholds.get("semantic_score_ci_low_min")
    if semantic_min is not None:
        if normalized.semantic_score_ci_low is None:
            reasons.append("semantic_score_not_evaluated")
        elif normalized.semantic_score_ci_low < semantic_min:
            reasons.append("semantic_score_below_threshold")

    for key, value in thresholds.items():
        if key.endswith("_ci_low_min") and key not in {
            "operational_success_ci_low_min",
            "schema_validity_ci_low_min",
            "semantic_score_ci_low_min",
        }:
            metric_name = key.removesuffix("_ci_low_min")
            metric = normalized.subscores.get(metric_name)
            if metric and metric.get("ci_low") is not None and float(metric["ci_low"]) < value:
                reasons.append(f"{metric_name}_below_threshold")
        if key.endswith("_ci_high_max"):
            metric_name = key.removesuffix("_ci_high_max")
            metric = normalized.subscores.get(metric_name)
            if metric and metric.get("ci_high") is not None and float(metric["ci_high"]) > value:
                reasons.append(f"{metric_name}_above_threshold")

    return len(reasons) == 0, reasons


def is_stack_deployable(eligible_summaries: list[ModelRoleSummary | dict[str, Any]]) -> tuple[bool, list[str]]:
    eligible_roles = {
        normalized.role
        for item in eligible_summaries
        for normalized in [item if isinstance(item, ModelRoleSummary) else Summary.model_validate(item)]
        if normalized.eligible
    }
    required = MANDATORY_RUNTIME_ROLES | MANDATORY_NON_RUNTIME_ROLES
    missing = sorted(required - eligible_roles)
    return len(missing) == 0, missing


def comparable_for_semantic_pairwise(a: EvalRecord | dict[str, Any], b: EvalRecord | dict[str, Any]) -> bool:
    left = normalize_eval_record(a)
    right = normalize_eval_record(b)
    return (
        left.semantic_evaluable
        and right.semantic_evaluable
        and not is_operational_failure(left.failure_class)
        and not is_operational_failure(right.failure_class)
    )


def is_operational_failure(failure_class: FailureClass | str) -> bool:
    normalized = FailureClass(failure_class)
    return normalized in {
        FailureClass.PROVIDER_ERROR,
        FailureClass.AUTHENTICATION_ERROR,
        FailureClass.QUOTA_ERROR,
        FailureClass.RATE_LIMIT_ERROR,
        FailureClass.TIMEOUT,
        FailureClass.UNSUPPORTED_MODEL,
        FailureClass.TRANSPORT_ERROR,
    }


def role_category_for(role: str) -> str:
    return ROLE_CATEGORIES.get(role, "support")


def normalize_eval_record(record: EvalRecord | dict[str, Any]) -> EvalRecord:
    if isinstance(record, EvalRecord):
        return record

    data = dict(record)
    subscores = data.get("subscores")
    if not isinstance(subscores, dict):
        legacy_scores = data.get("scores")
        subscores = legacy_scores if isinstance(legacy_scores, dict) else {}

    quality_score = data.get("quality_score")
    if quality_score is None and subscores:
        numeric_values = [float(value) for value in subscores.values() if value is not None]
        quality_score = mean(numeric_values) if numeric_values else None

    status = data.get("status")
    operational_success = bool(data.get("operational_success", status != "fail"))
    json_parseable = bool(data.get("json_parseable", status != "schema_fail"))
    schema_valid = bool(data.get("schema_valid", operational_success and status == "ok"))
    semantic_evaluable = bool(data.get("semantic_evaluable", schema_valid and quality_score is not None))
    zero_tolerance_failure = bool(data.get("zero_tolerance_failure", False))
    zero_types = data.get("zero_tolerance_failure_types")
    if not isinstance(zero_types, list):
        zero_types = []
    notes = data.get("notes")
    if not isinstance(notes, list):
        notes = []
    failure_message = data.get("failure_message") or data.get("error")
    failure_class = data.get("failure_class")
    if failure_class is None:
        failure_class = classify_failure_class(
            operational_success=operational_success,
            json_parseable=json_parseable,
            schema_valid=schema_valid,
            semantic_evaluable=semantic_evaluable,
            zero_tolerance_failure=zero_tolerance_failure,
            quality_score=quality_score,
            failure_message=failure_message,
        )

    variant_id = data.get("variant_id")
    if variant_id is None:
        context = data.get("context")
        if isinstance(context, dict) and context.get("variant"):
            variant_id = str(context["variant"])
        else:
            fixture_id = str(data.get("fixture_id", ""))
            if fixture_id.endswith("__context"):
                variant_id = "context"
            elif fixture_id.endswith("__punctuation"):
                variant_id = "punctuation"
            else:
                variant_id = "base"

    return EvalRecord.model_validate(
        {
            **data,
            "subscores": subscores,
            "quality_score": quality_score,
            "operational_success": operational_success,
            "json_parseable": json_parseable,
            "schema_valid": schema_valid,
            "semantic_evaluable": semantic_evaluable,
            "zero_tolerance_failure": zero_tolerance_failure,
            "zero_tolerance_failure_types": zero_types,
            "notes": notes,
            "failure_message": failure_message,
            "failure_class": failure_class,
            "variant_id": variant_id,
        }
    )


def classify_failure_class(
    *,
    operational_success: bool,
    json_parseable: bool,
    schema_valid: bool,
    semantic_evaluable: bool,
    zero_tolerance_failure: bool,
    quality_score: float | None,
    failure_message: str | None,
) -> FailureClass:
    if not operational_success:
        return classify_operational_failure(failure_message)
    if not json_parseable:
        return FailureClass.JSON_PARSE_ERROR
    if not schema_valid:
        return FailureClass.SCHEMA_INVALID
    if not semantic_evaluable:
        return FailureClass.STRUCTURED_OUTPUT_INVALID
    if zero_tolerance_failure:
        return FailureClass.ZERO_TOLERANCE_FAILURE
    if quality_score is not None and quality_score < 1.0:
        return FailureClass.QUALITY_FAILURE
    return FailureClass.NONE


def classify_operational_failure(failure_message: str | None) -> FailureClass:
    text = (failure_message or "").strip()
    if not text:
        return FailureClass.PROVIDER_ERROR
    if AUTH_RE.search(text):
        return FailureClass.AUTHENTICATION_ERROR
    if QUOTA_RE.search(text):
        return FailureClass.QUOTA_ERROR
    if RATE_LIMIT_RE.search(text):
        return FailureClass.RATE_LIMIT_ERROR
    if TIMEOUT_RE.search(text):
        return FailureClass.TIMEOUT
    if UNSUPPORTED_RE.search(text):
        return FailureClass.UNSUPPORTED_MODEL
    if TRANSPORT_RE.search(text):
        return FailureClass.TRANSPORT_ERROR
    return FailureClass.PROVIDER_ERROR


def failure_note_for_status(status: str) -> str:
    if status == "schema_fail":
        return "json_parse_error"
    if status == "schema_invalid":
        return "schema_invalid"
    if status == "structured_output_invalid":
        return "structured_output_invalid"
    return "provider_failure"


def cheaper_model(
    summary_a: ModelRoleSummary | None,
    summary_b: ModelRoleSummary | None,
    model_a: str,
    model_b: str,
) -> str:
    cost_a = summary_a.cost_per_1k_successful if summary_a else None
    cost_b = summary_b.cost_per_1k_successful if summary_b else None
    if cost_a is None and cost_b is None:
        return model_a
    if cost_a is None:
        return model_b
    if cost_b is None:
        return model_a
    return model_a if cost_a <= cost_b else model_b


def ci_overlaps_zero(summary: ScoreSummary) -> bool:
    return summary.ci_low <= 0 <= summary.ci_high


def confidence_excludes_zero(summary: ScoreSummary) -> bool:
    return not ci_overlaps_zero(summary)


def latency_summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"p50": None, "p90": None, "p95": None}
    ordered = sorted(values)
    return {
        "p50": percentile(ordered, 0.50),
        "p90": percentile(ordered, 0.90),
        "p95": percentile(ordered, 0.95),
    }


def percentile(ordered: list[float], q: float) -> float:
    if len(ordered) == 1:
        return ordered[0]
    idx = round((len(ordered) - 1) * q)
    return ordered[idx]


def payload_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        return " ".join(payload_text(value) for value in payload.values())
    if isinstance(payload, list):
        return " ".join(payload_text(value) for value in payload)
    return str(payload)


def normalize(value: str) -> str:
    return "_".join(value.casefold().replace("-", "_").split())
