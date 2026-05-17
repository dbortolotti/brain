# Brain

Brain is a local personal memory control plane exposed through a small MCP surface. Brain DB is the source of truth for memory identity, lifecycle, entity resolution, conflicts, open loops, and Cognee sync state. Cognee is an optional semantic projection that can be rebuilt from Brain DB.

## Documentation

- [User Guide](docs/USER_GUIDE.md) - end-user guidance for saving and recalling memories through Slack or an LLM.
- [API Setup Guide](docs/API_SETUP_GUIDE.md) - HTTP, MCP, auth, client setup, and integration examples.
- [Slack Setup Guide](docs/SLACK_SETUP.md) - Slack app configuration, routes, allowlists, and troubleshooting.
- [Backup Scheme](docs/BACKUP_SCHEME.md) - backup contents, verification, Google Drive replication, and restore outline.
- [Production Secrets](docs/production-secrets.md) - staging/prod release flow, secret, and variable handling.
- [Runtime Flow Diagrams](docs/role_flow_diagram.md) - current runtime flow and model-role topology notes.

## Local Dev Setup

```bash
cp .env.openai.example .env
make setup
make check
uv run pytest
```

If you need the local compose stack:

```bash
make up
make down
```

By default Brain uses SQLite at `sqlite:///.data/brain/brain.db`. The store also creates the schema automatically for local tests and dev, and Alembic migrations are available for production-controlled setup:

```bash
uv run alembic upgrade head
```

## Running The MCP Server

```bash
make mcp-http
```

Equivalent command:

```bash
uv run python -m memory_stack.mcp_server
```

Selected user-facing HTTP endpoints include:

- `GET /healthz`
- `GET /`, `GET /app`, and `GET /user` for the Brain user dashboard
- `GET /admin` for the root/admin dashboard view
- `GET /auth/session` and `GET /api/session` for the web session endpoint
- `POST /login` and `POST /logout`
- `PUT /account/password`
- `GET|POST /mcp` for the curated user/app MCP surface
- `GET|POST /admin/mcp` for the full admin MCP surface
- `GET|POST /app/mcp` for the legacy ChatGPT App MCP alias
- `GET /cognee` and `GET /admin/cognee` for Cognee UI entry points
- `GET|POST /ui` and `GET|POST /ui-api/{path:path}` compatibility aliases
- `GET /docs`, `GET /redoc`, and `GET /openapi.json`
- `GET /privacy`, `GET /terms`, and `GET /support`
- `GET /datasources`, `POST /datasources`, and `DELETE /datasources/{datasource}`
- `POST /memory/remember`
- `POST /memory/ingest_source`
- `POST /memory/recall`
- `POST /memory/profile_entity`
- `GET /memory/open_loops`
- `GET /memory/{memory_id}`
- `POST /memory/forget`
- `POST /memory/resolve_conflict`
- `POST /memory/review_recent`
- `POST /memory/undo_last`
- `POST /memory/sync_cognee`
- `POST /memory/rebuild_cognee`
- `POST /memory/merge_entities`

The high-level MCP tools are grouped by purpose:

Core memory:

- `brain_remember`
- `brain_ingest_source`
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_get_source`
- `brain_resolve_conflict`
- `brain_forget`
- `brain_review_recent`
- `brain_undo_last`
- `brain_merge_entities`

Session and profile context:

- `brain_session`
- `brain_profile_context_remember`
- `brain_profile_context_list`
- `brain_profile_context_forget`
- `brain_profile_context_sync`

Agent memory:

- `brain_agent_memory`
- `brain_agent_memory_recall`
- `brain_agent_memory_clear`

Palate:

- `brain_palate_describe_item`
- `brain_palate_remember`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_log_decision`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`
- `brain_palate_refresh_enrichment`

Curated Cognee/admin operations:

- `brain_sync_cognee`
- `brain_rebuild_cognee`
- `cognee_improve`

Raw SQL and arbitrary Cognee primitives are intentionally not exposed as public MCP tools. Brain exposes curated Cognee/admin operations such as sync, rebuild, and configured improve.

## ChatGPT App Surface

Brain exposes a curated MCP surface for a ChatGPT App and user-facing clients at `/mcp`, with the public URL `https://brain.dceb.net/mcp`. `/app/mcp` remains a legacy alias. The root dashboard is available at `https://brain.dceb.net/` and uses the same curated surface through a browser session cookie. Browser users sign in with user id and password; the dashboard does not store OAuth bearer tokens in local storage.

