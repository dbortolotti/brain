"""Legacy direct Cognee recall CLI.

New recall should go through Brain service or MCP tools.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from memory_stack.cognee_adapter import SEARCH_TYPES, recall_text
from memory_stack.config import load_settings
from memory_stack.io import to_jsonable, write_json

app = typer.Typer(no_args_is_help=True)
console = Console()


def parse_search_type(value: str) -> str:
    normalized = str(value).strip().upper()
    if normalized not in SEARCH_TYPES:
        allowed = ", ".join(SEARCH_TYPES)
        raise typer.BadParameter(
            f"Unknown search type {normalized!r}. Allowed values: {allowed}"
        )
    return normalized


async def recall(
    query: str,
    dataset: str,
    search_type: str,
    top_k: int,
    node_name: list[str] | None,
    node_name_filter_operator: str,
    output_dir: str,
) -> dict:
    settings = load_settings()
    normalized_search_type = parse_search_type(search_type)

    start = time.perf_counter()
    result = await recall_text(
        query=query,
        dataset=dataset,
        search_type=normalized_search_type,
        top_k=top_k,
        node_name=node_name,
        node_name_filter_operator=node_name_filter_operator,
        settings=settings,
    )
    elapsed = time.perf_counter() - start

    payload = {
        "query": query,
        "dataset": dataset,
        "search_type": normalized_search_type,
        "top_k": top_k,
        "node_name": node_name,
        "node_name_filter_operator": node_name_filter_operator,
        "latency_seconds": elapsed,
        "result": to_jsonable(result),
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(output_dir) / f"recall_{dataset}_{normalized_search_type}_{ts}.json"
    write_json(path, payload)

    console.print(f"[green]OK[/green] latency={elapsed:.2f}s output={path}")
    console.print(result)
    return {"payload": payload, "path": str(path)}


@app.command()
def main(
    query: str = typer.Option(..., "--query"),
    dataset: str = typer.Option("property_trial", "--dataset"),
    search_type: str = typer.Option("TEMPORAL", "--search-type"),
    top_k: int = typer.Option(10, "--top-k"),
    node_name: list[str] | None = typer.Option(None, "--node-name"),
    node_name_filter_operator: str = typer.Option("OR", "--node-name-filter-operator"),
    output_dir: str = typer.Option("eval/results/raw", "--output-dir"),
) -> None:
    asyncio.run(
        recall(
            query,
            dataset,
            search_type,
            top_k,
            node_name,
            node_name_filter_operator,
            output_dir,
        )
    )


if __name__ == "__main__":
    app()
