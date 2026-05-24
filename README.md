# Brain

Brain is a local personal memory control plane exposed through a small MCP surface. Brain DB is the control store for user scope, profile/bias policy, session mapping, confirmations, receipts, and app audit records. Cognee is the required semantic memory substrate for durable memory, source ingestion, graph/vector retrieval, and improvement.

## Documentation

- [User Guide](docs/USER_GUIDE.md) - end-user guidance for saving and recalling memories through Brain tools and the browser app.
- [Agent Tool Guide](docs/AGENT_TOOL_GUIDE.md) - advanced MCP tool usage, tool-selection rules, and agent-facing examples.
- [API Setup Guide](docs/API_SETUP_GUIDE.md) - HTTP, MCP, auth, client setup, and integration examples.
- [Backup Scheme](docs/BACKUP_SCHEME.md) - backup contents, verification, Google Drive replication, and restore outline.
- [Production Secrets](docs/production-secrets.md) - staging, prod, and release flow, secret handling, and config conflict rules.
- [ChatGPT App Hardening](docs/chatgpt-app-hardening.md) - app review hardening model and post-merge production verification checklist.
- [OpenAI Submission Checklist](docs/openai-submission.md) - remaining non-code checklist for ChatGPT App review.
- [Proposed Brain/Cognee Flow](docs/proposed_brain_cognee_flow.md) - proposed thinner Brain facade with Cognee as the semantic memory substrate.

## Local Dev Setup

```bash
cp .env.example .env
make setup
make check
uv run pytest
```

If you want the smaller local/OpenAI-oriented example, use `.env.openai.example` instead of `.env.example`. `.env.example` mirrors `cfg/common.yaml`: Postgres Cognee metadata, pgvector vectors, and the default graph provider. `.env.openai.example` is the smaller local/OpenAI-oriented example using Neo4j, LanceDB, and SQLite.

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

The default local URL is `http://127.0.0.1:8000`. The health check is served at the configured `BRAIN_HEALTH_PATH` (default `/healthz`).

Selected user-facing HTTP endpoints include:

