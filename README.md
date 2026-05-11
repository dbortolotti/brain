# Brain

Brain is a local personal memory control plane exposed through a small MCP
surface. Brain DB is the source of truth for memory identity, lifecycle, entity
resolution, conflicts, open loops, and Cognee sync state. Cognee is an optional
semantic projection that can be rebuilt from Brain DB.

## Documentation

- [User Guide](docs/USER_GUIDE.md) - end-user guidance for saving and recalling
  memories through Slack or an LLM.
- [API Setup Guide](docs/API_SETUP_GUIDE.md) - HTTP, MCP, auth, client setup,
  and integration examples.
- [Slack Setup Guide](docs/SLACK_SETUP.md) - Slack app configuration, routes,
  allowlists, and troubleshooting.
- [Backup Scheme](docs/BACKUP_SCHEME.md) - backup contents, verification,
  Google Drive replication, and restore outline.
- [Production Secrets](docs/production-secrets.md) - production secret and
  variable handling.
- [Runtime Flow Diagrams](docs/role_flow_diagram.md) - current runtime flow and
  model-role topology notes.

## Local Dev Setup

```bash
cp .env.openai.example .env
make setup
uv run pytest
```

By default Brain uses SQLite at `sqlite:///.data/brain/brain.db`. The store also
creates the schema automatically for local tests and dev, and Alembic migrations
are available for production-controlled setup:

```bash
uv run alembic upgrade head
```

## Running The MCP Server

```bash
make mcp-http
```

HTTP endpoints include:

- `GET /healthz`
- `GET|POST /mcp`
- `POST /memory/remember`
- `POST /memory/ingest_source`
- `POST /memory/recall`
- `POST /memory/profile_entity`
- `GET /memory/open_loops`
- `POST /memory/review_recent`
- `POST /memory/undo_last`

The high-level MCP tools are:

- `brain.remember`
- `brain.ingest_source`
- `brain.recall`
- `brain.profile_entity`
- `brain.list_open_loops`
- `brain.get_memory`
- `brain.get_source`
- `brain.resolve_conflict`
- `brain.forget`
- `brain.review_recent`
- `brain.undo_last`
- `brain.sync_cognee`
- `brain.rebuild_cognee`
- `brain.merge_entities`

Low-level Cognee and SQL operations are intentionally not exposed as public MCP
tools.

## Running The Slack Memory Agent

The Slack memory agent is a separate HTTP service. It does not serve `/mcp`, and
Slack paths should be routed to its own port:

```bash
make slack-agent
```

Routes:

- `GET /slack/healthz`
- `POST /slack/events`
- `POST /slack/commands`
- `POST /slack/interactions`

The agent verifies Slack signatures, timestamp freshness, team/channel/user
allowlists, and admin-only debug access before it touches Brain internals. Write
requests use the same role contracts in `src/memory_stack/agents/` that the
model eval harness tests, plus deterministic guardrails and a dry-run before
commit. By default, Slack writes require confirmation.

Supported Slack commands:

- `/brain remember <text>`
- `/brain recall <query>`
- `/brain profile <entity>`
- `/brain open-loops [topic]`
- `/brain get-memory <memory_id>`
- `/brain debug ...` for admin-only read-only inspection

Production should run this under launchd label `com.brain.slack-agent` on local
port `8003`; see `config/deployment/launchd/com.brain.slack-agent.plist.template`. Verify route
separation and fail-closed signature behavior with:

```bash
make slack-agent-check
```

## Running Tests

```bash
uv run ruff check src tests
uv run pytest
```

Unit tests use clean SQLite databases under `tmp_path`. They do not require live
network, live LLM calls, live Slack, or live Cognee.

Production deploys additionally run a pre-promotion live model smoke check. The
default scope is `active`, which makes tiny provider calls to the configured LLM
and embedding models from the new release before `current` is updated, launchd is
restarted, and app health checks can pass:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env \
  uv run python scripts/live_model_smoke.py --scope active
```

The equivalent Make target is:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make model-smoke
```

For statistical model-role evals, use the Brain eval CLI. Runtime defaults use
the configured LLM and embedding models; experiments can pass explicit
`provider:model` refs with `--models`.

