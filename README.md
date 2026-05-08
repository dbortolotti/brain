# Brain

Brain is a local personal memory control plane exposed through a small MCP
surface. Brain DB is the source of truth for memory identity, lifecycle, entity
resolution, conflicts, open loops, and Cognee sync state. Cognee is an optional
semantic projection that can be rebuilt from Brain DB.

## Local Dev Setup

```bash
cp .env.gemini.example .env
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
requests go through `config/slack_memory_agent_rules.md`, a structured proposal
contract, deterministic guardrails, and a dry-run before commit. By default,
Slack writes require confirmation.

Supported Slack commands:

- `/brain remember <text>`
- `/brain recall <query>`
- `/brain profile <entity>`
- `/brain open-loops [topic]`
- `/brain get-memory <memory_id>`
- `/brain debug ...` for admin-only read-only inspection

Production should run this under launchd label `com.brain.slack-agent` on local
port `8003`; see `launchd/com.brain.slack-agent.plist.template`. Verify route
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

Production deploys additionally run a live model smoke check. The default scope
is `active`, which makes tiny provider calls to the configured LLM and embedding
models after the app health checks pass:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env \
  uv run python scripts/live_model_smoke.py --scope active
```

Use `--scope core`, `--scope enabled`, or `--scope all` for registry-wide checks.
Judge-only models are excluded unless `--include-judge` is set.

To run one tiny live probe against every unique non-skipped model declared in
`brain_model_registry.yaml`, including disabled and judge-only entries:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env \
  uv run python scripts/live_model_smoke.py \
    --all-registry \
    --json-output eval_runs/live_model_smoke_all.json
```

The equivalent Make target is:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make model-smoke-all
```

For statistical model-role evals, use the Brain eval CLI. It writes one JSONL
record per model/role/fixture/repeat, plus an optional Markdown report with
bootstrap confidence intervals, cost, latency, zero-tolerance failures, and
pairwise model comparisons:

```bash
uv run brain eval models \
  --registry brain_model_registry.yaml \
  --fixture-set production \
  --roles slack_intake,memory_compiler,entity_resolution,conflict_classifier,recall_synthesizer \
  --model-set model-test-initial \
  --bootstrap-samples 5000 \
  --max-workers 4 \
  --output eval_runs/prod_$(date +%Y%m%d_%H%M%S).jsonl \
  --report-md eval_reports/model_eval_$(date +%Y%m%d_%H%M%S).md
```

## Environment Variables

Core Brain settings:

- `BRAIN_DATABASE_URL=sqlite:///.data/brain/brain.db`
- `BRAIN_OWNER_NAME=Daniele`
- `BRAIN_LOG_LEVEL=INFO`
- `BRAIN_AUTH_ENABLED=false`
- `BRAIN_AUTH_TOKEN`

LLM compiler settings, disabled by default:

- `BRAIN_LLM_ENABLED=false`
- `BRAIN_LLM_PROVIDER`
- `BRAIN_LLM_MODEL`
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
- `BRAIN_SLACK_RULES_PATH=./config/slack_memory_agent_rules.md`
- `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false`

Slack command handling is a thin optional layer over Brain service methods. It
does not bypass Brain DB.

## Profiles

Profiles are selected through `PROFILE` and provider-specific environment
variables:

- `gemini` for the Google lane
- `openai` for the OpenAI lane; text calls default to OpenAI Codex OAuth
- `local` for Ollama/Fastembed no-cloud use

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
embedding credential. Other providers keep their existing API-key or cloud
credential settings.

## Legacy Cognee Eval Tools

The old Cognee-first scripts are retained for compatibility and are marked as
legacy. New work should use the Brain eval harness under
`src/memory_stack/evals/`.
