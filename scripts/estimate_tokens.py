#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.io import load_memory_items
from memory_stack.token_costs import estimate_ingest_cost


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="gemini-3.1-flash-lite-preview")
    parser.add_argument("--chunk-size", type=int, default=1024)
    parser.add_argument("--google-free-tier", default="false")
    args = parser.parse_args()

    items = load_memory_items(args.input)
    source_text = "\n\n".join(item.to_ingestion_text() for item in items)
    google_free_tier = str(args.google_free_tier).lower() in {"1", "true", "yes"}
    estimate = estimate_ingest_cost(
        source_text=source_text,
        model=args.model,
        chunk_size=args.chunk_size,
        google_free_tier=google_free_tier,
    )

    console.print(f"source_tokens: {estimate.source_tokens}")
    console.print(f"chunks: {estimate.chunks}")
    console.print(f"llm_calls: {estimate.llm_calls}")
    console.print(
        "standard_ingest_paid_estimate: "
        f"${estimate.standard_ingest_paid_estimate_low:.6f} - "
        f"${estimate.standard_ingest_paid_estimate_high:.6f}"
    )
    console.print(
        "temporal_ingest_paid_estimate: "
        f"${estimate.temporal_ingest_paid_estimate_low:.6f} - "
        f"${estimate.temporal_ingest_paid_estimate_high:.6f}"
    )
    if estimate.reported_cost_with_free_tier is not None:
        console.print(f"reported_cost_with_free_tier: ${estimate.reported_cost_with_free_tier:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

