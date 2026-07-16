# Purpose

- Own executable operational scripts for setup checks, deployment, config rendering, backups, migrations, maintenance, docs generation, smoke tests, and production verification.

## Ownership

- Python scripts in this folder are repo-local CLIs and automation helpers.
- Shell scripts in this folder bootstrap or run deployment and production services.
- `production_check_utils.py` is shared utility code for production verification scripts.

## Local Contracts

- Scripts must be safe to run from the repository root unless their help text states otherwise.
- Do not print or persist secrets, provider auth tokens, raw private payloads, or full datasets.
- Destructive scripts such as resets, pruning, and migrations must keep explicit names and arguments for destructive behavior.
- Deployment and render scripts must stay aligned with `cfg/`, `.github/workflows/`, `deployment/`, and operator docs.

## Work Guidance

- Prefer `Path(__file__).resolve().parents[1]` or equivalent repo-root discovery over fragile current-directory assumptions.
- Keep script output actionable and concise; use nonzero exits for verification failures.
- For scripts importing `memory_stack`, preserve the existing `src` path setup or use project entry points.

## Verification

- Run `uv run ruff check scripts` after Python script edits.
- Run targeted tests for changed scripts, such as `uv run pytest tests/test_render_prod_env.py`, `tests/test_backup_stores.py`, or `tests/test_staging_e2e_suite_script.py`.

## Child DOX Index

- No child AGENTS.md files. All scripts are owned here.
