# Brain

Brain is a local personal memory control plane exposed through a small MCP surface. Brain DB is the source of truth for memory identity, lifecycle, entity resolution, conflicts, open loops, and Cognee sync state. Cognee is an optional semantic projection that can be rebuilt from Brain DB.

## Documentation

- [User Guide](docs/USER_GUIDE.md) - end-user guidance for saving and recalling memories through Slack or an LLM.
- [API Setup Guide](docs/API_SETUP_GUIDE.md) - HTTP, MCP, auth, client setup, and integration examples.
- [Slack Setup Guide](docs/SLACK_SETUP.md) - Slack app configuration, routes, allowlists, and troubleshooting.
- [Backup Scheme](docs/BACKUP_SCHEME.md) - backup contents, verification, Google Drive replication, and restore outline.
- [Production Secrets](docs/production-secrets.md) - staging, prod, and release flow, secret handling, and config conflict rules.
- [ChatGPT App Hardening](docs/chatgpt-app-hardening.md) - app review hardening model and post-merge production verification checklist.
- [OpenAI Submission Checklist](docs/openai-submission.md) - remaining non-code checklist for ChatGPT App review.
- [Runtime Flow Diagrams](docs/role_flow_diagram.md) - current runtime flow and model-role topology notes.

## Local Dev Setup

```bash
cp .env.example .env
make setup
make check
uv run pytest
```

If you want the smaller local/OpenAI-oriented example, use `.env.openai.example` instead of `.env.example`.

If you need the local compose stack:

```bash
make up
make down
```

By default Brain uses SQLite at `sqlite:///.data/brain/brain.db`. For controlled schema setup, run:

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
- `GET /app-assets/{asset_name}` and `GET /app/oauth/callback`
- `GET /auth/session` and `GET /api/session` for the web session endpoint
- `POST /login` and `POST /logout`
- `PUT /account/password`
- `GET|POST /authorize`
- `POST /register`
- `POST /token`
- `POST /revoke`
- `GET /.well-known/oauth-authorization-server`
- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-protected-resource/{resource_path:path}`
- `GET /.well-known/openai-apps-challenge` when `BRAIN_OPENAI_APPS_CHALLENGE_TOKEN` is configured for OpenAI domain verification
- `GET /admin/users`, `POST /admin/users`, `PUT /admin/users/{user_id}`, and `DELETE /admin/users/{user_id}`
- `GET|POST /mcp` for the curated user/app MCP surface
- `GET|POST /admin/mcp` for the full admin MCP surface
- `GET|POST /app/mcp` for the legacy ChatGPT App MCP alias
- `GET /docs`, `GET /docs/oauth2-redirect`, `GET /redoc`, and `GET /openapi.json`
- `GET /favicon.ico`, `GET /icon.png`, and `GET /apple-touch-icon.png`
- `GET /privacy`, `GET /terms`, and `GET /support`
- `GET /datasources`, `POST /datasources`, and `DELETE /datasources/{datasource}`
- `POST /create_datasource`
- `GET /list_datasources`
- `POST /delete_datasource`
- `DELETE /delete_datasource/{datasource}`
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

The high-level MCP tools are grouped by surface:

Public ChatGPT App surface:

- `brain_session`
- `brain_remember`
- `brain_profile_context_remember`
- `brain_profile_context_list`
- `brain_profile_context_forget`
- `brain_app_data_controls`
- `brain_ingest_source`
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_undo_last`
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

Internal admin surface:

- `brain_session`
- `brain_app_open_review_panel`
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
- `brain_profile_context_remember`
- `brain_profile_context_list`
- `brain_profile_context_forget`
- `brain_profile_context_sync`
- `brain_app_data_controls`
- `brain_sync_cognee`
- `brain_rebuild_cognee`
- `cognee_improve`
- `brain_agent_memory`
- `brain_agent_memory_recall`
- `brain_agent_memory_clear`
- `brain_merge_entities`
- `brain_palate_describe_item`
- `brain_palate_remember`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_log_decision`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`
- `brain_palate_refresh_enrichment`

Raw SQL and arbitrary Cognee primitives are intentionally not exposed as public MCP tools. Brain exposes curated Cognee/admin operations such as sync, rebuild, and configured improve.

## Running The Cognee UI Proxy

The Cognee UI proxy is a separate HTTP service. It does not serve `/mcp`, and UI paths should be routed to its own port. The proxy owns the `/cognee`, `/admin/cognee`, `/ui`, `/ui-api`, `/cognee-api`, `/ui-login`, `/ui-logout`, `/cognee-login`, and `/cognee-logout` surfaces.

