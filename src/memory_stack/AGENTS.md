# Purpose

- Own the Brain application package: HTTP and MCP server, service layer, control store, Cognee integration, auth, UI proxy, recall, ingestion, taste, evals, migrations, and supporting utilities.

## Ownership

- Core modules at this level own settings, models, stores, service orchestration, MCP/HTTP surfaces, OAuth/auth, sessions, request logging, icons, CLI entry points, and UI proxy/service behavior.
- Domain subpackages own specialized implementation under the child index below.

## Local Contracts

- `mcp_server.py` is the public/admin HTTP and MCP surface; keep public, app, and admin tool exposure intentionally separated.
- `brain_service.py` coordinates durable writes, ingestion, recall, and Cognee calls; do not bypass service-level policy for user-facing writes.
- `brain_store.py` and migrations own canonical control records, receipts, confirmations, user scope, profile context, and audit state.
- MCP `brain_remember` durably queues an external receipt before Cognee work,
  reuses that receipt for idempotent retries and completion status, and resumes
  pending queue records on service startup. Keep queued input private and remove
  it from the receipt metadata after successful processing.
- `cfg.py` owns settings loading and path normalization; new settings must stay aligned with `cfg/`, scripts, docs, and workflows.
- Auth, OAuth, session, and request logging code must avoid leaking tokens, cookies, passwords, raw provider payloads, or request bodies beyond configured safe limits.
- JSON-RPC notifications are requests without an `id` key: execute them without a response, omit them from batch responses, and return an empty HTTP `202` when a POST produces no JSON-RPC response; an explicit null `id` remains a request id.

## Work Guidance

- Keep durable behavior understandable from models, service code, store code, and docs together.
- Prefer typed request/response models and deterministic validation before calling LLM or Cognee layers.
- Preserve existing user-scope and profile-name handling when adding tools or storage paths.

## Verification

- Run targeted tests for touched modules, commonly `tests/test_mcp_server.py`, `tests/test_brain_service.py`, `tests/test_provider_auth.py`, `tests/test_ui_service.py`, `tests/test_ui_proxy.py`, or `tests/test_migrations.py`.
- Run `uv run ruff check src/memory_stack` after package edits.

## Child DOX Index

- `agents/AGENTS.md` - prompt role specs, shared agent rules, and prompt contract helpers.
- `cognee/AGENTS.md` - Cognee datapoints, OAuth compatibility, and capability probes.
- `evals/AGENTS.md` - Brain golden evals, model evals, scoring, metrics, and eval CLI.
- `ingestion/AGENTS.md` - source classifiers and source parsers.
- `migrations/AGENTS.md` - Alembic migration environment and versioned Brain DB migrations.
- `recall/AGENTS.md` - recall planning, retrieval, evidence building, and answer synthesis.
- `taste/AGENTS.md` - Palate/taste domain models, enrichment, routing, ranking, proposals, and Cognee-backed taste store.
- Unnested subpackages and assets owned here: `llm/`, `resolution/`, `static/`, `workers/`, and any empty placeholder package folders.
