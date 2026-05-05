# Brain

Cognee-native local memory evaluation harness.

## Quick Start

```bash
cp .env.gemini.example .env
make setup
make up
make check
make smoke
make eval
```

Profiles are selected through `PROFILE` and provider-specific environment variables:

- `gemini` for the Google challenger lane
- `openai` for the quality-ceiling lane
- `local` for the Ollama/Fastembed no-cloud lane

The HTTP service for production verification includes:

- `GET /healthz`
- `GET|POST /mcp`
- `GET /datasources` or `GET /list_datasources`
- `POST /datasources` or `POST /create_datasource`
- `DELETE /datasources/{datasource}` or `DELETE /delete_datasource/{datasource}`
- `GET /.well-known/oauth-protected-resource/mcp`
- `GET /.well-known/oauth-authorization-server`
- `POST /register`
- `GET|POST /authorize`
- `POST /token`
- `POST /revoke`

The Brain MCP tool surface now has two layers:

- High-level Brain memory tools: `remember(input, input_type="auto")`, `ingest_source`, `recall`, `profile_entity`, `list_open_loops`, `get_memory`, `resolve_conflict`, `forget`, and `sync_cognee`.
- Legacy Cognee harness tools: `remember(text, dataset_name, temporal=true, node_set=...)`, `add`, `cognify`, `recall(query, dataset, search_type="TEMPORAL", ...)`, `list_datasources`, `create_datasource`/`create_dataset`, `delete_datasource`, `list_node_sets`, and `create_node_set`.

Brain-owned memory is stored in the application control-plane database configured by
`BRAIN_DATABASE_URL` and defaults to `sqlite:///.data/brain/brain.db` for local
development. Set it to a Postgres URL for the production source of truth. Cognee
is treated as a projection/index; the first control-plane pass writes pending
`cognee_sync` rows and keeps the direct Cognee tools for evaluation/backfill.

Dataset and node-set names fail closed. If a tool sees a close existing name,
for example `my_health` versus `my-health`, it refuses the write/read and asks
you to retry with the exact existing name. To intentionally create the new
spelling, create the dataset or node set first.

The production Cognee web UI is published separately at:

- `https://brain.dceb.net/ui`
- local proxy: `http://127.0.0.1:8002`
- local Cognee frontend: `http://127.0.0.1:3000`
- local Cognee backend API: `http://127.0.0.1:8001`

The UI does not use the MCP OAuth authorization-code resource directly. The
browser app and Cognee backend have their own local auth assumptions, so Brain
puts a small reverse proxy in front of them and gates `/ui`, `/ui-api`, and
Next.js app routes with the same Brain auth password file used by MCP OAuth
approval.

Run it locally with:

```bash
make mcp-http
```

Run only the UI proxy locally with:

```bash
make ui-proxy
```

Production deployment is Phase 5 work and uses `/Volumes/xpg_usb4/prod/brain`.
When production auth is enabled, the OAuth password is stored at
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-password`.

Production request/response refinement logs are JSONL records written to:

```text
/Volumes/xpg_usb4/prod/brain/shared/logs/requests.jsonl
```

The log captures HTTP metadata plus request and response bodies. OAuth passwords,
authorization headers, auth codes, client secrets, and issued tokens are redacted.