- `GET /healthz`
- `GET /.well-known/oauth-authorization-server`
- `GET /.well-known/openid-configuration`
- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-protected-resource/{resource_path:path}`
- `GET /.well-known/openai-apps-challenge` when `BRAIN_OPENAI_APPS_CHALLENGE_TOKEN` is configured for OpenAI domain verification
- `POST /register`
- `GET|POST /authorize`
- `POST /token`
- `POST /revoke`
- `POST /login`
- `POST /logout`
- `GET /auth/session`
- `GET /api/session`
- `PUT /account/password`
- `GET /admin/tokens`
- `POST /admin/tokens`
- `DELETE /admin/tokens/{token_id}`
- `GET /admin/users`
- `POST /admin/users`
- `PUT /admin/users/{user_id}`
- `DELETE /admin/users/{user_id}`
- `GET|POST /mcp`
- `GET|POST /admin/mcp`
- `GET|POST /app/mcp`
- `GET /docs`
- `GET /docs/oauth2-redirect`
- `GET /redoc`
- `GET /openapi.json`
- `GET /favicon.ico`
- `GET /icon.png`
- `GET /apple-touch-icon.png`
- `GET /privacy`
- `GET /terms`
- `GET /support`
- `GET /datasources`
- `POST /datasources`
- `DELETE /datasources/{datasource}`
- `POST /create_datasource`
- `GET /list_datasources`
- `POST /delete_datasource`
- `DELETE /delete_datasource/{datasource}`
- `POST /memory/remember`
- `POST /memory/ingest_source`
- `POST /memory/recall`
- `POST /memory/profile_entity`
- `POST /memory/forget`
- `POST /memory/review_recent`
- `POST /memory/undo_last`

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
- external chat-continuity workflow
- external chat-continuity recall
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
- `brain_forget`
- `brain_review_recent`
- `brain_undo_last`
- `brain_profile_context_remember`
- `brain_profile_context_list`
- `brain_profile_context_forget`
- `brain_bias_context_remember`
- `brain_bias_context_list`
- `brain_bias_context_forget`
- `brain_profile_context_sync`
- `brain_app_data_controls`
- `cognee_improve`
- external chat-continuity workflow
- external chat-continuity recall
- external chat-continuity cleanup
- `brain_palate_describe_item`
- `brain_palate_remember`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_log_decision`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`
- `brain_palate_refresh_enrichment`

Raw SQL and arbitrary Cognee primitives are intentionally not exposed as public MCP tools. Brain exposes curated Cognee/admin operations such as forget, review_recent, undo_last, profile context sync, and configured improve.

## Running The Cognee UI Proxy

The Cognee UI proxy is a separate HTTP service. It does not serve `/mcp`, and UI paths should be routed to its own port. The proxy owns the `/cognee`, `/admin/cognee`, `/admin/cognee-api`, `/ui`, `/ui-api`, `/cognee-api`, `/ui-login`, `/ui-logout`, `/cognee-login`, and `/cognee-logout` surfaces.

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

The proxy also serves `GET /healthz`, `GET /docs`, `GET /docs/oauth2-redirect`, `GET /redoc`, `GET /openapi.json`, `GET /favicon.ico`, `GET /icon.png`, `GET /apple-touch-icon.png`, and the frontend root routes.

## ChatGPT App Surface

Brain exposes a curated MCP surface for a ChatGPT App and user-facing clients at the configured public base URL together with `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_APP_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`. The workflows currently set `BRAIN_PUBLIC_APP_MCP_PATH=/mcp`, so public app clients use the curated surface at `/mcp` while `/app/mcp` remains a legacy alias. The root dashboard uses the same curated surface through a browser session. Browser users sign in with user id and password; the dashboard uses its own session and CSRF flow rather than bearer tokens.

When auth is enabled, HTTP and MCP client requests use either the static token or the built-in OAuth bearer token flow. Browser dashboard users still authenticate through the cookie session.

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
- external chat-continuity workflow
- external chat-continuity recall
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

Admin, write-only, profile-context-sync, bias-context, chat-continuity-cleanup, and Palate persistence tools remain on the internal `/admin/mcp` surface only. The internal `/admin/mcp` surface also exposes `brain_app_open_review_panel`; the public app surface does not. On `/mcp`, read tools advertise `brain.memory.read`; write tools advertise `brain.memory.read brain.memory.write`, are rate-limited, and destructive app-surface calls such as `brain_undo_last` and `brain_profile_context_forget` require confirmation.

Browser dashboard auth is separate from MCP client auth. `/login` verifies a user-registry password, creates an opaque server-side session, and sets a cookie. Mutating dashboard requests must include the per-session CSRF token returned by `/auth/session`. MCP clients still use OAuth bearer tokens.

Protected unauthenticated requests return `401` with a `WWW-Authenticate` challenge that advertises Brain's protected-resource metadata.

User-registry passwords are stored as Argon2id hashes. Legacy plaintext user records are accepted for migration only; a successful login migrates that user, and operators can migrate and check the full registry with:

```bash
uv run python scripts/migrate_auth_user_passwords.py --env-file /path/to/brain.env
uv run python scripts/migrate_auth_user_passwords.py --env-file /path/to/brain.env --check
```

The Cognee UI proxy also uses Brain user/password login. Regular users enter through `/cognee`; superusers can use `/admin/cognee` for system-level Cognee inspection. The older `/ui` and `/ui-api` routes, plus `/cognee-api`, `/cognee-login`, `/cognee-logout`, `/ui-login`, and `/ui-logout`, are compatibility aliases.

Deployment also configures `BRAIN_AUTH_USERS_FILE` under `shared/secrets/brain-auth-users.json` and `BRAIN_AUTH_SUPERUSER_IDS` in the deployed config. A superuser can create, edit, and delete user records from the dashboard User Admin tab. Superusers can also create and revoke per-user personal access tokens for headless agents; Brain stores only token hashes in the OAuth state file, and the raw `brain_pat_...` value is shown only at creation time.

Public app support pages:

- `/privacy`
- `/terms`
- `/support`

See `docs/chatgpt-app-hardening.md` for the app review hardening model and the post-merge production verification checklist.

## Legacy Slack Adapter

Slack is no longer a supported Brain surface. The legacy adapter code remains dormant for compatibility and cleanup work, but default configs disable it and product docs should not route new users through Slack.

## Deployment and Release Model

Brain deploys in three tiers, plus local dev:

- `dev`: local developer runs.
- `qa`: every push to `main` deploys through `.github/workflows/deploy-local-qa.yml` to `/Volumes/xpg_usb4/qa/brain` as `oric`, with read-only repository permissions and the `qa-<12-char-sha>` build version. QA has no version input and derives its build version from the pushed commit SHA. Manual `workflow_dispatch` QA runs support only `force_config_override` for intentional re-baselines.
- `staging`: manual versioned staging runs through `.github/workflows/deploy-local-staging.yml` to `/Volumes/xpg_usb4/staging/brain` as `oric_staging`. The workflow requires a `vX.Y.Z` or prerelease tag, refreshes generated docs, writes `docs/generated/release.json` with that tag, pushes the docs stamp to `main`, deploys the stamped commit, and creates the annotated git tag.
- `prod`: manual release promotion runs through `.github/workflows/release.yml` and deploys the currently staged release version to the cloud Linux server at `159.195.79.79` over SSH as the Linux user `brain`.

The cloud production layout is:

```text
/opt/brain/current -> /opt/brain/releases/<commit-sha>
/opt/brain/shared/release.json
/etc/brain/brain.env
/etc/brain/brain-auth-password
/etc/brain/brain-auth-users.json
/var/lib/brain/data
/var/lib/brain/backups
/var/lib/brain/venvs/<commit-sha>
/var/lib/brain/current-venv -> /var/lib/brain/venvs/<commit-sha>
/var/lib/brain/docker
/var/log/brain
/etc/caddy/conf.d/brain.caddy
/etc/systemd/system/brain-mcp.service
/etc/systemd/system/brain-ui.service
/etc/systemd/system/brain-maintenance.service
/etc/systemd/system/brain-maintenance.timer
```

From this checkout, a direct cloud deploy can be run with:

```bash
make deploy-cloud-production
```

Direct deploys need real production secrets either already present in `/etc/brain/brain.env` on the server or passed with `scripts/deploy-cloud-production.sh --rendered-env PATH --rendered-auth-password PATH`.

The QA and staging workflows render each environment's `shared/secrets/brain.env` from GitHub Secrets and GitHub Variables with `scripts/render_prod_env.py`, then run `scripts/deploy-local-production.sh` with `BRAIN_DEPLOY_ENV=qa` or `staging`. Rendering and deploy run with passwordless `sudo` because deployed roots are owned by their runtime users. Staging runs as `oric_staging`; QA runs as `oric`. System LaunchDaemons are installed under `/Library/LaunchDaemons` so they can start at boot and wait for `/Volumes/xpg_usb4` to be mounted before launching.

The release workflow renders production config the same way, then runs `scripts/deploy-cloud-production.sh`. That uploader packages the checkout, copies it to `brain@159.195.79.79`, and runs `scripts/install-cloud-linux-production.sh` with sudo on the server. The Linux installer creates or repairs the `brain` user, installs missing runtime packages and `uv`, starts Postgres/pgvector and Neo4j with Docker Compose, runs migrations, installs systemd units, installs the Caddy reverse-proxy config, and restarts Brain.

The deploy will refuse to start Neo4j if `GRAPH_DATABASE_PASSWORD` is empty.

Production public HTTPS is direct DNS, not Cloudflare Tunnel:

```text
brain.dceb.net.  A  159.195.79.79
```

Keep the Cloudflare record DNS-only while Caddy manages the origin certificate directly. QA and staging may continue to use the local Cloudflare Tunnel config.

The workflow-dispatch-only `force_config_override` input bypasses config conflict checks and establishes a new baseline. Use it only for an intentional bootstrap or re-baseline. It is available only on workflow-dispatch runs for QA, staging, and release; push-based QA deploys do not use it.

Workflow model:

- `.github/workflows/deploy-local-qa.yml` triggers on `push` to `main` and on `workflow_dispatch`, and accepts only `force_config_override` for manual re-baselines.
- `.github/workflows/deploy-local-staging.yml` triggers on `workflow_dispatch`, requires `version`, accepts `force_config_override`, updates generated docs, stamps docs with the tag, pushes that docs commit to `main`, and tags the stamped commit.
- `.github/workflows/release.yml` is manual only, requires a previously staged `version`, and also accepts `force_config_override`.
- `.github/workflows/validate.yml` runs on `pull_request` and `workflow_dispatch`.

The Makefile exposes the deploy helpers:

```bash
make deploy-local-production
make deploy-cloud-production
```

Equivalent commands:

```bash
./scripts/deploy-local-production.sh
./scripts/deploy-cloud-production.sh
```

Before the first QA/staging daemon deploy on a Mac, create the service users:

```bash
./scripts/setup-macos-service-users.sh
```

Deployments also configure `BRAIN_AUTH_USERS_FILE` under `shared/secrets/brain-auth-users.json` and `BRAIN_AUTH_SUPERUSER_IDS` in the deployed config. Auth-enabled Brain instances fail closed when the configured registry is missing or empty, and superusers can manage users from the dashboard User Admin tab without restarting the service.

GitHub Secrets and GitHub Variables are the source of truth; direct emergency edits to live config must be propagated back, or the next deploy will fail.

## Release Versioning

Every deploy writes runtime release metadata into:

```text
/Volumes/xpg_usb4/{qa|staging}/brain/current/release.json
/Volumes/xpg_usb4/{qa|staging}/brain/shared/release.json
/opt/brain/current/release.json
/opt/brain/shared/release.json
```

The release metadata records the app name, environment, version, SHA, release directory, deployed_at, and source. The source is `github-actions` for workflow runs and `local` for local runs.

The renderer also writes config-render metadata keys into the rendered config:

```text
BRAIN_CONFIG_RENDER_SHA
BRAIN_CONFIG_RENDERED_AT
BRAIN_CONFIG_RENDER_SOURCE
```

The release metadata keys are:

```text
BRAIN_RELEASE_ENV
BRAIN_RELEASE_SHA
BRAIN_RELEASE_VERSION
```

These metadata keys are deployment metadata, not repository variables. The conflict checker ignores both metadata families.

Normal pushes to `main` deploy QA with an automatic build version such as `qa-1a2b3c4d5e6f`. To create a promotable release, manually run the staging workflow with a version like `v2.1.0` or `v2.1.0-rc.1`. That workflow refreshes generated docs, records the tag in `docs/generated/release.json`, pushes any docs stamp commit back to `main`, deploys that stamped commit to staging, records `BRAIN_RELEASE_VERSION` as the tag, and creates the annotated git tag at the staged SHA. If the tag already exists at a different SHA, the staging run fails instead of retagging.

Production promotion does not mint a new version. The release workflow reads staging `shared/release.json`, verifies the requested version is the active staged version, verifies the git tag already exists at that exact SHA, checks that the staging `current` symlink points at the same commit, and then deploys production with the same `BRAIN_RELEASE_VERSION` and staged SHA.

## Conflict Rule

The renderer compares three files:

```text
proposed: newly rendered GitHub Secrets/Vars config
live:     /Volumes/xpg_usb4/{qa|staging}/brain/shared/secrets/brain.env or /etc/brain/brain.env
base:     /Volumes/xpg_usb4/{qa|staging}/brain/shared/secrets/brain.env.last-deployed or the rendered production baseline
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