The ChatGPT App surface intentionally lists only user-safe tools:

- `brain_session`
- `brain_remember`
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_undo_last`
- `brain_profile_context_list`
- `brain_profile_context_remember`
- `brain_profile_context_forget`
- `brain_app_data_controls`

Admin, raw projection, hard-delete, agent-memory-clear, and Palate write tools remain on the internal `/admin/mcp` surface only. On `/mcp`, `brain_remember` previews by default; a client may save only after explicit user confirmation by calling it with `context.confirmed_by_user=true`. App-surface write tools accept either top-level `confirmed_by_user=true` or `context.confirmed_by_user=true`. Read tools advertise `brain.memory.read`; write tools advertise `brain.memory.read brain.memory.write`, are rate-limited, and append a redacted audit record visible in the dashboard Data Controls tab. Destructive app-surface calls such as `brain_undo_last` and `brain_profile_context_forget` require confirmation.

Browser dashboard auth is separate from MCP client auth. `/login` verifies a user-registry password, creates an opaque server-side session, and sets a `Secure`, `HttpOnly`, `SameSite=Lax` cookie. Mutating dashboard requests must include the per-session CSRF token returned by `/auth/session`. MCP clients still use OAuth bearer tokens.

The Cognee UI proxy also uses Brain user/password login. Regular users enter through `/cognee`; root users can use `/admin/cognee` for system-level Cognee inspection. The older `/ui` and `/ui-api` routes are compatibility aliases.

Public app support pages:

- `https://brain.dceb.net/privacy`
- `https://brain.dceb.net/terms`
- `https://brain.dceb.net/support`

See `docs/chatgpt-app-hardening.md` for the app review hardening model and the post-merge production verification checklist.

## Running The Slack Memory Agent

The Slack memory agent is a separate HTTP service. It does not serve `/mcp`, and Slack paths should be routed to its own port:

```bash
make slack-agent
```

Equivalent command:

```bash
uv run python -m memory_stack.slack_agent_server
```

Routes:

- `GET /slack/healthz`
- `POST /slack/events`
- `POST /slack/commands`
- `POST /slack/interactions`

The agent verifies Slack signatures, timestamp freshness, team/channel/user allowlists, and admin-only debug access before it touches Brain internals. Write requests use the same role contracts in `src/memory_stack/agents/` that the model eval harness tests, plus deterministic guardrails and a dry-run before commit. By default, Slack writes require confirmation.

Supported Slack commands:

- `/brain remember <text>`
- `/brain recall <query>`
- `/brain profile <entity>`
- `/brain open-loops [topic]`
- `/brain get-memory <memory_id>`
- `/brain debug ...` for admin-only read-only inspection

Production should run this under launchd label `com.brain.slack-agent` on local port `8003`; see `deployment/launchd/com.brain.slack-agent.plist.template`. Verify route separation and fail-closed signature behavior with:

```bash
make slack-agent-check
```

## Deployment and Release Model

Brain deploys on the self-hosted `brain-prod` runner in three environment tiers:

- `dev`: local developer runs.
- `staging`: `main` deploys through `.github/workflows/deploy-local-staging.yml` to `/Volumes/xpg_usb4/staging/brain`.
- `prod`: manual release promotion runs through `.github/workflows/release.yml` and deploys the currently staged release version to `/Volumes/xpg_usb4/prod/brain`.

`.github/workflows/deploy-local-production.yml` remains available as a manual production deploy escape hatch. It is not triggered by pushes to `main`.

The workflows render each environment's `shared/secrets/brain.env` from GitHub Secrets and GitHub Variables before running `scripts/deploy-local-production.sh` with `BRAIN_DEPLOY_ENV=staging` or `BRAIN_DEPLOY_ENV=prod`.

Workflow model:

