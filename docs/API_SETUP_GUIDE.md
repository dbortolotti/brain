# API Setup Guide

This guide is for developers and operators who want to connect Brain to an LLM
client, MCP client, or direct HTTP integration. For end-user memory examples,
see the [User Guide](USER_GUIDE.md).

Brain exposes two API surfaces:

- HTTP and JSON-RPC MCP over the FastAPI server.
- MCP stdio for local desktop clients that launch Brain as a subprocess.

Slack is separate and uses its own service and routes. See
[Slack Setup](SLACK_SETUP.md) for Slack app configuration.

## Install

Create a local env file and install dependencies:

```bash
cp .env.example .env
make setup
```

Run tests before wiring a client:

```bash
uv run pytest
```

By default, local Brain uses:

```env
BRAIN_DATABASE_URL=sqlite:///.data/brain/brain.db
BRAIN_MCP_HOST=127.0.0.1
BRAIN_MCP_PORT=8000
BRAIN_MCP_PATH=/mcp
BRAIN_AUTH_ENABLED=false
```

For controlled schema setup:

```bash
uv run alembic upgrade head
```

## Run The HTTP/MCP Server

Start the server:

```bash
make mcp-http
```

Equivalent command:

```bash
uv run python -m memory_stack.mcp_server
```

Default local URL:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

The MCP endpoint is:

```text
GET|POST /mcp
```

The path is controlled by:

```env
BRAIN_MCP_PATH=/mcp
```

## HTTP Endpoints

Core memory endpoints:

```text
POST /memory/remember
POST /memory/ingest_source
POST /memory/recall
POST /memory/profile_entity
GET  /memory/open_loops
GET  /memory/{memory_id}
POST /memory/forget
POST /memory/resolve_conflict
POST /memory/review_recent
POST /memory/undo_last
POST /memory/sync_cognee
POST /memory/rebuild_cognee
POST /memory/merge_entities
```

Legacy/Cognee datasource endpoints are also present:

```text
GET    /datasources
POST   /datasources
DELETE /datasources/{datasource}
```

Low-level SQL and raw Cognee primitives are not exposed as public MCP tools.

## Authentication

Local development usually runs with:

```env
BRAIN_AUTH_ENABLED=false
```

When auth is enabled, HTTP and MCP requests require a bearer token accepted by
one of these paths:

- Static token: `BRAIN_AUTH_TOKEN`
- Brain OAuth access token from the built-in authorization flow

Static token example:

```env
BRAIN_AUTH_ENABLED=true
BRAIN_AUTH_TOKEN=replace-with-a-long-random-token
```

Then call:

```bash
curl http://127.0.0.1:8000/healthz \
  -H "Authorization: Bearer $BRAIN_AUTH_TOKEN"
```

Protected unauthenticated requests return `401` with a `WWW-Authenticate`
challenge that advertises Brain's protected-resource metadata.

OAuth metadata routes:

```text
GET /.well-known/oauth-protected-resource
GET /.well-known/oauth-protected-resource/{resource_path}
GET /.well-known/oauth-authorization-server
POST /register
GET|POST /authorize
POST /token
POST /revoke
```

Production auth is configured through `BRAIN_AUTH_PASSWORD_FILE`,
`BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_SCOPES`, and token lifetime settings. See
[Production Secrets](production-secrets.md) for secret handling.

## MCP Over HTTP

List MCP tools:

```bash
curl -s http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

Call `brain_remember`:

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
        "input_type": "chat_conclusion",
        "source_policy": "memory_only",
        "dry_run": true
      }
    }
  }'
```

If auth is enabled, add:

```bash
-H "Authorization: Bearer $BRAIN_AUTH_TOKEN"
```

## MCP Stdio

Use stdio when a local MCP client should launch Brain directly rather than call
an already-running HTTP service.

Export a Claude Desktop config:

```bash
make mcp-config
```

