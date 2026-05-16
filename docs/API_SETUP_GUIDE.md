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
BRAIN_APP_MCP_PATH=/app/mcp
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

The curated ChatGPT App MCP endpoint is:

```text
GET|POST /app/mcp
```

The path is controlled by:

```env
BRAIN_MCP_PATH=/mcp
BRAIN_APP_MCP_PATH=/app/mcp
```

## HTTP Endpoints

Core memory endpoints:

```text
GET  /
GET  /app
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

Raw SQL and arbitrary Cognee primitives are not exposed as public MCP tools.
Brain does expose curated Cognee/admin operations such as sync, rebuild, and
configured improve.

## ChatGPT App Surface

Use `/app/mcp` for a ChatGPT App or any user-facing client that should not see
admin tools. In production its public URL is:

```text
https://brain.dceb.net/app/mcp
```

The browser dashboard is served by the same MCP process at:

```text
https://brain.dceb.net/
```

The curated app tool set is:

```text
brain_session
brain_recall
brain_remember
brain_profile_entity
brain_list_open_loops
brain_get_memory
brain_review_recent
brain_undo_last
brain_profile_context_list
brain_profile_context_remember
brain_profile_context_forget
brain_app_data_controls
```

`brain_remember` is confirmation-first on `/app/mcp`. Without explicit
confirmation it is forced to `dry_run=true`; after the user confirms, call it
again with `context.confirmed_by_user=true` to save. App-surface write tools
accept either top-level `confirmed_by_user=true` or
`context.confirmed_by_user=true`. Read-only app tools require
`brain.memory.read`; write tools require `brain.memory.write` as well, are
rate-limited, and append a redacted app write audit record. Destructive
app-surface calls such as `brain_undo_last` and
`brain_profile_context_forget` require confirmation. Admin tools, raw Cognee
projection tools, agent-memory clear, and Palate writes are not listed or
callable on `/app/mcp`.

Public app support pages are available at `/privacy`, `/terms`, and `/support`.

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

For multiple users, set `BRAIN_AUTH_USERS_FILE` to a JSON list or object of
records with `id`/`user_id`, `password`, optional `display_name`, optional
`email`, and optional `superuser` fields. OAuth authorization stores the selected
`user_id` in issued tokens; HTTP and MCP memory operations then scope Brain DB
rows, profile context files, Palate data, recall logs, and app audit records to
that user. Existing single-user data remains under `BRAIN_USER_ID=default`.

Superusers can manage users from the Brain dashboard's User Admin tab. The
dashboard calls the admin HTTP endpoints below with the user's bearer token:

```text
GET    /admin/users
POST   /admin/users
PUT    /admin/users/{user_id}
DELETE /admin/users/{user_id}
```

These endpoints require full Brain auth plus a superuser user record. They never
return passwords and refresh the in-process OAuth user registry after edits.

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

Call `brain_session` first when an agent needs Brain workflow names or the
standard portable session id:

```bash
curl -s http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "brain_session",
      "arguments": {}
    }
  }'
```

Call `brain_remember` for a durable fact or decision:

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
        "input_type": "fact",
        "source_policy": "memory_only",
        "dry_run": true
      }
    }
  }'
```

Use `brain_agent_memory`, not `brain_remember`, for chat-session handovers,
conversation summaries, agent workflow learnings, and preserved chat context.
Pass the `session_id` returned by `brain_session`.

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

## Internal MCP Tools

The internal `/mcp` surface exposes:

```text
brain_session
brain_profile_context_remember
brain_profile_context_list
brain_profile_context_forget
brain_profile_context_sync
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
cognee_improve
brain_agent_memory
brain_agent_memory_recall
brain_agent_memory_clear
brain_merge_entities
brain_palate_describe_item
brain_palate_remember
brain_palate_query
brain_palate_evaluate_options
brain_palate_log_decision
brain_palate_confirm
brain_palate_cancel
brain_palate_correct_proposal
brain_palate_refresh_enrichment
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

`chat_conclusion` is for durable conclusions made in chat. It is not the
handover/session-memory path. Use `brain_agent_memory` for chat-session memory
and handovers.

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
    "input_type": "fact",
    "source_policy": "memory_only",
    "dry_run": false
  }'
```

Brain may classify the stored memory card as kind `person_fact`; `fact` is the
client input type.

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