- `.github/workflows/deploy-local-staging.yml` triggers on `push` to `main` and on `workflow_dispatch`, and accepts optional `version` and `force_config_override` inputs.
- `.github/workflows/release.yml` is manual only, requires a previously staged `version`, and also accepts `force_config_override`.
- `.github/workflows/deploy-local-production.yml` is manual only and accepts `force_config_override`.
- `.github/workflows/validate.yml` runs on `pull_request` and `workflow_dispatch`.

## Release Versioning

Every deploy writes runtime release metadata into:

```text
/Volumes/xpg_usb4/{staging|prod}/brain/current/release.json
/Volumes/xpg_usb4/{staging|prod}/brain/shared/release.json
/Volumes/xpg_usb4/{staging|prod}/brain/shared/current-version
```

Normal pushes to `main` deploy staging with an automatic build version such as `staging-1a2b3c4d5e6f`. To create a promotable release, manually run the staging workflow with a version like `v2.1.0` or `v2.1.0-rc.1`. That staged workflow deploys the SHA, records `BRAIN_RELEASE_VERSION`, and creates the annotated git tag at the staged SHA.

Production promotion does not mint a new version. The release workflow reads staging `shared/release.json`, verifies the requested version is the active staged version, verifies the git tag already exists at that exact SHA, then deploys production with the same `BRAIN_RELEASE_VERSION`.

## Conflict Rule

The renderer compares three files:

```text
proposed: newly rendered GitHub Secrets/Vars config
live:     /Volumes/xpg_usb4/{staging|prod}/brain/shared/secrets/brain.env
base:     /Volumes/xpg_usb4/{staging|prod}/brain/shared/secrets/brain.env.last-deployed
```

For each non-metadata key:

```text
if proposed == live:
  no change
elif live == base:
  live has not been manually edited; overwrite with proposed
else:
  fail deploy
```

After a successful render, both `brain.env` and `brain.env.last-deployed` are updated to the proposed config.

The GitHub Actions staging, production, and release workflows expose `force_config_override` only as an explicit manual-dispatch option, and it defaults to `false`. Normal push deploys and manual deploys without that option enabled use the conflict rule above.

Use `force_config_override=true` only for an intentional bootstrap or re-baseline. Otherwise, resolve a conflict by propagating the live change back to GitHub Secrets/Variables or by intentionally reconciling the environment back to the last deployed baseline before redeploying.

## Live Model Smoke and Operational Checks

After deployment, staging and production run `scripts/live_model_smoke.py` against the configured live model scope. By default this is `active`, which calls the active `LLM_PROVIDER`/`LLM_MODEL` and `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL` with tiny requests. Set repository variable `BRAIN_MODEL_SMOKE_SCOPE` to `active` or `none` to control deploys.

The Make target mirrors the active smoke run and writes `eval_runs/live_model_smoke_active.json` by default:

```bash
make model-smoke
```

Equivalent command:

```bash
uv run python scripts/live_model_smoke.py --scope active --json-output eval_runs/live_model_smoke_active.json
```

Useful production checks:

```bash
make prod-check
make ui-prod-check
make slack-agent-check
make cloudflare-verify
```

Operational maintenance targets:

```bash
make mcp-config
make palate-probe
make backup
make reset
make reset-hard
```

Use `make reset-hard` only when you intend to delete the local stores.

## Running Tests

```bash
make lint
make test
```

Equivalent commands:

```bash
uv run ruff check src tests
uv run pytest
```

Unit tests use clean SQLite databases under `tmp_path`. They do not require live network, live LLM calls, live Slack, or live Cognee.

## Docs Automation

Documentation has a deterministic source-of-truth check plus a manual LLM refresh path:

```bash
make docs-generate  # refresh docs/generated/facts.json
make docs-check     # fail if facts or managed docs are stale
make docs-llm       # manually rewrite managed docs with the configured LLM
make docs-hash      # refresh source hashes after manual doc review
```

The validate workflow and the deploy workflows run `make docs-check`. The LLM rewrite hook is manual so normal commits and deploys do not depend on network availability or model credentials.

For statistical model-role evals, use the Brain eval Make targets. The default target writes `eval_runs/brain-golden.json`:

```bash
make brain-eval
```

For targeted fine-grained evals, use:

```bash
make targeted-fine-grained-eval
```

