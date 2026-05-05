"""Legacy direct Cognee ingestion CLI.

New ingestion should go through Brain service or MCP tools.
"""
from __future__ import annotations

import asyncio
import time

import typer
from rich.console import Console

from memory_stack.cognee_adapter import remember_text
from memory_stack.config import (
    check_embedding_dimension_change,
    load_settings,
    record_embedding_dimension,
)
from memory_stack.io import load_memory_items

app = typer.Typer(no_args_is_help=True)
console = Console()


async def ingest_items(
    input_path: str,
    temporal: bool = True,
    self_improvement: bool = False,
) -> None:
    settings = load_settings()
    ok, message = check_embedding_dimension_change(settings)
    if not ok:
        console.print(f"[red][FAIL][/red] Embedding dimension check failed: {message}")
        raise typer.Exit(1)

    items = load_memory_items(input_path)
    for idx, item in enumerate(items, start=1):
        text = item.to_ingestion_text()
        start = time.perf_counter()
        await remember_text(
            text,
            dataset_name=item.dataset_name,
            temporal=temporal,
            self_improvement=self_improvement,
            node_set=item.tags or None,
            settings=settings,
        )
        elapsed = time.perf_counter() - start
        console.print(
            f"[green]ingested[/green] {idx}/{len(items)} "
            f"{item.origin_id} dataset={item.dataset_name} "
            f"temporal={temporal} elapsed={elapsed:.2f}s"
        )

    record_embedding_dimension(settings)


@app.command()
def main(
    input_path: str = typer.Option(..., "--input"),
    temporal: bool = typer.Option(True, "--temporal/--no-temporal"),
    self_improvement: bool = typer.Option(
        False, "--self-improvement/--no-self-improvement"
    ),
) -> None:
    asyncio.run(ingest_items(input_path, temporal, self_improvement))


if __name__ == "__main__":
    app()