```bash
make ui-proxy
```

Equivalent command:

```bash
uv run python -m uvicorn memory_stack.ui_proxy:app --host 127.0.0.1 --port 8002
```

Routes include:

- `GET /cognee`
- `GET|POST|PUT|PATCH|DELETE /cognee/{path:path}`
- `GET|POST|PUT|PATCH|DELETE /cognee-api/{path:path}`
- `GET /admin/cognee`
- `GET|POST|PUT|PATCH|DELETE /admin/cognee/{path:path}`
- `GET|POST|PUT|PATCH|DELETE /admin/cognee-api/{path:path}`
- `GET /ui`
- `GET|POST|PUT|PATCH|DELETE /ui/{path:path}`
- `GET|POST|PUT|PATCH|DELETE /ui-api/{path:path}`
- `GET|POST /ui-login`
- `POST /ui-logout`
- `GET|POST /cognee-login`
- `POST /cognee-logout`

The proxy also serves `GET /healthz`, `GET /docs`, `GET /redoc`, `GET /openapi.json`, `GET /favicon.ico`, `GET /icon.png`, `GET /apple-touch-icon.png`, and the frontend root routes.

## ChatGPT App Surface

Brain exposes a curated MCP surface for a ChatGPT App and user-facing clients at the configured public base URL together with `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_APP_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`. `/app/mcp` remains a legacy alias. The root dashboard uses the same curated surface through a browser session. Browser users sign in with user id and password; the dashboard uses its own session and CSRF flow rather than bearer tokens.

The ChatGPT App surface intentionally lists only user-safe tools:

