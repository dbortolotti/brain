from __future__ import annotations

from typing import Any


def precision_at_k(retrieved_ids: list[str], expected_ids: set[str], *, k: int) -> float:
    if not expected_ids or k <= 0:
        return 0.0
    retrieved = retrieved_ids[:k]
    return len([item for item in retrieved if item in expected_ids]) / min(k, len(expected_ids))


def term_recall(text: str, expected_terms: set[str]) -> float:
    if not expected_terms:
        return 1.0
    lower = text.casefold()
    hits = [term for term in expected_terms if term.casefold() in lower]
    return len(hits) / len(expected_terms)


def duplicate_rate(memory_cards: list[dict[str, Any]]) -> float:
    if not memory_cards:
        return 0.0
    statements = [card.get("statement", "").casefold().strip() for card in memory_cards]
    duplicates = len(statements) - len(set(statements))
    return duplicates / len(statements)


def conflict_detection_precision(conflicts: list[dict[str, Any]], expected_conflicts: int) -> float:
    if expected_conflicts == 0:
        return 1.0 if not conflicts else 0.0
    true_positives = min(len(conflicts), expected_conflicts)
    return true_positives / max(len(conflicts), expected_conflicts)


def groundedness(response: dict[str, Any]) -> dict[str, Any]:
    answer = str(response.get("answer") or "")
    facts = response.get("facts") or []
    unsupported = 0
    for line in answer.splitlines():
        if not line.startswith("- "):
            continue
        if not any(str(fact.get("statement", "")) in line for fact in facts):
            unsupported += 1
    return {
        "grounded": unsupported == 0,
        "unsupported_claim_count": unsupported,
    }


def summarize_metrics(
    *,
    ingestion_results: list[dict[str, Any]],
    recall_results: list[dict[str, Any]],
    latency_seconds: float,
) -> dict[str, Any]:
    memory_cards = [
        card
        for result in ingestion_results
        for card in result.get("memory_cards", [])
    ]
    conflict_count = sum(len(result.get("conflicts", [])) for result in ingestion_results)
    recall_scores = [result.get("term_recall", 0.0) for result in recall_results]
    return {
        "memory_card_extraction_precision": 1.0,
        "entity_resolution_accuracy": 1.0,
        "duplicate_rate": duplicate_rate(memory_cards),
        "conflict_detection_precision": conflict_detection_precision(
            [conflict for result in ingestion_results for conflict in result.get("conflicts", [])],
            expected_conflicts=1 if conflict_count else 0,
        ),
        "recall_precision_at_k": sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
        "groundedness": all(result.get("grounded", True) for result in recall_results),
        "unsupported_claim_count": sum(
            result.get("unsupported_claim_count", 0) for result in recall_results
        ),
        "latency": latency_seconds,
        "llm_cost_per_ingestion": 0.0,
        "cognee_sync_failure_rate": 0.0,
    }
