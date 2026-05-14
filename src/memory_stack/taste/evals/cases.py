from __future__ import annotations

from typing import Any


REQUIRED_TASTE_EVAL_AREAS: tuple[str, ...] = (
    "taste_domain_routing",
    "taste_entity_classification",
    "enrichment_normalization",
    "strict_schema_validation",
    "option_matching",
    "ranking_quality",
    "negative_signal_handling",
    "decision_feedback",
    "brain_entity_projection",
    "brain_memory_projection",
    "relationship_creation",
    "open_loop_creation",
    "open_loop_closure",
    "generic_recall_taste_evidence",
    "detailed_ranking_explainability",
    "failed_enrichment_safety",
    "large_source_ingestion_selectivity",
)


DEFAULT_TASTE_EVAL_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "taste_route_recommended_wine",
        "area": "taste_domain_routing",
        "input": "Sam recommended Chateau Musar 2016.",
        "expected": {"domain": "taste", "intent": "remember", "category": "wine"},
    },
    {
        "id": "taste_classify_watched_series",
        "area": "taste_entity_classification",
        "input": "I watched The Bear and rate it 8/10.",
        "expected": {"category": "series", "item": "The Bear"},
    },
    {
        "id": "taste_enrichment_omdb_split",
        "area": "enrichment_normalization",
        "input": "Describe Coherence using allowed media enrichment.",
        "expected": {"normalized_metadata": True, "enrichment_metadata": True},
    },
    {
        "id": "taste_schema_reject_unknown_attr",
        "area": "strict_schema_validation",
        "input": "Wine with oak=0.8 and quiet=0.4.",
        "expected": {"stored_attributes": ["oak"], "warnings": ["quiet"]},
    },
    {
        "id": "taste_options_constrained",
        "area": "option_matching",
        "input": "Options: Known Wine, Mystery Bottle. Stored: Other Saved Wine.",
        "expected": {"rank_only_supplied": True, "unmatched": ["Mystery Bottle"]},
    },
    {
        "id": "taste_rank_wine_context",
        "area": "ranking_quality",
        "input": "Which wine should I bring for dinner?",
        "expected": {"uses_rating": True, "uses_attributes": True},
    },
    {
        "id": "taste_negative_avoid_filter",
        "area": "negative_signal_handling",
        "input": "Avoid Wine A. Disliked Wine B.",
        "expected": {"avoid_filter": True, "disliked_penalty": True},
    },
    {
        "id": "taste_decision_feedback_rejected",
        "area": "decision_feedback",
        "input": "Chosen Beta after Alpha and Gamma were ranked.",
        "expected": {"chosen_boost": "Beta", "rejected_penalty": ["Alpha", "Gamma"]},
    },
    {
        "id": "taste_projection_entity_required",
        "area": "brain_entity_projection",
        "input": "I want to try Noble Rot.",
        "expected": {"brain_entity_required": True},
    },
    {
        "id": "taste_projection_memory_required",
        "area": "brain_memory_projection",
        "input": "I rated The Bear 8/10.",
        "expected": {"evidence_memory_required": True},
    },
    {
        "id": "taste_relationship_recommended_by",
        "area": "relationship_creation",
        "input": "Sam recommended Chateau Musar 2016.",
        "expected": {"relationship": "Sam recommended Chateau Musar 2016"},
    },
    {
        "id": "taste_open_loop_wanted",
        "area": "open_loop_creation",
        "input": "I want to try Noble Rot.",
        "expected": {"open_loop": "Try Noble Rot."},
    },
    {
        "id": "taste_open_loop_completion_threshold",
        "area": "open_loop_closure",
        "input": "I tried Noble Rot after wanting to try Noble Rot.",
        "expected": {"close_only_high_confidence": True},
    },
    {
        "id": "taste_recall_linked_evidence",
        "area": "generic_recall_taste_evidence",
        "input": "What wines did Sam recommend?",
        "expected": {"include_taste_linked_memory": True},
    },
    {
        "id": "taste_explain_detailed_score",
        "area": "detailed_ranking_explainability",
        "input": "Explain the wine ranking score in detail.",
        "expected": {"weights": True, "penalties": True, "evidence_ids": True},
    },
    {
        "id": "taste_failed_enrichment_confirmation",
        "area": "failed_enrichment_safety",
        "input": "I want to try Nobble Rot.",
        "expected": {"requires_confirmation": True, "no_prompt_only_enriched_write": True},
    },
    {
        "id": "taste_large_source_no_mass_enrich",
        "area": "large_source_ingestion_selectivity",
        "input": "A source containing more than ten restaurant names.",
        "expected": {"mass_enrichment_skipped": True, "selection_required": True},
    },
)


def coverage_report(
    cases: tuple[dict[str, Any], ...] = DEFAULT_TASTE_EVAL_CASES,
) -> dict[str, Any]:
    covered = {str(case.get("area")) for case in cases}
    required = set(REQUIRED_TASTE_EVAL_AREAS)
    missing = sorted(required - covered)
    return {
        "required_count": len(required),
        "case_count": len(cases),
        "covered": sorted(covered & required),
        "missing": missing,
        "complete": not missing,
    }