For full end-to-end model checks, use the E2E model suite. It creates a fresh SQLite Brain database, seeds it through the app service layer, retrieves runtime facts/evidence, and calls the live configured model against the same shared role contracts used by runtime. The suite covers every checked-in fine-grained role spec, plus recall synthesis cases that use real runtime recall payloads.

```bash
uv run brain eval e2e-models --model openai:gpt-5.5 --output-json eval_runs/e2e_model/results.json
```

The pytest live E2E gate is opt-in because it makes provider calls:

```bash
BRAIN_RUN_LIVE_E2E_MODEL_TESTS=1 uv run pytest tests/test_e2e_model_suite.py -q
```

For live staging acceptance, use the staging E2E suite. It creates or updates the
dedicated `brain-e2e` user, signs in through the cookie/CSRF UI auth path, primes
staging organically through MCP tool calls, confirms Palate proposals, checks
user isolation, and scores usage results with `gpt-5.5` high reasoning.

```bash
ENV_FILE=/Volumes/xpg_usb4/staging/brain/shared/secrets/brain.env \
  uv run python scripts/staging_e2e_suite.py
```

The default target is the local staging service at `http://127.0.0.1:18100`,
which avoids public proxy routing for admin user-management APIs.

The runner writes JSON reports under `.reports/staging-e2e/` by default. It is
not part of normal `pytest` because it mutates staging and makes live provider
calls.

## Environment Variables

Deployment, routing, and auth-related settings worth calling out:

- `BRAIN_APP_MCP_PATH=/app/mcp`
- `BRAIN_ADMIN_MCP_PATH=/admin/mcp`
- `BRAIN_PUBLIC_BASE_URL`
- `BRAIN_PUBLIC_MCP_PATH`
- `BRAIN_PUBLIC_ADMIN_MCP_PATH`
- `BRAIN_PUBLIC_APP_MCP_PATH`
- `BRAIN_PUBLIC_UI_PATH`
- `BRAIN_PUBLIC_UI_API_PATH`
- `BRAIN_RELEASE_ENV`
- `BRAIN_RELEASE_SHA`
- `BRAIN_RELEASE_VERSION`
- `BRAIN_AUTH_PASSWORD_FILE`
- `BRAIN_AUTH_STATE_PATH`
- `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`
- `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`
- `BRAIN_AUTH_REQUIRE_PKCE`
- `BRAIN_AUTH_SCOPES`
- `BRAIN_APP_WRITE_RATE_LIMIT_COUNT`
- `BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS`
- `BRAIN_COGNEE_PALATE_DATASET`
- `BRAIN_TASTE_CANONICAL_STORE`

Core Brain settings:

- `BRAIN_DATABASE_URL=sqlite:///.data/brain/brain.db`
- `BRAIN_USER_ID=default`
- `BRAIN_OWNER_NAME=Daniele`
- `BRAIN_LOG_LEVEL=INFO`
- `BRAIN_AUTH_ENABLED=false`
- `BRAIN_AUTH_TOKEN`

Brain data is scoped by `BRAIN_USER_ID`. OAuth deployments must set `BRAIN_AUTH_USERS_FILE` to a JSON user registry; issued OAuth tokens carry a `user_id`, and Brain filters memory, profile context, Palate records, audit logs, and recall data to that user. Superusers are marked with `superuser: true` or configured through `BRAIN_AUTH_SUPERUSER_IDS`; they can manage users from the dashboard User Admin tab. Use `scripts/migrate_default_user_to_daniele.py` for the one-time migration from the original single-user `default` owner to `daniele` plus a separate `default` root user.

Production auth also relies on `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_REQUIRE_PKCE`, and `BRAIN_AUTH_SCOPES`.

LLM compiler settings, disabled by default. When enabled, it uses the same fixed runtime LLM as the rest of Brain/Cognee: `openai:gpt-5.4-mini`.

