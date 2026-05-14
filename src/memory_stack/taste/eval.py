from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

from .ranking import RankingWeights, build_grounding, rank_candidates, retrieve_candidates


DEFAULT_SWEEP_GRID = {
    "preference": [1.2, 1.4, 1.6],
    "context": [0.4, 0.5, 0.7],
    "attribute_match_cap": [1.0, 1.5, 2.0],
    "attribute_uncertainty_width_penalty": [0.25, 0.5, 0.75],
    "chosen_feedback": [0.1, 0.15, 0.25],
    "rejected_feedback": [0.05, 0.1, 0.2],
}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open() as handle:
        cases = json.load(handle)
    if not isinstance(cases, list):
        raise ValueError("eval cases must be a JSON list")
    return cases


def evaluate_cases(
    store: Any,
    cases: list[dict[str, Any]],
    *,
    weights: RankingWeights | None = None,
    k: int = 3,
) -> dict[str, Any]:
    results = []
    ndcg_scores = []
    overlap_scores = []

    for case in cases:
        ranked_ids = rank_case(store, case, weights=weights)
        expected = case.get("expected_top_3") or case.get("expected") or []
        expected_ids = [str(entity_id) for entity_id in expected[:k]]
        actual_ids = ranked_ids[:k]
        ndcg = ndcg_at_k(actual_ids, expected_ids, k)
        overlap = top_k_overlap(actual_ids, expected_ids, k)
        ndcg_scores.append(ndcg)
        overlap_scores.append(overlap)
        results.append(
            {
                "name": case.get("name") or case.get("query", ""),
                "actual_top_3": actual_ids,
                "expected_top_3": expected_ids,
                "ndcg_at_3": round(ndcg, 4),
                "top_3_overlap": round(overlap, 4),
            }
        )

    return {
        "case_count": len(cases),
        "mean_ndcg_at_3": round(mean(ndcg_scores), 4),
        "mean_top_3_overlap": round(mean(overlap_scores), 4),
        "cases": results,
    }


def rank_case(
    store: Any,
    case: dict[str, Any],
    *,
    weights: RankingWeights | None = None,
) -> list[str]:
    intent = case.get("intent")
    if not isinstance(intent, dict):
        raise ValueError(f"case {case.get('name') or case.get('query')} missing intent")

    extracted_entities = [
        {"canonical_name": name, "type": intent.get("entity_type")}
        for name in case.get("options", [])
    ]
    retrieval = retrieve_candidates(store, intent, extracted_entities)
    query = str(case.get("query") or "")
    feedback = store.decision_feedback(
        query,
        [entity["id"] for entity in retrieval["candidates"]],
    )
    ranked = rank_candidates(
        retrieval["candidates"],
        intent,
        decision_feedback=feedback,
        weights=weights,
    )
    return [item["id"] for item in build_grounding(ranked)]


def ndcg_at_k(actual_ids: list[str], expected_ids: list[str], k: int = 3) -> float:
    if not expected_ids:
        return 0.0
    ideal_relevances = list(range(len(expected_ids), 0, -1))[:k]
    relevance_by_id = {
        entity_id: relevance
        for entity_id, relevance in zip(expected_ids, ideal_relevances, strict=False)
    }
    dcg = discounted_gain([relevance_by_id.get(entity_id, 0) for entity_id in actual_ids[:k]])
    idcg = discounted_gain(ideal_relevances)
    return dcg / idcg if idcg else 0.0


def discounted_gain(relevances: list[int]) -> float:
    return sum(
        ((2**relevance) - 1) / math.log2(index + 2)
        for index, relevance in enumerate(relevances)
    )


def top_k_overlap(actual_ids: list[str], expected_ids: list[str], k: int = 3) -> float:
    if not expected_ids:
        return 0.0
    return len(set(actual_ids[:k]) & set(expected_ids[:k])) / min(k, len(expected_ids))


def sweep_weights(
    store: Any,
    cases: list[dict[str, Any]],
    grid: dict[str, list[float]] | None = None,
) -> list[dict[str, Any]]:
    grid = grid or DEFAULT_SWEEP_GRID
    keys = list(grid)
    results = []
    for values in itertools.product(*(grid[key] for key in keys)):
        weights = RankingWeights.from_mapping(dict(zip(keys, values, strict=True)))
        score = evaluate_cases(store, cases, weights=weights)
        results.append(
            {
                "mean_ndcg_at_3": score["mean_ndcg_at_3"],
                "mean_top_3_overlap": score["mean_top_3_overlap"],
                "weights": dict(zip(keys, values, strict=True)),
            }
        )
    return sorted(
        results,
        key=lambda item: (item["mean_ndcg_at_3"], item["mean_top_3_overlap"]),
        reverse=True,
    )


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Brain Taste ranking quality.")
    parser.add_argument("cases", help="Path to ranking eval cases JSON.")
    parser.add_argument("--brain-db", help="Optional Brain SQLite database path.")
    parser.add_argument("--sweep", action="store_true", help="Run the default weight sweep.")
    parser.add_argument("--top", type=int, default=10, help="Number of sweep rows to print.")
    args = parser.parse_args()

    from memory_stack.cfg import Settings, load_settings
    from memory_stack.taste.store import TasteStore

    settings = load_settings()
    if args.brain_db:
        settings = Settings(**settings.model_dump(), brain_database_url=f"sqlite:///{args.brain_db}")
    store = TasteStore(settings)
    cases = load_cases(args.cases)
    if args.sweep:
        print(json.dumps(sweep_weights(store, cases)[: args.top], indent=2))
    else:
        print(json.dumps(evaluate_cases(store, cases), indent=2))


if __name__ == "__main__":
    main()
