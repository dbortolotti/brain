# API Setup Guide

This guide is for developers and operators who want to connect Brain to an LLM client, MCP client, ChatGPT app client, or direct HTTP integration. For end-user memory examples, see the [User Guide](USER_GUIDE.md).

Brain exposes two API surfaces:

- HTTP and JSON-RPC MCP over the FastAPI server.
- MCP stdio for local desktop clients that launch Brain as a subprocess.

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
BRAIN_ADMIN_MCP_PATH=/admin/mcp
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

If you customize the health route, update `BRAIN_HEALTH_PATH` accordingly.

The curated user/app MCP endpoint is:

```text
GET|POST /mcp
```

The full admin MCP endpoint is:

```text
GET|POST /admin/mcp
```

The path is controlled by:

```env
BRAIN_MCP_PATH=/mcp
BRAIN_ADMIN_MCP_PATH=/admin/mcp
```

The health path is controlled separately by `BRAIN_HEALTH_PATH`.

## HTTP Endpoints

Core memory endpoints:

```text
POST /memory/remember
POST /memory/ingest_source
POST /memory/recall
POST /memory/profile_entity
POST /memory/forget
POST /memory/review_recent
POST /memory/undo_last
```

OAuth, auth, and browser session endpoints:

```text
GET  /.well-known/oauth-protected-resource
GET  /.well-known/oauth-protected-resource/{resource_path:path}
GET  /.well-known/oauth-authorization-server
GET  /.well-known/openid-configuration
POST /register
GET|POST /authorize
POST /token
POST /revoke
POST /login
POST /logout
GET  /auth/session
GET  /api/session
PUT  /account/password
```

Admin user-management and personal access token endpoints:

```text
GET    /admin/users
POST   /admin/users
PUT    /admin/users/{user_id}
DELETE /admin/users/{user_id}
GET    /admin/tokens
POST   /admin/tokens
DELETE /admin/tokens/{token_id}
```

The public UI and dashboard are served by the same Brain HTTP process at the configured public base URL. The public UI paths are controlled by `BRAIN_PUBLIC_UI_PATH` and `BRAIN_PUBLIC_UI_API_PATH`.

Public UI and docs pages:

```text
GET /docs
GET /docs/oauth2-redirect
GET /redoc
GET /openapi.json
GET /healthz
GET /apple-touch-icon.png
GET /favicon.ico
GET /icon.png
```

Cognee/UI proxy routes are also served by the same Brain HTTP process:

```text
GET      /
GET|POST /cognee-login
POST     /cognee-logout
GET|POST /ui-login
POST     /ui-logout
DELETE|GET|PATCH|POST|PUT /cognee
DELETE|GET|PATCH|POST|PUT /cognee/{path:path}
DELETE|GET|PATCH|POST|PUT /cognee-api/{path:path}
DELETE|GET|PATCH|POST|PUT /ui
DELETE|GET|PATCH|POST|PUT /ui/{path:path}
DELETE|GET|PATCH|POST|PUT /ui-api/{path:path}
DELETE|GET|PATCH|POST|PUT /admin/cognee
DELETE|GET|PATCH|POST|PUT /admin/cognee/{path:path}
DELETE|GET|PATCH|POST|PUT /admin/cognee-api/{path:path}
```

Admin user-management endpoints:

```text
GET    /admin/users
POST   /admin/users
PUT    /admin/users/{user_id}
DELETE /admin/users/{user_id}
```

Legacy/Cognee datasource endpoints are also present:

```text
GET    /datasources
POST   /datasources
DELETE /datasources/{datasource}
```

Compatibility aliases also exist:

```text
POST   /create_datasource
GET    /list_datasources
POST   /delete_datasource
DELETE /delete_datasource/{datasource}
```

Brain exposes curated Cognee/admin operations such as forget, review_recent, undo_last, profile context sync, and `cognee_improve` on the internal surface. Internal Palate persistence tools, `brain_app_open_review_panel`, and `brain_palate_refresh_enrichment` stay on `/admin/mcp`.

## ChatGPT App Surface

Use the public app MCP surface for ChatGPT App or any user-facing client that should not see admin tools. The internal `/admin/mcp` surface exposes `brain_app_open_review_panel`; the public app surface does not. In production, the public MCP URLs are configured by `BRAIN_PUBLIC_BASE_URL`, `BRAIN_PUBLIC_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`. The public UI paths use `BRAIN_PUBLIC_UI_PATH` and `BRAIN_PUBLIC_UI_API_PATH`.

The curated app tool set is:

