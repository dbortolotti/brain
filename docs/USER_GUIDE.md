# Brain User Guide

Brain is a local personal memory service. It stores durable memory in Brain DB,
can project selected data into Cognee, and exposes memory operations through HTTP
and MCP-compatible JSON-RPC tools. Slack is available as a separate guarded
intake surface.

## Quick Start

Install dependencies and create a local environment file:

```bash
cp .env.example .env
make setup
uv run pytest
```

Start the MCP/HTTP service:

```bash
make mcp-http
```

The default local service is:

```text
http://127.0.0.1:8000
```

Check that it is running:

```bash
curl http://127.0.0.1:8000/healthz
```

By default Brain uses SQLite at `.data/brain/brain.db`. For a controlled schema
setup, run migrations explicitly:

```bash
uv run alembic upgrade head
```

## Configuration Basics

The main local configuration lives in `.env`. The most important local settings
are:

```env
BRAIN_DATABASE_URL=sqlite:///.data/brain/brain.db
BRAIN_MCP_HOST=127.0.0.1
BRAIN_MCP_PORT=8000
BRAIN_MCP_PATH=/mcp
BRAIN_AUTH_ENABLED=false
BRAIN_LLM_ENABLED=false
BRAIN_COGNEE_ENABLED=false
BRAIN_COGNEE_RECALL_ENABLED=false
```

If `BRAIN_AUTH_ENABLED=false`, local HTTP examples do not need an authorization
header. If you enable auth and set `BRAIN_AUTH_TOKEN`, include:

```bash
-H "Authorization: Bearer $BRAIN_AUTH_TOKEN"
```

## Remember A Fact

Use `remember` for short durable facts, preferences, decisions, and open
questions:

```bash
curl -s http://127.0.0.1:8000/memory/remember \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Sam from Goldman prefers morning calls.",
    "input_type": "person_fact",
    "source_policy": "memory_only"
  }'
```

Preview without writing:

```bash
curl -s http://127.0.0.1:8000/memory/remember \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The Brain project should keep Slack as the primary guarded intake.",
    "input_type": "project_state",
    "dry_run": true
  }'
```

## Ingest Source Material

Use `ingest_source` when the input is a longer artifact and Brain should keep
source provenance:

```bash
curl -s http://127.0.0.1:8000/memory/ingest_source \
  -H "Content-Type: application/json" \
  -d '{
    "source_kind": "markdown",
    "title": "Meeting notes",
    "source": "Decision: use Brain DB as the source of truth. Cognee remains rebuildable.",
    "why_saved": "Architecture decision from project planning.",
    "extract_memories": true
  }'
```

Common source kinds are `article`, `transcript`, `markdown`, `pdf`, `email`,
`table`, `chat_log`, and `other`.

## Recall Memories

Ask Brain to answer from stored memory:

```bash
curl -s http://127.0.0.1:8000/memory/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What do we know about Sam from Goldman?",
    "include_sources": true,
    "include_conflicts": true,
    "limit": 10
  }'
```

Useful recall modes are `auto`, `evidence`, `profile`, `open_loops`, `sources`,
`memories`, and `debug`:

```bash
curl -s http://127.0.0.1:8000/memory/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show open architecture questions",
    "mode": "open_loops"
  }'
```

## Profile An Entity

Build an entity-centric summary:

```bash
curl -s http://127.0.0.1:8000/memory/profile_entity \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sam from Goldman",
    "entity_type": "person",
    "include_sources": true,
    "include_conflicts": true
  }'
```

## Review And Undo Recent Ingestion

Review recent writes:

```bash
curl -s http://127.0.0.1:8000/memory/review_recent \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10,
    "include_sources": true
  }'
```

Undo the latest ingestion run:

```bash
curl -s http://127.0.0.1:8000/memory/undo_last \
  -H "Content-Type: application/json" \
  -d '{}'
```

Undo a specific run:

