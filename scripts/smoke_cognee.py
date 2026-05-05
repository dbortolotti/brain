#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cognee_adapter import recall_text, remember_text
from memory_stack.config import load_settings
from memory_stack.io import load_memory_items
from memory_stack.scoring import result_to_text


console = Console()
SAMPLE = "data/samples/synthetic_property_emails.jsonl"


async def run_smoke() -> int:
    settings = load_settings()
    items = load_memory_items(SAMPLE)

    try:
        for item in items:
            await remember_text(
                item.to_ingestion_text(),
                dataset_name=item.dataset_name,
                temporal=True,
                node_set=item.tags or None,
                settings=settings,
            )
        console.print("[green][PASS][/green] ingest succeeded")
    except Exception as exc:
        console.print(f"[red][FAIL][/red] ingest failed: {exc}")
        return 1

    temporal_result = await recall_text(
        query="What is our current position on whether a separate CDM Principal Designer is required?",
        dataset="property_trial",
        search_type="TEMPORAL",
        settings=settings,
    )
    temporal_text = result_to_text(temporal_result)
    temporal_checks = [
        "Asbestech" in temporal_text,
        "Principal Designer" in temporal_text,
        ("Jason" in temporal_text or "Irwin" in temporal_text),
    ]
    if all(temporal_checks):
        console.print("[green][PASS][/green] temporal recall returned Principal Designer context")
    else:
        console.print("[yellow][WARN][/yellow] temporal recall returned weak context")

    contradiction_terms = ["confirmed", "disagrees", "current"]
    if sum(term.lower() in temporal_text.lower() for term in contradiction_terms) >= 2:
        console.print("[green][PASS][/green] contradiction distinction partially present")
    else:
        console.print("[yellow][WARN][/yellow] contradiction distinction weak")

    graph_result = await recall_text(
        query="Who is involved in the Melcombe Court asbestos works and what are their roles?",
        dataset="property_trial",
        search_type="GRAPH_COMPLETION",
        settings=settings,
    )
    graph_text = result_to_text(graph_result)
    if "Asbestech" in graph_text:
        console.print("[green][PASS][/green] relation query returned Asbestech")
        return 0

    console.print("[yellow][WARN][/yellow] relation query did not clearly return Asbestech")
    return 0


def main() -> int:
    try:
        return asyncio.run(run_smoke())
    except Exception as exc:
        console.print(f"[red][FAIL][/red] smoke failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
