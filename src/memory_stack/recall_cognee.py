from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from memory_stack.cognee_adapter import recall_text
from memory_stack.config import load_settings
from memory_stack.io import to_jsonable, write_json

app = typer.Typer(no_args_is_help=True)
console = Console()


def parse_search_type(value: str) -> str:
    return str(value).upper()


async def recall(
    query: str,
    dataset: str,
    search_type: str,
    top_k: int,
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
        settings=settings,
    )
    elapsed = time.perf_counter() - start

    payload = {
        "query": query,
        "dataset": dataset,
        "search_type": normalized_search_type,
        "top_k": top_k,
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
    output_dir: str = typer.Option("eval/results/raw", "--output-dir"),
) -> None:
    asyncio.run(recall(query, dataset, search_type, top_k, output_dir))


if __name__ == "__main__":
    app()