```text
brain_session
brain_recall
brain_remember
brain_ingest_source
brain_profile_entity
brain_list_open_loops
brain_get_memory
brain_review_recent
external chat-continuity workflow
external chat-continuity recall
brain_undo_last
brain_profile_context_list
brain_profile_context_remember
brain_profile_context_forget
brain_app_data_controls
brain_palate_describe_item
brain_palate_query
brain_palate_evaluate_options
brain_palate_confirm
brain_palate_cancel
brain_palate_correct_proposal
```

Read-only app tools require `brain.memory.read`; write tools require `brain.memory.write` as well and are rate-limited by `BRAIN_APP_WRITE_RATE_LIMIT_COUNT` and `BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS`. The app surface treats `brain_undo_last` and `brain_profile_context_forget` as destructive tools. The app surface includes selected Palate read/interaction tools; internal Palate persistence tools stay on `/admin/mcp`.

## Authentication

Local development usually runs with:

```env
BRAIN_AUTH_ENABLED=false
```

When auth is enabled, HTTP and MCP client requests require a bearer token accepted by one of these paths:

- Static token: `BRAIN_AUTH_TOKEN`
- Brain OAuth access token from the built-in authorization flow
- Brain personal access token, created by a superuser for a specific `user_id`

Static token example:

```env
BRAIN_AUTH_ENABLED=true
BRAIN_AUTH_TOKEN=replace-with-a-long-random-token
```

Then call:

```bash
curl http://127.0.0.1:8000/healthz -H "Authorization: Bearer $BRAIN_AUTH_TOKEN"
```

Protected unauthenticated requests return `401` with a `WWW-Authenticate` challenge that advertises Brain's protected-resource metadata.

For headless same-machine agents, use personal access tokens instead of browser OAuth. A superuser creates a token once, stores the returned secret in the agent's local secret store, and the agent calls Brain with `Authorization: Bearer ...`. Brain stores only a token hash and maps each request back to the token's `user_id`.

OAuth metadata routes:

```text
GET /.well-known/oauth-protected-resource
GET /.well-known/oauth-protected-resource/{resource_path:path}
GET /.well-known/oauth-authorization-server
GET /.well-known/openid-configuration
POST /register
GET|POST /authorize
POST /token
POST /revoke
```

When `BRAIN_AUTH_REQUIRE_PKCE=true`, authorization requests require a code challenge.

The browser dashboard uses cookie-based auth instead of pasted bearer tokens:

```text
POST /login
POST /logout
GET  /auth/session
GET  /api/session
PUT  /account/password
```

`/auth/session` and `/api/session` return the public current-user record and a CSRF token for dashboard write requests. `/api/session` remains a compatibility alias. Use `/account/password` to change the signed-in user's password.

The Cognee UI proxy also uses the Brain user registry. `/cognee-login` and `/ui-login` are login routes; `/cognee-logout` and `/ui-logout` are logout routes. `/admin/cognee` requires a superuser user record. `/ui`, `/ui-api`, `/cognee`, `/cognee-api`, `/admin/cognee`, `/admin/cognee-api`, and their path variants remain compatibility aliases.

Production auth is configured through `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_SCOPES`, `BRAIN_AUTH_REQUIRE_PKCE`, `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_USERS_FILE`, and `BRAIN_AUTH_SUPERUSER_IDS`. See [Production Secrets](production-secrets.md) for secret handling.

For multiple users, set `BRAIN_AUTH_USERS_FILE` to a JSON list or object of records with `id`/`user_id`, an Argon2id `password_hash`, optional `password_scheme`, optional `password_updated_at`, optional `display_name`, optional `email`, and optional `superuser` fields. Legacy records with a plaintext `password` are accepted only for migration; after successful login, or after running `scripts/migrate_auth_user_passwords.py`, Brain rewrites the registry without plaintext password fields. OAuth authorization stores the selected `user_id` in issued tokens; HTTP and MCP memory operations then scope Brain DB rows, profile context files, Palate data, recall logs, and app audit records to that user. Auth-enabled deployments fail closed if the configured users file is missing or empty.

Superusers can manage users and personal access tokens from the Brain dashboard's User Admin tab. The dashboard calls the admin HTTP endpoints below with the user's web session and CSRF token; MCP/API clients may still use an OAuth bearer token:

```text
GET    /admin/users
POST   /admin/users
PUT    /admin/users/{user_id}
DELETE /admin/users/{user_id}
GET    /admin/tokens
POST   /admin/tokens
DELETE /admin/tokens/{token_id}
```

These endpoints require full Brain auth plus a superuser user record. They never return passwords and refresh the in-process OAuth user registry after edits. Created or changed passwords are stored as Argon2id hashes.

## MCP Over HTTP

