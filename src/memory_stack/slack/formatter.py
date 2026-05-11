from __future__ import annotations

from typing import Any

from memory_stack.brain_models import IngestionReceipt, RecallResponse
from memory_stack.recall.synthesizer import render_open_loops


def format_ingestion_receipt(receipt: IngestionReceipt) -> str:
    lines = [f"Stored {len(receipt.memory_cards)} memories."]
    if receipt.source.source_id:
        lines.append(f"Source ID: {receipt.source.source_id}")
    for index, card in enumerate(receipt.memory_cards, start=1):
        lines.extend(
            [
                "",
                f"{index}. {card.kind}",
                f"   {card.statement}",
                f"   memory_id: {card.id}",
                f"   confidence: {card.confidence}",
                f"   status: {card.status}",
            ]
        )

    if receipt.entities:
        lines.extend(["", "Entities created/updated:"])
        for entity in receipt.entities:
            lines.append(f"- {entity.canonical_name} [{entity.id}; {entity.type}]")

    if receipt.relationships:
        lines.extend(["", "Relationships created/updated:"])
        for relationship in receipt.relationships:
            predicate = relationship.get("predicate", "relationship")
            subject = relationship.get("subject_entity_id", "subject")
            object_ = relationship.get("object_entity_id", "object")
            lines.append(f"- {subject} {predicate} {object_}")

    conflict_count = len(receipt.conflicts)
    lines.extend(["", "No conflicts detected." if conflict_count == 0 else f"{conflict_count} conflicts detected."])
    lines.extend(["", "Actions: Inspect | Undo | Mark wrong"])
    return "\n".join(lines)


def format_recall_response(response: RecallResponse) -> str:
    return response.answer


format_open_loops = render_open_loops


def format_review(review: dict[str, Any]) -> str:
    return (
        "Recent Brain activity\n"
        f"- ingestion runs: {len(review.get('ingestion_runs', []))}\n"
        f"- memories: {len(review.get('memory_cards', []))}\n"
        f"- sources: {len(review.get('sources', []))}\n"
        f"- conflicts: {len(review.get('conflicts', []))}"
    )


def format_undo(result: dict[str, Any]) -> str:
    return (
        f"Undo result: {result.get('status')}.\n"
        f"- memories deleted: {len(result.get('deleted_memories', []))}\n"
        f"- sources deleted: {len(result.get('deleted_sources', []))}"
    )