- `brain_session`
- `brain_remember`
- `brain_profile_context_remember`
- `brain_profile_context_list`
- `brain_profile_context_forget`
- `brain_app_data_controls`
- `brain_ingest_source`
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_undo_last`
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

Admin, raw projection, hard-delete, profile-context-sync, agent-memory-clear, and Palate write tools remain on the internal `/admin/mcp` surface only. On `/mcp`, read tools advertise `brain.memory.read`; write tools advertise `brain.memory.read brain.memory.write`, are rate-limited, and destructive app-surface calls such as `brain_undo_last` and `brain_profile_context_forget` require confirmation.

Browser dashboard auth is separate from MCP client auth. `/login` verifies a user-registry password, creates an opaque server-side session, and sets a cookie. Mutating dashboard requests must include the per-session CSRF token returned by `/auth/session`. MCP clients still use OAuth bearer tokens.

User-registry passwords are stored as Argon2id hashes. Legacy plaintext user records are accepted for migration only; a successful login migrates that user, and operators can migrate and check the full registry with:

```bash
uv run python scripts/migrate_auth_user_passwords.py --env-file /path/to/brain.env
uv run python scripts/migrate_auth_user_passwords.py --env-file /path/to/brain.env --check
```

The Cognee UI proxy also uses Brain user/password login. Regular users enter through `/cognee`; superusers can use `/admin/cognee` for system-level Cognee inspection. The older `/ui` and `/ui-api` routes, plus `/cognee-api`, `/cognee-login`, `/cognee-logout`, `/ui-login`, and `/ui-logout`, are compatibility aliases.

Public app support pages:

- `/privacy`
- `/terms`
- `/support`

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

The agent verifies Slack signatures, timestamp freshness, team, channel, and user allowlists, and admin-only debug access before it touches Brain internals. By default, Slack writes require confirmation.

Supported Slack commands:

- `/brain remember <text>`
- `/brain recall <query>`
- `/brain profile <entity>`
- `/brain open-loops [topic]`
- `/brain get-memory <memory_id>`
- `/brain debug ...` for admin-only read-only inspection

The agent listens on local port `8003` by default; see `BRAIN_SLACK_AGENT_PORT=8003`. Verify route separation and fail-closed signature behavior with:

```bash
make slack-agent-check
```

## Deployment and Release Model

Brain deploys on the self-hosted `brain-prod` runner in three environment tiers:

- `dev`: local developer runs.
- `staging`: `main` deploys through `.github/workflows/deploy-local-staging.yml` to `/Volumes/xpg_usb4/staging/brain`. That workflow can also be run manually; its `version` input is optional, and if omitted it deploys a `staging-<12-char-sha>` build version.
- `prod`: manual release promotion runs through `.github/workflows/release.yml` and deploys the currently staged release version to `/Volumes/xpg_usb4/prod/brain`.

`.github/workflows/deploy-local-production.yml` remains available as a manual production deploy escape hatch. It is not triggered by pushes to `main`; its workflow-dispatch run resolves a `prod-<12-char-sha>` build version.

The workflows render each environment's `shared/secrets/brain.env` from GitHub Secrets and GitHub Variables with `scripts/render_prod_env.py`, then run `scripts/deploy-local-production.sh` with `BRAIN_DEPLOY_ENV=staging` or `BRAIN_DEPLOY_ENV=prod`. They also set `BRAIN_MCP_PATH=/mcp`, `BRAIN_ADMIN_MCP_PATH=/admin/mcp`, `BRAIN_APP_MCP_PATH=/app/mcp`, `BRAIN_PUBLIC_MCP_PATH=/mcp`, `BRAIN_PUBLIC_ADMIN_MCP_PATH=/admin/mcp`, `BRAIN_PUBLIC_APP_MCP_PATH=/mcp`, `BRAIN_PUBLIC_UI_PATH=/cognee`, and `BRAIN_PUBLIC_UI_API_PATH=/cognee-api`.

Workflow model:

- `.github/workflows/deploy-local-staging.yml` triggers on `push` to `main` and on `workflow_dispatch`, and accepts optional `version` and `force_config_override` inputs.
- `.github/workflows/release.yml` is manual only, requires a previously staged `version`, and also accepts `force_config_override`.
- `.github/workflows/deploy-local-production.yml` is manual only and accepts `force_config_override`.
- `.github/workflows/validate.yml` runs on `pull_request` and `workflow_dispatch`.

The Makefile also exposes `make deploy-local-production` as a manual production deploy helper:

```bash
make deploy-local-production
```

Equivalent command:

```bash
./scripts/deploy-local-production.sh
```

Deployments also configure `BRAIN_AUTH_USERS_FILE` under `shared/secrets/brain-auth-users.json` and `BRAIN_AUTH_SUPERUSER_IDS` in the deployed config. Auth-enabled Brain instances fail closed when the configured registry is missing, and superusers can manage users from the dashboard User Admin tab without restarting the service.

GitHub Secrets and GitHub Variables are the source of truth; direct emergency edits to live config must be propagated back before the next deploy.

## Release Versioning

Every deploy writes runtime release metadata into:

```text
/Volumes/xpg_usb4/{staging|prod}/brain/current/release.json
/Volumes/xpg_usb4/{staging|prod}/brain/shared/release.json
/Volumes/xpg_usb4/{staging|prod}/brain/shared/current-version
```

The release metadata records the app name, environment, version, SHA, deployment directory, deploy time, and source. The source is `github-actions` for workflow runs and `local` for local runs.

Normal pushes to `main` deploy staging with an automatic build version such as `staging-1a2b3c4d5e6f`. To create a promotable release, manually run the staging workflow with a version like `v2.1.0` or `v2.1.0-rc.1`. If you omit the version on a manual staging run, it falls back to `staging-<12-char-sha>`. That staged workflow deploys the SHA, records `BRAIN_RELEASE_VERSION`, and creates the annotated git tag at the staged SHA when the version starts with `v`. If the tag already exists at a different SHA, the staging run fails instead of retagging.

Production promotion does not mint a new version. The release workflow reads staging `shared/release.json`, verifies the requested version is the active staged version, verifies the git tag already exists at that exact SHA, checks that the staging `current` symlink points at the same commit, and then deploys production with the same `BRAIN_RELEASE_VERSION`.

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

The renderer ignores metadata keys when it compares configs. The metadata set includes:

```text
BRAIN_CONFIG_RENDER_SHA
BRAIN_CONFIG_RENDERED_AT
BRAIN_CONFIG_RENDER_SOURCE
BRAIN_RELEASE_ENV
BRAIN_RELEASE_SHA
BRAIN_RELEASE_VERSION
```

After a successful render, both `brain.env` and `brain.env.last-deployed` are updated to the proposed config.

`force_config_override=true` bypasses the three-way conflict check and establishes a new baseline. Use it only for an intentional bootstrap or re-baseline. Otherwise, resolve a conflict by propagating the live change back to GitHub Secrets/Variables or by intentionally reconciling the environment back to the last deployed baseline before redeploying.

`BRAIN_AUTH_PASSWORD` is handled similarly, but it is written to the environment's `shared/secrets/brain-auth-password` with a matching `brain-auth-password.last-deployed` snapshot.

## Live Model Smoke and Operational Checks

Use `scripts/live_model_smoke.py` against the configured live model scope. The Make target mirrors the active smoke run and writes `eval_runs/live_model_smoke_active.json` by default:

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

`cloudflare-verify` checks DNS/TLS, public curated and admin MCP URLs, dashboard, privacy, terms, support, browser security headers, OAuth metadata, ChatGPT App tool descriptors, and the authenticated public app MCP surface when auth is enabled. It also confirms the public app surface remains text-only. For authenticated checks against hashed user registries, set `BRAIN_VERIFIER_USER_ID` and `BRAIN_VERIFIER_PASSWORD_FILE` or `BRAIN_AUTH_VERIFIER_USER_ID` and `BRAIN_AUTH_VERIFIER_PASSWORD_FILE`.

Operational maintenance targets:

```bash
make mcp-config
make palate-probe
make backup
make reset
make reset-hard
make agent-memory
make maintenance
```

Use `make reset-hard` only when you intend to delete the local stores.

## Running Tests

```bash
make lint
make test
```

Equivalent commands:

```bash
uv run ruff check .
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