List MCP tools:

```bash
curl -s http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}'
```

Call `brain_session` first when an agent needs the active user's portable session id:

```bash
curl -s http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -d '{
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
curl -s http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -d '{
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

If auth is enabled, add:

```bash
-H "Authorization: Bearer $BRAIN_AUTH_TOKEN"
```

If you changed `BRAIN_MCP_PATH`, replace `/mcp` in the examples.

## MCP Stdio

Use stdio when a local MCP client should launch Brain directly rather than call an already-running HTTP service.

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

from the repository root with environment values derived from your active Brain settings.

## Internal MCP Tools

The internal `/admin/mcp` surface exposes:

```text
brain_app_open_review_panel
brain_session
brain_profile_context_remember
brain_profile_context_list
brain_profile_context_forget
brain_bias_context_remember
brain_bias_context_list
brain_bias_context_forget
brain_profile_context_sync
brain_ingest_source
brain_recall
brain_profile_entity
brain_forget
brain_review_recent
brain_undo_last
cognee_improve
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
  "context": {"confirmed_by_user": true}
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

Set `run_in_background` for very long documents or chat clients with short tool timeouts.

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

`chat_conclusion` is for durable conclusions made in chat.

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

Use `dry_run=true` when integrating a new client or when the LLM should ask for user confirmation before writing.

## Direct HTTP Examples

Remember:

```bash
curl -s http://127.0.0.1:8000/memory/remember -H "Content-Type: application/json" -d '{
  "input": "Sam from Goldman prefers morning calls.",
  "input_type": "fact",
  "source_policy": "memory_only",
  "dry_run": false
}'
```

Brain may classify the stored memory card as kind `person_fact`; `fact` is the client input type.

Ingest source:

```bash
curl -s http://127.0.0.1:8000/memory/ingest_source -H "Content-Type: application/json" -d '{
  "source_kind": "markdown",
  "title": "Meeting notes",
  "source": "Decision: use Brain DB as the source of truth. Cognee remains rebuildable.",
  "why_saved": "Architecture decision from project planning.",
  "extract_memories": true
}'
```

Recall:

```bash
curl -s http://127.0.0.1:8000/memory/recall -H "Content-Type: application/json" -d '{
  "query": "What do we know about Sam from Goldman?",
  "include_sources": true,
  "include_conflicts": true,
  "limit": 10
}'
```

Review recent writes:

```bash
curl -s http://127.0.0.1:8000/memory/review_recent -H "Content-Type: application/json" -d '{"limit": 10, "include_sources": true}'
```

Undo the latest write:

```bash
curl -s http://127.0.0.1:8000/memory/undo_last -H "Content-Type: application/json" -d '{}'
```

## Production Checks

Verify a production MCP deployment:

```bash
ENV_FILE=/etc/brain/brain.env make prod-check
```

Verify public direct-DNS routing:

```bash
make public-check
```

The production verifier checks release metadata, runtime paths, local health, local Brain UI health when enabled, MCP route behavior, the local Brain dashboard, the public app MCP surface, OAuth metadata when auth is enabled, and backup manifests unless `--skip-backups` is used. The public check verifies DNS/TLS reaches `brain.dceb.net` directly through Caddy and that required public pages are available. For authenticated verification against hashed user registries, set `BRAIN_VERIFIER_USER_ID` and `BRAIN_VERIFIER_PASSWORD_FILE` or `BRAIN_AUTH_VERIFIER_USER_ID` and `BRAIN_AUTH_VERIFIER_PASSWORD_FILE`.

## Troubleshooting

`401 authentication_required`

Auth is enabled. Add `Authorization: Bearer ...`, configure OAuth, or disable auth for local development.

`404 Not found` on `/mcp`

Check `BRAIN_MCP_PATH`. The server only accepts the configured MCP path.

No tools appear in an MCP client.

Confirm the client is calling `tools/list`, using the generated stdio config, or pointing at the right HTTP URL and path.

Writes fail because Cognee is unavailable.

Cognee is required for durable memory/source writes. Restore Cognee before retrying the write; Brain does not fall back to semantic Brain DB rows.

## Related Docs

- [User Guide](USER_GUIDE.md) covers end-user memory usage patterns.
- [Backup Scheme](BACKUP_SCHEME.md) covers backup and restore behavior.
- [Production Secrets](production-secrets.md) covers production secret handling.

<!-- brain-doc-source-hash: 266f6673ceb1d8ead8c797be1a46e805cc9fb2998345fc65af76235c224c8ff3 -->
<!-- brain-doc-source-commit: 16017c67b4220b00a152858a29667dbeaaa4c373 -->