Write it directly to Claude Desktop's config:

```bash
uv run python scripts/export_mcp_config.py --write
```

Write it somewhere else for inspection:

```bash
uv run python scripts/export_mcp_config.py --output /tmp/brain-mcp-config.json
```

The generated config runs:

```text
python -m memory_stack.mcp_stdio
```

from the repository root with environment values derived from your active
Brain settings.

## MCP Tools

The public MCP tools are:

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

Use `brain_remember` for short durable statements:

```json
{
  "input": "Maya prefers written briefs before vendor calls.",
  "input_type": "auto",
  "source_policy": "memory_only",
  "dry_run": false
}
```

Use `brain_ingest_source` for longer source material:

```json
{
  "source": "Decision: Slack remains the primary guarded intake. Open question: should Telegram be added later?",
  "source_kind": "markdown",
  "title": "Architecture review notes",
  "why_saved": "Project state and follow-up planning.",
  "extract_memories": true,
  "dry_run": false,
  "run_in_background": true
}
```

Set `run_in_background` for very long documents or chat clients with short tool
timeouts. The tool returns `status: queued`; Brain then writes source/memory rows
in-process and leaves Cognee projection as `pending` for `brain_sync_cognee`.

Use `brain_recall` to answer from memory:

```json
{
  "query": "What decisions have we made about Slack intake?",
  "mode": "auto",
  "include_sources": true,
  "include_superseded": false,
  "include_conflicts": true,
  "limit": 20
}
```

## Input Types And Source Kinds

Common `brain_remember` input types:

```text
auto
note
fact
thought
person_interaction
open_question
research_question
chat_conclusion
table
```

Common `brain_ingest_source` source kinds:

```text
auto
article
transcript
markdown
pdf
email
table
chat_log
other
```

Source policies:

```text
auto
memory_only
source_only
source_and_memory
```

Use `dry_run=true` when integrating a new client or when the LLM should ask for
user confirmation before writing.

## Direct HTTP Examples

Remember:

```bash
curl -s http://127.0.0.1:8000/memory/remember \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Sam from Goldman prefers morning calls.",
    "input_type": "person_fact",
    "source_policy": "memory_only",
    "dry_run": false
  }'
```

Ingest source:

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

Recall:

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

Review recent writes:

```bash
curl -s http://127.0.0.1:8000/memory/review_recent \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "include_sources": true}'
```

Undo the latest write:

```bash
curl -s http://127.0.0.1:8000/memory/undo_last \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Checks

Verify a production MCP deployment:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make prod-check
```

Verify public Cloudflare routing:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make cloudflare-verify
```

The production verifier checks health, MCP route behavior, OAuth metadata when
auth is enabled, and backup manifests unless `--skip-backups` is used.

## Troubleshooting

`401 authentication_required`

Auth is enabled. Add `Authorization: Bearer ...`, configure OAuth, or disable
auth for local development.

`404 Not found` on `/mcp`

Check `BRAIN_MCP_PATH`. The server only accepts the configured MCP path.

No tools appear in an MCP client.

Confirm the client is calling `tools/list`, using the generated stdio config, or
pointing at the right HTTP URL and path.

Writes succeed but recall misses new data.

Brain DB is authoritative, but optional Cognee/vector projection may be pending.
Use `brain_recall` with direct Brain evidence first, then inspect
`cognee_sync_status` or run `brain_sync_cognee` if projection is enabled.

Slack routes hit the MCP server.

Route `/slack/*` to the Slack agent port, not the MCP server. See
[Slack Setup](SLACK_SETUP.md).

## Related Docs

- [User Guide](USER_GUIDE.md) covers end-user memory usage patterns.
- [Slack Setup](SLACK_SETUP.md) covers Slack app and route configuration.
- [Backup Scheme](BACKUP_SCHEME.md) covers backup and restore behavior.
- [Production Secrets](production-secrets.md) covers production secret handling.
