# Purpose

- Own Brain evaluation runners, model comparison tooling, golden queries, metrics, scoring, fixtures, and eval CLI behavior.

## Ownership

- `cli.py` owns `memory-stack-brain-eval` and model-eval subcommands.
- Runner, metrics, scoring, model matrix, and provider client modules own offline and model-backed evaluation execution.
- `fixtures/` owns package-level eval fixtures.

## Local Contracts

- Eval outputs belong in ignored runtime paths such as `eval_runs/`, `eval_reports/`, or explicit output paths, not in source unless they are durable fixtures.
- Live model/provider evals must make provider use and output paths explicit.
- Keep eval fixture semantics aligned with role specs and service-layer behavior.

## Work Guidance

- Preserve resumability and inspectable JSON/Markdown outputs for longer eval runs.
- When adding a metric or fixture mode, update the CLI and tests together.

## Verification

- Run `uv run pytest tests/test_brain_evals.py tests/test_model_eval_runner.py tests/test_e2e_model_suite.py` for eval changes.
- Use `make brain-eval` when a behavior change needs the golden eval path.

## Child DOX Index

- No child AGENTS.md files. Eval modules and package fixtures are owned here.
