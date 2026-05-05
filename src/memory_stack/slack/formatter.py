from __future__ import annotations

from typing import Any

from memory_stack.brain_models import IngestionReceipt, RecallResponse


def format_ingestion_receipt(receipt: IngestionReceipt) -> str:
    lines = [f"Stored {len(receipt.memory_cards)} memories."]
    for index, card in enumerate(receipt.memory_cards, start=1):
        lines.extend(["", f"{index}. {card.kind}", f"   {card.statement}"])

    if receipt.entities:
        lines.extend(["", "Entities created/updated:"])
        for entity in receipt.entities:
            lines.append(f"- {entity.canonical_name}")

    conflict_count = len(receipt.conflicts)
    lines.extend(["", "No conflicts detected." if conflict_count == 0 else f"{conflict_count} conflicts detected."])
    return "\n".join(lines)


def format_recall_response(response: RecallResponse) -> str:
    return response.answer


def format_open_loops(loops: list[dict[str, Any]]) -> str:
    if not loops:
        return "No open loops found."
    lines = ["Open loops"]
    for loop in loops:
        lines.append(f"- {loop['statement']} [{loop['memory_id']}]")
    return "\n".join(lines)


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
