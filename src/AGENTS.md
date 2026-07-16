# Purpose

- Own Python source code for the Brain application and package exports.

## Ownership

- `memory_stack/` is the main application package.
- `cfg.py` is a top-level compatibility module and must stay aligned with `memory_stack.cfg`.

## Local Contracts

- Target Python 3.12 and the dependencies declared in `pyproject.toml`.
- Brain DB and service-layer policy are canonical for control state; Cognee owns semantic memory storage and retrieval.
- Public HTTP, MCP, and ChatGPT App surfaces must remain curated and must not expose raw SQL, arbitrary Cognee primitives, secrets, or private operational internals.
- Keep auth, session, request logging, and data-control behavior explicit and tested.

## Work Guidance

- Prefer existing service, model, and store boundaries over introducing parallel paths.
- Keep FastAPI and MCP request/response shapes stable unless the caller-facing contract is intentionally changing.
- When source changes affect docs or deployment behavior, update the owning child AGENTS.md chain and managed docs in the same pass.

## Verification

- Run `uv run ruff check src` after source edits.
- Run targeted `uv run pytest` tests for the touched package area; use full `uv run pytest` for broad behavior changes.

## Child DOX Index

- `memory_stack/AGENTS.md` - main Brain package contracts and package-level child boundaries.