```bash
uv run brain eval models \
  --fixture-set brain-model-test-v2 \
  --models openai:gpt-5.5 \
  --repeat-runs 1 \
  --output-json eval_runs/model_eval/results.json
```

For full end-to-end model checks, use the E2E model suite. It creates a fresh
SQLite Brain database, seeds it through the app service layer, retrieves runtime
facts/evidence, and calls the live configured model against the same shared role
contracts used by runtime. The suite covers every checked-in fine-grained role
spec, plus recall synthesis cases that use real runtime recall payloads.

```bash
uv run brain eval e2e-models \
  --model openai:gpt-5.5 \
  --output-json eval_runs/e2e_model/results.json
```

The pytest live E2E gate is opt-in because it makes provider calls:

```bash
BRAIN_RUN_LIVE_E2E_MODEL_TESTS=1 uv run pytest tests/test_e2e_model_suite.py -q
```

## Environment Variables

Core Brain settings:

- `BRAIN_DATABASE_URL=sqlite:///.data/brain/brain.db`
- `BRAIN_OWNER_NAME=Daniele`
- `BRAIN_LOG_LEVEL=INFO`
- `BRAIN_AUTH_ENABLED=false`
- `BRAIN_AUTH_TOKEN`

LLM compiler settings, disabled by default. When enabled, it uses the same fixed
runtime LLM as the rest of Brain: `openai:gpt-5.5`.

- `BRAIN_LLM_ENABLED=false`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`

Cognee projection settings, optional:

- `BRAIN_COGNEE_ENABLED=false`
- `BRAIN_COGNEE_RECALL_ENABLED=false`
- `BRAIN_COGNEE_MEMORY_DATASET=memory`
- `BRAIN_COGNEE_SOURCES_DATASET=sources`
- `BRAIN_COGNEE_DATA_DATASET=data`
- `BRAIN_COGNEE_RECALL_TOP_K=10`

Slack capture settings, optional:

- `BRAIN_SLACK_ENABLED=false`
- `BRAIN_SLACK_AGENT_ENABLED=false`
- `BRAIN_SLACK_AGENT_HOST=127.0.0.1`
- `BRAIN_SLACK_AGENT_PORT=8003`
- `BRAIN_SLACK_SIGNING_SECRET`
- `BRAIN_SLACK_BOT_TOKEN`
- `BRAIN_SLACK_ALLOWED_TEAM_IDS`
- `BRAIN_SLACK_ALLOWED_CHANNEL_IDS`
- `BRAIN_SLACK_ALLOWED_USER_IDS`
- `BRAIN_SLACK_ADMIN_USER_IDS`
- `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false`

Slack command handling is a thin optional layer over Brain service methods. It
does not bypass Brain DB.

## Profiles

Runtime uses one configured LLM and one configured embedding model. The default
production values are OpenAI `gpt-5.5` for LLM calls and
`fastembed:intfloat/multilingual-e5-large` with 1024-dimensional vectors for
local embeddings.

Provider API keys can be stored once and reused across every model for that
provider:

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
AWS_REGION=eu-west-2
AWS_BEARER_TOKEN_BEDROCK=...
GROQ_API_KEY=gsk_...
VOYAGE_API_KEY=...
```

`LLM_API_KEY` and `EMBEDDING_API_KEY` are still supported as role-specific
overrides. If they are unset, the active `LLM_PROVIDER` and
`EMBEDDING_PROVIDER` use the matching provider key, so benchmarking can switch
`LLM_MODEL` without duplicating credentials.

OpenAI text-model auth is provider-scoped and OAuth-first:

```env
OPENAI_AUTH_MODE=oauth
OPENAI_CODEX_AUTH_PROFILE=default
```

Sign in with:

```bash
uv run brain models auth login --provider openai-codex
```

Set `OPENAI_AUTH_MODE=api_key` to use `OPENAI_API_KEY` for OpenAI text calls.
OpenAI embeddings still require `OPENAI_API_KEY`; Codex OAuth is not used as an
embedding credential. Non-runtime providers are available only for explicit
eval/smoke experiments.