The renderer ignores metadata keys when it compares configs. After a successful render, both `brain.env` and `brain.env.last-deployed` are updated to the proposed config.

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

You can override the output path with `MODEL_SMOKE_OUTPUT` and append additional arguments with `MODEL_SMOKE_ARGS`.

Useful production checks:

```bash
make prod-check
make ui-prod-check
make slack-agent-check
make public-check
```

`public-check` checks the direct-DNS public HTTPS health and required support pages through Caddy.

Operational maintenance targets:

```bash
make mcp-config
make palate-probe
make backup
make reset
make reset-hard
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
make llm-docs       # alias used by the pre-commit hook
make docs-hash      # refresh source hashes after manual doc review
```

The validate workflow and the QA deploy workflow run `make docs-check`. The staging workflow runs `make docs-generate`, stamps `docs/generated/release.json` with the requested tag, commits those generated docs to `main` when they changed, and then runs `make docs-check`. The local pre-commit hook runs `make llm-docs`, so commits require the configured LLM documentation environment.

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
- `BRAIN_COGNEE_DATA_DATASET`
- `BRAIN_COGNEE_ENABLED`
- `BRAIN_COGNEE_MEMORY_DATASET`
- `BRAIN_COGNEE_PALATE_DATASET`
- `BRAIN_COGNEE_RECALL_ENABLED`
- `BRAIN_COGNEE_RECALL_TOP_K`
- `BRAIN_COGNEE_SOURCES_DATASET`
- `BRAIN_COGNEE_SYNC_ON_INGEST`
- `BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT`
- `BRAIN_DATABASE_URL`
- `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED`
- `BRAIN_GOOGLE_DRIVE_FOLDER`
- `BRAIN_GOOGLE_DRIVE_LOCAL_PATH`
- `BRAIN_GOOGLE_DRIVE_REMOTE`
- `BRAIN_HEALTH_PATH`
- `BRAIN_INGEST_BACKGROUND_AUTO_CHARS`
- `BRAIN_LAUNCHD_LABEL`
- `BRAIN_LLM_ENABLED`
- `BRAIN_LOG_LEVEL`
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
- `BRAIN_SLACK_SIGNING_SECRET`
- `BRAIN_SLACK_BOT_TOKEN`
- `BRAIN_TASTE_AUTO_ENRICH_ENABLED`
- `BRAIN_TASTE_AUTO_WRITE_THRESHOLD`
- `BRAIN_TASTE_CANONICAL_STORE`
- `BRAIN_TASTE_CONFIRMATION_THRESHOLD`
- `BRAIN_TASTE_ENABLED`
- `BRAIN_TASTE_GOOGLE_PLACES_API_KEY`
- `BRAIN_TASTE_LLM_MODEL`
- `BRAIN_TASTE_LLM_REASONING_EFFORT`
- `BRAIN_TASTE_LLM_ROUTING_ENABLED`
- `BRAIN_TASTE_OMDB_API_KEY`
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
- `BRAIN_COGNEE_PALATE_DATASET=palate`
- `BRAIN_COGNEE_RECALL_TOP_K=10`
- `GRAPH_DATABASE_PROVIDER=ladybug`
- `VECTOR_DB_PROVIDER=pgvector`
- `VECTOR_DATASET_DATABASE_HANDLER=pgvector`
- `DB_PROVIDER=postgres`
- `ENABLE_BACKEND_ACCESS_CONTROL=false`