```bash
curl -s http://127.0.0.1:8000/memory/undo_last \
  -H "Content-Type: application/json" \
  -d '{"ingestion_run_id": "run_..."}'
```

Undo performs soft deletes.

## List Open Loops

```bash
curl -s "http://127.0.0.1:8000/memory/open_loops?status=open&limit=20"
```

Filter by topic:

```bash
curl -s "http://127.0.0.1:8000/memory/open_loops?topic=Slack&status=open"
```

## Fetch A Memory

```bash
curl -s http://127.0.0.1:8000/memory/mem_...
```

## Resolve Conflicts

When Brain detects a contradiction or duplicate, resolve it explicitly:

```bash
curl -s http://127.0.0.1:8000/memory/resolve_conflict \
  -H "Content-Type: application/json" \
  -d '{
    "conflict_memory_id": "mem_new",
    "target_memory_id": "mem_existing",
    "action": "supersede",
    "note": "Newer Slack correction replaces the older value."
  }'
```

Supported actions are `supersede`, `keep_both`, `mark_duplicate`,
`archive_old`, `reject_new`, and `mark_contradiction`.

## Cognee Projection

Cognee is optional. Brain DB remains the source of truth. Enable projection only
when you want semantic/vector-backed projection support:

```env
BRAIN_COGNEE_ENABLED=true
BRAIN_COGNEE_RECALL_ENABLED=true
```

Manually sync pending projections:

```bash
curl -s http://127.0.0.1:8000/memory/sync_cognee \
  -H "Content-Type: application/json" \
  -d '{"object_type": "all", "dataset": "all", "force": false}'
```

Mark projections stale for rebuild:

```bash
curl -s http://127.0.0.1:8000/memory/rebuild_cognee \
  -H "Content-Type: application/json" \
  -d '{"dataset": "all", "prune_first": false}'
```

## MCP Usage

The MCP endpoint is `POST /mcp` by default. A minimal JSON-RPC tool call looks
like this:

```bash
curl -s http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "brain_remember",
      "arguments": {
        "input": "Brain DB is the source of truth.",
        "input_type": "chat_conclusion"
      }
    }
  }'
```

List available tools:

```bash
curl -s http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

Core MCP tools include:

```text
brain_remember
brain_ingest_source
brain_recall
brain_profile_entity
brain_list_open_loops
brain_get_memory
brain_get_source
brain_resolve_conflict
brain_forget
brain_review_recent
brain_undo_last
brain_sync_cognee
brain_rebuild_cognee
brain_merge_entities
```

## Slack Usage

Slack runs as a separate service:

```bash
make slack-agent
```

The default Slack service is:

```text
http://127.0.0.1:8003
```

Useful Slack commands:

```text
/brain remember Sam from Goldman prefers morning calls.
/brain confirm Sam from Goldman prefers morning calls.
/brain recall What do we know about Sam from Goldman?
/brain profile Sam from Goldman
/brain open-loops Slack
/brain get-memory mem_...
/brain debug snapshot
```

Debug commands are restricted to `BRAIN_SLACK_ADMIN_USER_IDS`. See
[Slack Setup](SLACK_SETUP.md) for Slack app configuration.

## Testing And Verification

Run the regular test suite:

```bash
uv run pytest
```

Run lint checks:

```bash
uv run ruff check src tests
```

Verify the Slack service once it is running:

```bash
make slack-agent-check
```

Run a live model smoke check when provider credentials are configured:

```bash
ENV_FILE=/path/to/brain.env \
  uv run python scripts/live_model_smoke.py --scope active
```

## Operational Notes

- Brain DB is authoritative. Cognee is a rebuildable projection.
- Slack and MCP are intentionally separate services and ports.
- Slack write paths dry-run and require confirmation by default.
- Unit tests are designed not to require live Slack, live LLM calls, live
  Cognee, or network access.
- Production secret handling is documented in
  [Production Secrets](production-secrets.md).
