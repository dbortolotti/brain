# Purpose

- Own GitHub Actions workflows for repository validation, local QA deploys, local staging deploys, and release promotion.

## Ownership

- `.github/workflows/validate.yml` owns pull-request and manual repository validation.
- `.github/workflows/deploy-local-qa.yml` owns main-branch QA deployment on the self-hosted `brain-prod` runner.
- `.github/workflows/deploy-local-staging.yml` owns versioned staging deployment and generated release-doc stamping.
- `.github/workflows/release.yml` owns promotion of an already staged version to production.

## Local Contracts

- Do not put literal secrets or rendered production values in workflow files; consume GitHub `vars` and `secrets`.
- Keep workflow validation commands aligned with `Makefile`, `pyproject.toml`, and the scripts they call.
- Release promotion must verify that the requested tag, staged metadata, and staging current symlink point to the same commit.
- Staging release workflows that update `docs/generated/` must preserve the docs generation contract in `docs/AGENTS.md`.

## Work Guidance

- Prefer explicit shell guards in workflow scripts: `set -euo pipefail`, clear failure messages, and deterministic paths.
- When adding an environment variable to deployment, update `scripts/render_prod_env.py`, `cfg/`, docs, and workflow env blocks together.

## Verification

- For validation workflow changes, run `make docs-check`, `uv run ruff check src tests scripts`, and `uv run pytest` when feasible.
- For deployment workflow changes, also run targeted tests for the touched scripts, commonly `uv run pytest tests/test_render_prod_env.py tests/test_deployment_requirements.py`.

## Child DOX Index

- No child AGENTS.md files. Workflow files are owned here.
