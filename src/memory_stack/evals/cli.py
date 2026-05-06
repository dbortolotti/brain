from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from memory_stack.config import load_settings
from memory_stack.evals.model_matrix import REGISTRY_PATH
from memory_stack.evals.model_runner import ModelEvalRunConfig, run_model_evals
from memory_stack.evals.runner import run_golden_evals


app = typer.Typer(no_args_is_help=False)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    output: str | None = typer.Option(None, "--output", help="Golden eval JSON output."),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    run_golden_command(output=output)


@app.command("golden")
def golden(output: str | None = typer.Option(None, "--output")) -> None:
    run_golden_command(output=output)


@app.command("models")
def models(
    registry: Path = typer.Option(REGISTRY_PATH, "--registry"),
    fixture_set: str = typer.Option("smoke", "--fixture-set"),
    roles: str | None = typer.Option(None, "--roles", help="Comma-separated role list."),
    model_refs: str | None = typer.Option(None, "--models", help="Comma-separated model refs."),
    model_set: str | None = typer.Option(
        None,
        "--model-set",
        help="Named model set, e.g. model-test-initial.",
    ),
    scope: str = typer.Option("core", "--scope", help="core, enabled, or all when --models is absent."),
    include_judge: bool = typer.Option(False, "--include-judge"),
    repeat_runs: int = typer.Option(1, "--repeat-runs", min=1),
    bootstrap_samples: int = typer.Option(1000, "--bootstrap-samples", min=0),
    output: Path = typer.Option(..., "--output"),
    report_md: Path | None = typer.Option(None, "--report-md"),
    raw_output_dir: Path | None = typer.Option(None, "--raw-output-dir"),
) -> None:
    config = ModelEvalRunConfig(
        registry_path=registry,
        fixture_set=fixture_set,
        roles=parse_csv(roles),
        model_refs=parse_csv_list(model_refs),
        model_set=model_set,
        scope=scope,
        include_judge=include_judge,
        repeat_runs=repeat_runs,
        bootstrap_samples=bootstrap_samples,
        output_path=output,
        report_md_path=report_md,
        raw_output_dir=raw_output_dir,
    )
    result = run_model_evals(load_settings(), config)
    console.print(f"[green]wrote[/green] {output}")
    if report_md:
        console.print(f"[green]wrote[/green] {report_md}")
    console.print_json(data={"run_id": result["run_id"], "record_count": result["record_count"]})


def run_golden_command(output: str | None) -> None:
    result = run_golden_evals(load_settings())
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        console.print(f"[green]wrote[/green] {path}")
    else:
        console.print_json(data=result["metrics"])


def parse_csv(value: str | None) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}


def parse_csv_list(value: str | None) -> list[str] | None:
    items = [item.strip() for item in (value or "").split(",") if item.strip()]
    return items or None


if __name__ == "__main__":
    app()