- `BRAIN_LLM_ENABLED=false`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`

Taste/palate input enrichment uses its own model setting so it can stay on a stronger model without changing Cognee projection defaults:

- `BRAIN_TASTE_LLM_MODEL=gpt-5.5`
- `BRAIN_TASTE_LLM_REASONING_EFFORT=medium`

Cognee projection settings:

- `BRAIN_COGNEE_ENABLED=true`
- `BRAIN_COGNEE_RECALL_ENABLED=false`
- `BRAIN_COGNEE_MEMORY_DATASET=memory`
- `BRAIN_COGNEE_SOURCES_DATASET=sources`
- `BRAIN_COGNEE_DATA_DATASET=data`
- `BRAIN_COGNEE_AGENT_MEMORY_DATASET=agent_memory`
- `BRAIN_AGENT_MEMORY_SESSION_ID=portable_agent_session`
- `BRAIN_COGNEE_RECALL_TOP_K=10`
- `GRAPH_DATABASE_PROVIDER=ladybug`
- `VECTOR_DB_PROVIDER=pgvector`
- `VECTOR_DATASET_DATABASE_HANDLER=pgvector`
- `DB_PROVIDER=postgres`
- `ENABLE_BACKEND_ACCESS_CONTROL=false`

`BRAIN_AGENT_MEMORY_SESSION_ID` and `BRAIN_COGNEE_AGENT_MEMORY_DATASET` are base names. At runtime, authenticated users receive a derived session id and Cognee agent-memory dataset scoped to their Brain user id, so one user cannot recall or improve another user's chat-session memory.

Brain defaults Cognee's rebuildable projection to Postgres/pgvector for vector storage and Postgres for Cognee metadata. The configured Postgres role must be able to create the `vector` extension; with Cognee's pgvector dataset handler it also needs permission to create per-dataset databases.

Brain Taste settings:

- `BRAIN_TASTE_ENABLED=true`
- `BRAIN_TASTE_LLM_ROUTING_ENABLED=false`
- `BRAIN_TASTE_AUTO_ENRICH_ENABLED=true`
- `BRAIN_TASTE_OMDB_API_KEY`
- `BRAIN_TASTE_WEB_ENRICHMENT_ENABLED=true`
- `BRAIN_TASTE_GOOGLE_PLACES_API_KEY`
- `BRAIN_TASTE_AUTO_WRITE_THRESHOLD=0.95`
- `BRAIN_TASTE_CONFIRMATION_THRESHOLD=0.70`
- `BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD=0.97`
- `BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD=0.80`
- `BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS=24`

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

Slack command handling is a thin optional layer over Brain service methods. It does not bypass Brain DB.

## Profiles

Runtime uses one configured LLM and one configured embedding model. The checked-in defaults are OpenAI `gpt-5.4-mini` for runtime/Cognee LLM calls and OpenAI `text-embedding-3-large` with 3072-dimensional vectors for embeddings.

Environment examples differ by local setup:

- `.env.example` mirrors `cfg/common.yaml`: Postgres Cognee metadata, pgvector vectors, and the default graph provider.
- `.env.openai.example` is a smaller local/OpenAI-oriented example using Neo4j, LanceDB, and SQLite.
- `cfg/staging.yaml` is the staging override deployed from `main`.
- `cfg/prod.yaml` is the production override promoted by the release workflow. Promotable releases are versioned in staging first; production verifies and keeps that staged `BRAIN_RELEASE_VERSION` instead of creating a new version at promotion time.

Provider API keys can be stored once and reused across every model for that provider:

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

`LLM_API_KEY` and `EMBEDDING_API_KEY` are still supported as role-specific overrides. If they are unset, the active `LLM_PROVIDER` and `EMBEDDING_PROVIDER` use the matching provider key, so benchmarking can switch `LLM_MODEL` without duplicating credentials.

OpenAI text-model auth is provider-scoped and OAuth-first:

```env
OPENAI_AUTH_MODE=oauth
OPENAI_CODEX_AUTH_PROFILE=default
```

Sign in with:

```bash
uv run brain models auth login --provider openai-codex
```

Set `OPENAI_AUTH_MODE=api_key` to use `OPENAI_API_KEY` for OpenAI text calls. When `OPENAI_AUTH_MODE=oauth` and `EMBEDDING_PROVIDER=openai`, Brain's Cognee OAuth compatibility layer also passes the refreshed OAuth bearer as the OpenAI embedding credential. Use API-key mode when you want embeddings to use `OPENAI_API_KEY` explicitly. Non-runtime providers are available only for explicit eval/smoke experiments.

<!-- brain-doc-source-hash: 1a03c8505d2c3d0554cadd8a6850c894416b3c440e20eea352a5cc7418bbaa7c -->
