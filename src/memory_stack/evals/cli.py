from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from memory_stack.config import load_settings
from memory_stack.evals.e2e_model_suite import run_e2e_model_suite
from memory_stack.evals.model_runner import ModelEvalRunConfig, run_model_evals, run_rescore, run_rerun_failed
from memory_stack.evals.provider_client import LiveProviderClient
from memory_stack.evals.runner import run_golden_evals
from memory_stack.model_selection import parse_csv_list, parse_csv_set


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
    fixture_set: str = typer.Option("smoke", "--fixture-set"),
    mode: str = typer.Option("broad", "--mode", help="broad or fine-grained"),
    roles: str | None = typer.Option(None, "--roles", help="Comma-separated role list."),
    model_refs: str | None = typer.Option(None, "--models", help="Comma-separated model refs."),
    include_judge: bool = typer.Option(False, "--include-judge"),
    repeat_runs: int = typer.Option(1, "--repeat-runs", min=1),
    bootstrap_samples: int = typer.Option(1000, "--bootstrap-samples", min=0),
    endpoint_max_concurrency: int = typer.Option(1, "--endpoint-max-concurrency", min=1),
    retry_attempts: int = typer.Option(2, "--retry-attempts", min=0),
    repeat: int | None = typer.Option(None, "--repeat", min=1),
    retry_backoff_seconds: float = typer.Option(1.0, "--retry-backoff-seconds", min=0.0),
    output: Path | None = typer.Option(None, "--output"),
    output_json: Path | None = typer.Option(None, "--output-json"),
    report_md: Path | None = typer.Option(None, "--report-md"),
    raw_output_dir: Path | None = typer.Option(None, "--raw-output-dir"),
) -> None:
    resolved_repeat_runs = repeat or repeat_runs
    resolved_output = output_json or output
    if resolved_output is None:
        raise typer.BadParameter("pass --output or --output-json")
    config = ModelEvalRunConfig(
        fixture_set=fixture_set,
        mode=mode,
        roles=parse_csv_set(roles),
        model_refs=parse_csv_list(model_refs),
        include_judge=include_judge,
        repeat_runs=resolved_repeat_runs,
        bootstrap_samples=bootstrap_samples,
        output_path=resolved_output,
        report_md_path=report_md,
        raw_output_dir=raw_output_dir,
        endpoint_max_concurrency=endpoint_max_concurrency,
        retry_attempts=retry_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )
    result = run_model_evals(load_settings(), config, progress_callback=progress_printer())
    console.print(f"[green]wrote[/green] {resolved_output}")
    console.print(f"[green]wrote[/green] {result['report_md_path']}")
    console.print(f"[green]wrote[/green] {result['report_html_path']}")
    console.print(f"[green]wrote[/green] {result['failed_manifest_jsonl_path']}")
    console.print(f"[green]wrote[/green] {result['failed_manifest_md_path']}")
    console.print_json(data={"run_id": result["run_id"], "record_count": result["record_count"]})


@app.command("e2e-models")
def e2e_models(
    output_json: Path = typer.Option(..., "--output-json"),
    database_path: Path | None = typer.Option(None, "--database-path"),
    model_ref: str | None = typer.Option(None, "--model"),
    retry_attempts: int = typer.Option(2, "--retry-attempts", min=0),
    retry_backoff_seconds: float = typer.Option(1.0, "--retry-backoff-seconds", min=0.0),
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    resolved_database_path = database_path or output_json.with_suffix(".db")
    if resolved_database_path.exists():
        resolved_database_path.unlink()
    settings = load_settings().model_copy(
        update={"brain_database_url": f"sqlite:///{resolved_database_path}"}
    )
    result = run_e2e_model_suite(
        settings,
        model_ref=model_ref,
        client=LiveProviderClient(
            settings,
            retry_attempts=retry_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
        ),
    )
    output_json.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    console.print(f"[green]wrote[/green] {output_json}")
    console.print(f"[green]wrote[/green] {resolved_database_path}")
    console.print_json(
        data={
            "model": result["model"],
            "record_count": result["record_count"],
            "pass_count": result["pass_count"],
            "fail_count": result["fail_count"],
        }
    )


@app.command("rerun-failed")
def rerun_failed(
    source_json: Path = typer.Option(..., "--source-json"),
    failed_manifest: Path = typer.Option(..., "--failed-manifest"),
    output_json: Path = typer.Option(..., "--output-json"),
    endpoint_max_concurrency: int = typer.Option(1, "--endpoint-max-concurrency", min=1),
    bootstrap_samples: int = typer.Option(1000, "--bootstrap-samples", min=0),
    retry_attempts: int = typer.Option(2, "--retry-attempts", min=0),
    retry_backoff_seconds: float = typer.Option(1.0, "--retry-backoff-seconds", min=0.0),
    overwrite: bool = typer.Option(False, "--overwrite"),
    failure_class: str | None = typer.Option(None, "--failure-class"),
    role: str | None = typer.Option(None, "--role"),
    model: str | None = typer.Option(None, "--model"),
) -> None:
    result = run_rerun_failed(
        load_settings(),
        source_path=source_json,
        failed_manifest_path=failed_manifest,
        output_path=output_json,
        overwrite=overwrite,
        bootstrap_samples=bootstrap_samples,
        endpoint_max_concurrency=endpoint_max_concurrency,
        retry_attempts=retry_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
        failure_class=failure_class,
        role=role,
        model=model,
    )
    console.print(f"[green]updated[/green] {output_json}")
    console.print(f"[green]wrote[/green] {result['report_md_path']}")
    console.print(f"[green]wrote[/green] {result['report_html_path']}")
    console.print(f"[green]wrote[/green] {result['failed_manifest_jsonl_path']}")
    console.print(f"[green]wrote[/green] {result['failed_manifest_md_path']}")
    console.print_json(data={"run_id": result["run_id"], "record_count": result["record_count"]})


@app.command("rescore")
def rescore(
    source_json: Path = typer.Option(..., "--source-json"),
    output_json: Path = typer.Option(..., "--output-json"),
    bootstrap_samples: int = typer.Option(1000, "--bootstrap-samples", min=0),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    result = run_rescore(
        source_path=source_json,
        output_path=output_json,
        overwrite=overwrite,
        bootstrap_samples=bootstrap_samples,
    )
    console.print(f"[green]updated[/green] {output_json}")
    console.print(f"[green]wrote[/green] {result['report_md_path']}")
    console.print(f"[green]wrote[/green] {result['report_html_path']}")
    console.print(f"[green]wrote[/green] {result['failed_manifest_jsonl_path']}")
    console.print(f"[green]wrote[/green] {result['failed_manifest_md_path']}")
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


def progress_printer():
    last_printed = {"value": 0}

    def print_progress(done: int, total: int, record: dict) -> None:
        should_print = (
            done == 1
            or done == total
            or done - last_printed["value"] >= 25
            or record.get("status") == "fail"
        )
        if not should_print:
            return
        last_printed["value"] = done
        console.print(
            "[cyan]progress[/cyan] "
            f"{done}/{total} "
            f"{record['model']} {record['role']} {record['fixture_id']} "
            f"status={record['status']}"
        )

    return print_progress


if __name__ == "__main__":
    app()
