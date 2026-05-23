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
    "palate_control_entity_id",
    "palate_evidence_external_id",
    "no_legacy_relationship_projection",
    "palate_open_loop_external_id",
    "no_legacy_open_loop_closure",
    "taste_query_recall_evidence",
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
        "id": "taste_control_entity_id_required",
        "area": "palate_control_entity_id",
        "input": "I want to try Noble Rot.",
        "expected": {"control_entity_id_required": True},
    },
    {
        "id": "taste_external_evidence_id_required",
        "area": "palate_evidence_external_id",
        "input": "I rated The Bear 8/10.",
        "expected": {"external_evidence_id_required": True},
    },
    {
        "id": "taste_no_legacy_relationship_projection",
        "area": "no_legacy_relationship_projection",
        "input": "Sam recommended Chateau Musar 2016.",
        "expected": {"legacy_relationship_rows_written": False},
    },
    {
        "id": "taste_open_loop_external_id",
        "area": "palate_open_loop_external_id",
        "input": "I want to try Noble Rot.",
        "expected": {"external_open_loop_id": True},
    },
    {
        "id": "taste_no_legacy_open_loop_closure",
        "area": "no_legacy_open_loop_closure",
        "input": "I tried Noble Rot after wanting to try Noble Rot.",
        "expected": {"legacy_open_loop_rows_written": False},
    },
    {
        "id": "taste_query_recall_evidence",
        "area": "taste_query_recall_evidence",
        "input": "What wines did Sam recommend?",
        "expected": {"include_ranked_taste_evidence": True},
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