For full end-to-end model checks, use the E2E model suite. It creates a fresh SQLite Brain database, seeds it through the app service layer, retrieves runtime facts and evidence, and calls the live configured model against the same shared role contracts used by runtime. The suite covers every checked-in fine-grained role spec, plus recall synthesis cases that use real runtime recall payloads.

```bash
uv run brain eval e2e-models --model openai:gpt-5.5 --output-json eval_runs/e2e_model/results.json
```

The pytest live E2E gate is opt-in because it makes provider calls:

```bash
BRAIN_RUN_LIVE_E2E_MODEL_TESTS=1 uv run pytest tests/test_e2e_model_suite.py -q
```

For live staging acceptance, use the staging E2E suite. It creates or updates the dedicated `brain-e2e` user, signs in through the cookie and CSRF UI auth path, primes staging organically through MCP tool calls, confirms Palate proposals, checks user isolation, and scores usage results with `gpt-5.5` high reasoning.

```bash
ENV_FILE=/Volumes/xpg_usb4/staging/brain/shared/secrets/brain.env uv run python scripts/staging_e2e_suite.py
```

The runner writes JSON reports under `.reports/staging-e2e/` by default. It is not part of normal `pytest` because it mutates staging and makes live provider calls.

## Environment Variables

Deployment, routing, and auth-related settings worth calling out:

