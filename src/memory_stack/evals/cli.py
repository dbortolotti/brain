from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from memory_stack.config import load_settings
from memory_stack.evals.runner import run_golden_evals


app = typer.Typer(no_args_is_help=False)
console = Console()


@app.command()
def main(output: str | None = typer.Option(None, "--output")) -> None:
    result = run_golden_evals(load_settings())
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        console.print(f"[green]wrote[/green] {path}")
    else:
        console.print_json(data=result["metrics"])


if __name__ == "__main__":
    app()