At runtime, authenticated users receive a derived session id and Cognee chat-continuity dataset scoped to their Brain user id, so one user cannot recall or improve another user's chat-session memory.

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

Legacy Slack adapter settings, unsupported and disabled by default:

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

Slack command handling is retained only as dormant legacy code and is not part of the supported Brain/Cognee cutover surface.

## Profiles

Runtime uses one configured LLM and one configured embedding model.

Environment examples differ by local setup:

- `.env.example` mirrors `cfg/common.yaml`: Postgres Cognee metadata, pgvector vectors, and the default graph provider.
- `.env.openai.example` is a smaller local/OpenAI-oriented example using Neo4j, LanceDB, and SQLite.
- `cfg/qa.yaml` is the QA override deployed automatically from `main`.
- `cfg/staging.yaml` is the staging override deployed by the manual tagged staging workflow.
- `cfg/prod.yaml` is the production override promoted by the release workflow. Promotable releases are versioned in staging first; production verifies and keeps that staged `BRAIN_RELEASE_VERSION` instead of creating a new one at promotion time.

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

<!-- brain-doc-source-hash: a3cf55a542c8fd6edf4c24e481c12d8169c02fbfd751d5e7c3f6ffb4a22dbd63 -->
<!-- brain-doc-source-commit: c01adbc3b67d1dfe659caf5600f743d1fffad426 -->