- `ALLOW_EMBEDDING_DIMENSION_CHANGE`
- `BRAIN_ADMIN_MCP_PATH`
- `BRAIN_AGENT_MEMORY_SESSION_ID`
- `BRAIN_APP_MCP_PATH`
- `BRAIN_APP_WRITE_RATE_LIMIT_COUNT`
- `BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS`
- `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`
- `BRAIN_AUTH_ENABLED`
- `BRAIN_AUTH_PASSWORD_FILE`
- `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`
- `BRAIN_AUTH_REQUIRE_PKCE`
- `BRAIN_AUTH_SCOPES`
- `BRAIN_AUTH_STATE_PATH`
- `BRAIN_AUTH_SUPERUSER_IDS`
- `BRAIN_AUTH_TOKEN`
- `BRAIN_AUTH_USERS_FILE`
- `BRAIN_BACKUP_DIR`
- `BRAIN_COGNEE_AGENT_MEMORY_DATASET`
- `BRAIN_COGNEE_DATA_DATASET`
- `BRAIN_COGNEE_ENABLED`
- `BRAIN_COGNEE_MEMORY_DATASET`
- `BRAIN_COGNEE_PALATE_DATASET`
- `BRAIN_COGNEE_RECALL_ENABLED`
- `BRAIN_COGNEE_RECALL_TOP_K`
- `BRAIN_COGNEE_SOURCES_DATASET`
- `BRAIN_DATABASE_URL`
- `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED`
- `BRAIN_GOOGLE_DRIVE_FOLDER`
- `BRAIN_GOOGLE_DRIVE_LOCAL_PATH`
- `BRAIN_GOOGLE_DRIVE_REMOTE`
- `BRAIN_HEALTH_PATH`
- `BRAIN_LAUNCHD_LABEL`
- `BRAIN_LOG_LEVEL`
- `BRAIN_LLM_ENABLED`
- `BRAIN_MCP_HOST`
- `BRAIN_MCP_PATH`
- `BRAIN_MCP_PORT`
- `BRAIN_NEO4J_BREW_SERVICE`
- `BRAIN_NEO4J_DOCKER_CONTAINER`
- `BRAIN_NEO4J_DUMP_ENABLED`
- `BRAIN_NEO4J_LAUNCHD_LABEL`
- `BRAIN_NEO4J_STOP_FOR_DUMP`
- `BRAIN_OPENAI_APPS_CHALLENGE_TOKEN`
- `BRAIN_OWNER_FULL_NAME`
- `BRAIN_OWNER_NAME`
- `BRAIN_PROD_ROOT`
- `BRAIN_PROFILE_CONTEXT_PATH`
- `BRAIN_PROVIDER_AUTH_PROFILES_PATH`
- `BRAIN_PROVIDER_AUTH_STATE_DIR`
- `BRAIN_PUBLIC_ADMIN_MCP_PATH`
- `BRAIN_PUBLIC_APP_MCP_PATH`
- `BRAIN_PUBLIC_BASE_URL`
- `BRAIN_PUBLIC_MCP_PATH`
- `BRAIN_PUBLIC_UI_API_PATH`
- `BRAIN_PUBLIC_UI_PATH`
- `BRAIN_RELEASE_ENV`
- `BRAIN_RELEASE_SHA`
- `BRAIN_RELEASE_VERSION`
- `BRAIN_REQUEST_LOG_ENABLED`
- `BRAIN_REQUEST_LOG_MAX_BODY_BYTES`
- `BRAIN_REQUEST_LOG_PATH`
- `BRAIN_REQUEST_LOG_RETENTION_DAYS`
- `BRAIN_ROUTING_LOG_ENABLED`
- `BRAIN_ROUTING_LOG_PATH`
- `BRAIN_ROUTING_LOG_RETENTION_DAYS`
- `BRAIN_SERVICE_NAME`
- `BRAIN_SLACK_ADMIN_USER_IDS`
- `BRAIN_SLACK_AGENT_ENABLED`
- `BRAIN_SLACK_AGENT_HOST`
- `BRAIN_SLACK_AGENT_PORT`
- `BRAIN_SLACK_ALLOWED_CHANNEL_IDS`
- `BRAIN_SLACK_ALLOWED_TEAM_IDS`
- `BRAIN_SLACK_ALLOWED_USER_IDS`
- `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE`
- `BRAIN_SLACK_ENABLED`
- `BRAIN_TASTE_AUTO_ENRICH_ENABLED`
- `BRAIN_TASTE_AUTO_WRITE_THRESHOLD`
- `BRAIN_TASTE_CANONICAL_STORE`
- `BRAIN_TASTE_CONFIRMATION_THRESHOLD`
- `BRAIN_TASTE_ENABLED`
- `BRAIN_TASTE_LLM_MODEL`
- `BRAIN_TASTE_LLM_REASONING_EFFORT`
- `BRAIN_TASTE_LLM_ROUTING_ENABLED`
- `BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD`
- `BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD`
- `BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS`
- `BRAIN_TASTE_WEB_ENRICHMENT_ENABLED`
- `BRAIN_UI_BACKEND_PORT`
- `BRAIN_UI_ENABLED`
- `BRAIN_UI_FRONTEND_PORT`
- `BRAIN_UI_HOST`
- `BRAIN_UI_LAUNCHD_LABEL`
- `BRAIN_UI_PROXY_PORT`
- `BRAIN_UI_SESSION_SECONDS`
- `BRAIN_USER_ID`
- `DATA_ROOT_DIRECTORY`
- `DB_HOST`
- `DB_NAME`
- `DB_PASSWORD`
- `DB_PORT`
- `DB_PROVIDER`
- `DB_USERNAME`
- `EMBEDDING_DIMENSIONS`
- `EMBEDDING_MODEL`
- `EMBEDDING_PROVIDER`
- `ENABLE_BACKEND_ACCESS_CONTROL`
- `GOOGLE_FREE_TIER`
- `GRAPH_DATABASE_NAME`
- `GRAPH_DATABASE_PASSWORD`
- `GRAPH_DATABASE_PROVIDER`
- `GRAPH_DATABASE_URL`
- `GRAPH_DATABASE_USERNAME`
- `LLM_MAX_TOKENS`
- `LLM_MODEL`
- `LLM_PROVIDER`
- `LLM_TEMPERATURE`
- `OPENAI_AUTH_MODE`
- `OPENAI_CODEX_AUTH_PROFILE`
- `OPENAI_CODEX_BASE_URL`
- `PROFILE`
- `SYSTEM_ROOT_DIRECTORY`
- `VECTOR_DATASET_DATABASE_HANDLER`
- `VECTOR_DB_HOST`
- `VECTOR_DB_KEY`
- `VECTOR_DB_NAME`
- `VECTOR_DB_PASSWORD`
- `VECTOR_DB_PORT`
- `VECTOR_DB_PROVIDER`
- `VECTOR_DB_URL`
- `VECTOR_DB_USERNAME`

