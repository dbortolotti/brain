# Purpose

- Own GitHub Actions workflows for repository validation and production release.

## Ownership

- `.github/workflows/validate.yml` owns pull-request and manual repository validation.
- `.github/workflows/release.yml` owns the manual production release of `main` to srv1: generated release-doc stamping, validation, config rendering, deploy, and tagging.

## Local Contracts

- Both workflows run on GitHub-hosted `ubuntu-latest` runners. No workflow may require a self-hosted runner, a Mac, or a path under `/Volumes/` (the local QA/staging tiers and the self-hosted `brain-prod` runner were retired on 2026-10-25 after a Mac reboot left Colima down and blocked a release for a day).
- Do not put literal secrets or rendered production values in workflow files; consume GitHub `vars` and `secrets`. srv1 access is the `BRAIN_PROD_SSH_KEY` secret plus the host key pinned in the workflow.
- Keep workflow validation commands aligned with `Makefile`, `pyproject.toml`, and the scripts they call.
- Release must stamp and validate the exact commit it deploys, read the production config baseline from srv1 before rendering, and create the version tag only after the install succeeded; a version whose tag already exists at a different SHA is refused.
- Workflows that update `docs/generated/` must preserve the docs generation contract in `docs/AGENTS.md`.

## Work Guidance

- Prefer explicit shell guards in workflow scripts: `set -euo pipefail`, clear failure messages, and deterministic paths.
- When adding an environment variable to deployment, update `scripts/render_prod_env.py`, `cfg/`, docs, and workflow env blocks together.

## Verification

- For validation workflow changes, run `make docs-check`, `uv run ruff check src tests scripts`, and `uv run pytest` when feasible.
- For deployment workflow changes, also run targeted tests for the touched scripts, commonly `uv run pytest tests/test_render_prod_env.py tests/test_deployment_requirements.py tests/test_docs_automation.py`.

## Child DOX Index

- No child AGENTS.md files. Workflow files are owned here.
