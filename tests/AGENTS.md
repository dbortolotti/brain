# Purpose

- Own repository tests, fixtures, hygiene checks, and test-only utilities.

## Ownership

- Top-level `test_*.py` files mirror source, deployment, docs, config, and script behavior.
- `model_eval_tests/` owns larger durable model-evaluation fixtures and its live runner.

## Local Contracts

- Tests must not require real secrets, private provider auth state, or production data by default.
- Runtime outputs, run folders, caches, and pyc files must remain untracked.
- When changing public behavior, update or add tests at the nearest affected boundary instead of only broad end-to-end coverage.
- Keep repository hygiene expectations aligned with `.gitignore` and `tests/test_repo_hygiene.py`.

## Work Guidance

- Prefer focused deterministic tests for service, store, parser, and config behavior.
- Use live/provider smoke tests only when explicitly intended and documented by the test or script.

## Verification

- Run targeted `uv run pytest <path>` for changed areas.
- Run full `uv run pytest` for broad changes.
- Run `uv run pytest tests/test_repo_hygiene.py` after changing ignored/generated/secret path handling.

## Child DOX Index

- `model_eval_tests/AGENTS.md` - durable model-evaluation fixtures, live runner, and fixture integrity checks.
