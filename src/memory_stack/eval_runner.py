"""Legacy Cognee-first eval runner.

New Brain evals live under memory_stack.evals.
"""
from __future__ import annotations

import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from memory_stack.cognee_adapter import recall_text
from memory_stack.config import load_settings
from memory_stack.io import load_eval_queries, to_jsonable, write_json
from memory_stack.scoring import score_result

app = typer.Typer(no_args_is_help=True)
console = Console()


CSV_COLUMNS = [
    "timestamp",
    "profile",
    "llm_provider",
    "llm_model",
    "embedding_provider",
    "embedding_model",
    "dataset",
    "query_id",
    "search_type",
    "query",
    "latency_seconds",
    "score",
    "raw_result_path",
    "notes",
]


async def run_eval(queries_path: str, output_path: str, top_k: int = 10) -> list[dict[str, Any]]:
    settings = load_settings()
    queries = load_eval_queries(queries_path)
    output = Path(output_path)
    raw_dir = output.parent / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for index, eval_query in enumerate(queries, start=1):
        console.print(f"[cyan]query[/cyan] {eval_query.id} search_type={eval_query.search_type}")
        start = time.perf_counter()
        result = await recall_text(
            query=eval_query.query,
            dataset=eval_query.dataset,
            search_type=eval_query.search_type,
            top_k=top_k,
            node_name=eval_query.node_name,
            node_name_filter_operator=eval_query.node_name_filter_operator,
            settings=settings,
        )
        elapsed = time.perf_counter() - start
        timestamp = datetime.now().isoformat(timespec="microseconds")
        raw_path = raw_result_path(raw_dir, timestamp, eval_query.id, index)
        write_json(
            raw_path,
            {
                "query": eval_query.model_dump(),
                "latency_seconds": elapsed,
                "result": to_jsonable(result),
            },
        )
        score = score_result(result, eval_query.must_include)
        row = {
            "timestamp": timestamp,
            "profile": settings.profile,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "dataset": eval_query.dataset,
            "query_id": eval_query.id,
            "search_type": eval_query.search_type,
            "query": eval_query.query,
            "latency_seconds": f"{elapsed:.4f}",
            "score": score["score"],
            "raw_result_path": str(raw_path),
            "notes": score["notes"],
        }
        rows.append(row)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"[green]wrote[/green] {output}")
    return rows


def raw_result_path(raw_dir: Path, timestamp: str, query_id: str, index: int) -> Path:
    safe_timestamp = timestamp.replace(":", "").replace(".", "")
    return raw_dir / f"{safe_timestamp}_{index:03d}_{query_id}.json"


@app.command()
def main(
    queries: str = typer.Option("eval/queries.yaml", "--queries"),
    output: str = typer.Option("eval/results/results.csv", "--output"),
    top_k: int = typer.Option(10, "--top-k"),
) -> None:
    asyncio.run(run_eval(queries, output, top_k))


if __name__ == "__main__":
    app()