Core Brain settings:

- `BRAIN_DATABASE_URL=sqlite:///.data/brain/brain.db`
- `BRAIN_USER_ID=default`
- `BRAIN_OWNER_NAME=Daniele`
- `BRAIN_LOG_LEVEL=INFO`
- `BRAIN_AUTH_ENABLED=false`
- `BRAIN_AUTH_TOKEN`

Brain data is scoped by `BRAIN_USER_ID`. When auth is enabled, `BRAIN_AUTH_USERS_FILE` must point to a JSON user registry; issued OAuth tokens carry a `user_id`, and Brain filters memory, profile context, Palate records, audit logs, and recall data to that user. Superusers are marked with `superuser: true` or configured through `BRAIN_AUTH_SUPERUSER_IDS`; they can manage users from the dashboard User Admin tab. Auth-enabled deployments fail closed if the configured users file is missing or empty.

Production auth also relies on `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_REQUIRE_PKCE`, and `BRAIN_AUTH_SCOPES`.

Google Drive backup settings:

- `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED`
- `BRAIN_GOOGLE_DRIVE_FOLDER`
- `BRAIN_GOOGLE_DRIVE_LOCAL_PATH`
- `BRAIN_GOOGLE_DRIVE_REMOTE`

LLM compiler settings are disabled by default. When enabled, it uses the same fixed runtime LLM as the rest of Brain and Cognee:

- `BRAIN_LLM_ENABLED=false`
- `LLM_PROVIDER`
- `LLM_MODEL`

Taste and palate input enrichment uses its own model setting so it can stay on a stronger model without changing Cognee projection defaults:

- `BRAIN_TASTE_LLM_MODEL=gpt-5.5`
- `BRAIN_TASTE_LLM_REASONING_EFFORT=medium`

Cognee projection settings:

- `BRAIN_COGNEE_ENABLED=true`
- `BRAIN_COGNEE_RECALL_ENABLED=false`
- `BRAIN_COGNEE_MEMORY_DATASET=memory`
- `BRAIN_COGNEE_SOURCES_DATASET=sources`
- `BRAIN_COGNEE_DATA_DATASET=data`
- `BRAIN_COGNEE_AGENT_MEMORY_DATASET=agent_memory`
- `BRAIN_COGNEE_PALATE_DATASET=palate`
- `BRAIN_AGENT_MEMORY_SESSION_ID=portable_agent_session`
- `BRAIN_COGNEE_RECALL_TOP_K=10`
- `GRAPH_DATABASE_PROVIDER=ladybug`
- `VECTOR_DB_PROVIDER=pgvector`
- `VECTOR_DATASET_DATABASE_HANDLER=pgvector`
- `DB_PROVIDER=postgres`
- `ENABLE_BACKEND_ACCESS_CONTROL=false`

`BRAIN_AGENT_MEMORY_SESSION_ID` and `BRAIN_COGNEE_AGENT_MEMORY_DATASET` are base names. At runtime, authenticated users receive a derived session id and Cognee agent-memory dataset scoped to their Brain user id, so one user cannot recall or improve another user's chat-session memory.

Brain defaults Cognee's rebuildable projection to Postgres and pgvector for vector storage and Postgres for Cognee metadata. The configured Postgres role must be able to create the `vector` extension; with Cognee's pgvector dataset handler it also needs permission to create per-dataset databases.

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

Runtime uses one configured LLM and one configured embedding model.

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

Set `OPENAI_AUTH_MODE=api_key` to use `OPENAI_API_KEY` for OpenAI text calls. When `OPENAI_AUTH_MODE=oauth` and `EMBEDDING_PROVIDER=openai`, Brain's Cognee OAuth compatibility layer also passes the refreshed OAuth bearer as the OpenAI embedding credential. Use API-key mode when you want embeddings to use `OPENAI_API_KEY` explicitly. Non-runtime providers are available only for explicit eval and smoke experiments.

<!-- brain-doc-source-hash: ca041ace87c5bfd2f237c4fc5e8e132c521b4c6904ecca39472444c03dec5c6d -->
