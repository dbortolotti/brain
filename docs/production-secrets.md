# Production Secrets

The QA, staging, production, and release workflows run on the self-hosted `brain-prod` runner. The deployment model has three deployed environments, plus local dev:

- `dev`: local developer runs.
- `qa`: pushes and merges to `main` deploy through `.github/workflows/deploy-local-qa.yml` to `/Volumes/xpg_usb4/qa/brain`. QA runs as `oric`, uses read-only repository permissions, and records a `qa-<12-char-sha>` build version. `workflow_dispatch` on QA supports `force_config_override`; it has no version input.
- `staging`: manual versioned staging runs through `.github/workflows/deploy-local-staging.yml` to `/Volumes/xpg_usb4/staging/brain`. The workflow requires a `vX.Y.Z` or prerelease tag such as `vX.Y.Z-rc.1`, refreshes generated docs, writes `docs/generated/release.json` with the staged environment, version, and timestamp, pushes the docs stamp to `main`, deploys the stamped commit, and creates the annotated git tag at the staged SHA.
- `prod`: manual release promotion runs through `.github/workflows/release.yml` and deploys the currently staged release version to the cloud Linux server at `159.195.79.79` over SSH as the Linux service user `brain`.

The QA and staging workflows render each environment's `shared/secrets/brain.env` and `shared/secrets/brain-auth-password` from GitHub Secrets and GitHub Variables with `scripts/render_prod_env.py`, then run `scripts/deploy-local-production.sh` with `BRAIN_DEPLOY_ENV=qa` or `staging`.

The release workflow renders production config the same way, then runs `scripts/deploy-cloud-production.sh`. That script packages the checkout, uploads it to `brain@159.195.79.79`, and runs `scripts/install-cloud-linux-production.sh` with sudo on the server.

The rendered config and QA/staging deploy steps run with passwordless `sudo` on the local self-hosted runner. Staging is owned and run by `oric_staging`; QA is owned and run by `oric`. `scripts/setup-macos-service-users.sh` creates the hidden staging service user on a new Mac. QA and staging deploys install system LaunchDaemons in `/Library/LaunchDaemons`, not per-user LaunchAgents, so services start at boot and wait for `/Volumes/xpg_usb4/{qa|staging}/brain/current` before launching. Each LaunchDaemon uses `SessionCreate` with its service user and starts from `/var/db/brain-{staging|qa}`.

Cloud production uses standard Linux paths and systemd:

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

The Linux installer creates the `brain` service user when missing, installs required Debian packages and `uv` when missing, starts Postgres/pgvector and Neo4j with Docker Compose, runs Alembic migrations, installs systemd units, installs Caddy routing for `brain.dceb.net`, and restarts `brain-mcp.service` and `brain-ui.service`.

Production public HTTPS uses direct DNS and Caddy, not Cloudflare Tunnel:

```text
brain.dceb.net.  A  159.195.79.79
```

Keep the Cloudflare record DNS-only while Caddy manages the origin certificate directly. The production hostname is intentionally absent from `deployment/cloudflare/config.example.yml`; that tunnel template remains only for QA/staging local routes.

Direct operator deploys use:

```bash
scripts/deploy-cloud-production.sh \
  --rendered-env /path/to/brain.env \
  --rendered-auth-password /path/to/brain-auth-password
```

The renderer requires `GRAPH_DATABASE_PASSWORD` to be non-empty.

The deploy workflows also pass `BRAIN_AUTH_TOKEN` into `render_prod_env.py`.

The staging and release workflow-dispatch `version` inputs are required. QA has no version input and derives its build version from the pushed commit SHA. `force_config_override` is available only on workflow-dispatch runs for QA, staging, and release. It defaults to `false`. Push-based QA deploys do not use it.

## Release Versioning

Every deploy writes runtime release metadata into:

```text
/Volumes/xpg_usb4/{qa|staging}/brain/current/release.json
/Volumes/xpg_usb4/{qa|staging}/brain/shared/release.json
/opt/brain/current/release.json
/opt/brain/shared/release.json
```

The release metadata records the app name, environment, version, SHA, release directory, `deployed_at`, and source. The source is `github-actions` for workflow runs and `local` for local runs.

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

Normal pushes to `main` deploy QA with an automatic build version such as `qa-1a2b3c4d5e6f`. To create a promotable release, manually run the staging workflow with a version like `v2.1.0` or `v2.1.0-rc.1`. That workflow refreshes generated docs, records the tag in `docs/generated/release.json`, pushes any docs stamp commit back to `main`, deploys that stamped commit, records `BRAIN_RELEASE_VERSION` as the tag, and creates the annotated git tag at the staged SHA. If the tag already exists at a different SHA, the staging run fails instead of retagging.

Production promotion does not mint a new version. The release workflow reads staging `shared/release.json`, verifies the requested version is the active staged version, verifies the git tag already exists at that exact SHA, checks that the staging `current` symlink points at the same commit, and then deploys production with the same `BRAIN_RELEASE_VERSION` and staged SHA.

GitHub Secrets and GitHub Variables are the source of truth. Live config can still be edited directly for an emergency, but the next deploy for that environment will fail unless that change has been propagated back to GitHub.

## Config Conflict Rule

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

## Deployment Metadata and Auth Registry

Deployment also configures `BRAIN_AUTH_USERS_FILE` under `shared/secrets/brain-auth-users.json` and `BRAIN_AUTH_SUPERUSER_IDS` in the deployed config. A superuser can create, edit, and delete user records from the dashboard User Admin tab. Superusers can also create and revoke per-user personal access tokens for headless agents; Brain stores only token hashes in the OAuth state file, and the raw `brain_pat_...` value is shown only at creation time.

The deployed auth and dashboard surfaces include these route families:

```text
/                     app root
/admin                root/admin dashboard view
/user                 user dashboard
/app                  app dashboard
/login                user login endpoint
/logout               user logout endpoint
/account/password     change own password
/admin/users          list and create auth users
/admin/users/{user_id} update or delete auth users
/admin/tokens         list and create personal access tokens
/admin/tokens/{token_id} revoke a personal access token
/authorize            OAuth authorization endpoint
/token                OAuth token endpoint
/revoke               OAuth token revocation endpoint
/register             OAuth client registration endpoint
/.well-known/oauth-authorization-server
/.well-known/oauth-protected-resource
/.well-known/oauth-protected-resource/{resource_path:path}
/.well-known/openid-configuration
/.well-known/openai-apps-challenge
/auth/session         session endpoint
/api/session          session endpoint
/app-assets/{asset_name}
/apple-touch-icon.png
/app/oauth/callback
/create_datasource
/datasources
/datasources/{datasource}
/delete_datasource
/delete_datasource/{datasource}
/docs
/docs/oauth2-redirect
/favicon.ico
/healthz
/icon.png
/list_datasources
/memory/forget
/memory/ingest_source
/memory/merge_entities
/memory/open_loops
/memory/profile_entity
/memory/rebuild_cognee
/memory/recall
/memory/remember
/memory/resolve_conflict
/memory/review_recent
/memory/sync_cognee
/memory/undo_last
/memory/{memory_id}
/openapi.json
/privacy
/redoc
/support
/terms
/{path:path}          MCP route fallback
```

The key auth routes are `GET` and `POST` as appropriate: `/authorize` accepts `GET` and `POST`, `/login`, `/logout`, `/register`, `/revoke`, and `/token` are `POST`-only, `/account/password` is `PUT`, `/admin/users` and `/admin/tokens` are `GET` and `POST`, `/admin/users/{user_id}` is `PUT` and `DELETE`, `/admin/tokens/{token_id}` is `DELETE`, and `/auth/session` and `/api/session` are `GET`.

The workflows set `BRAIN_MCP_PATH=/mcp`, `BRAIN_ADMIN_MCP_PATH=/admin/mcp`, `BRAIN_APP_MCP_PATH=/app/mcp`, `BRAIN_PUBLIC_MCP_PATH=/mcp`, `BRAIN_PUBLIC_ADMIN_MCP_PATH=/admin/mcp`, `BRAIN_PUBLIC_APP_MCP_PATH=/mcp`, `BRAIN_PUBLIC_UI_PATH=/cognee`, and `BRAIN_PUBLIC_UI_API_PATH=/cognee-api`.

`/app/mcp`, `/ui`, and `/ui-api` remain compatibility aliases, and the Cognee UI proxy also exposes `/ui-login`, `/ui-logout`, `/cognee-login`, and `/cognee-logout`. The Cognee UI proxy surfaces also remain available at:

```text
/admin/cognee
/admin/cognee/{path:path}
/admin/cognee-api/{path:path}
/cognee
/cognee/{path:path}
/cognee-api/{path:path}
/cognee-login
/cognee-logout
/ui
/ui/{path:path}
/ui-api/{path:path}
/ui-login
/ui-logout
```

## Required Secrets

Configure these in GitHub repository secrets for QA, staging, and production deploys:

```text
OPENAI_API_KEY
GRAPH_DATABASE_PASSWORD
BRAIN_AUTH_PASSWORD
```

The deploy workflows also pass `BRAIN_AUTH_TOKEN` into `render_prod_env.py`.

`GRAPH_DATABASE_PASSWORD` is treated as required by the renderer and cannot be empty. The renderer rejects empty or placeholder values for `OPENAI_API_KEY` (``, `replace-me`, `sk-...`, `...`) and `BRAIN_AUTH_PASSWORD` (``, `replace-me`, `...`).

## Optional Taste Integration Secrets

```text
BRAIN_TASTE_OMDB_API_KEY
BRAIN_TASTE_GOOGLE_PLACES_API_KEY
```

Set these only when the corresponding Taste integrations are enabled.

## Optional Eval Provider Secrets

Runtime uses the configured LLM and embedding provider/model settings. Set these only when you want explicit eval or smoke experiments against additional `provider:model` refs:

```text
OPENROUTER_API_KEY
GEMINI_API_KEY
GOOGLE_API_KEY
ANTHROPIC_API_KEY
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
AWS_BEARER_TOKEN_BEDROCK
GROQ_API_KEY
VOYAGE_API_KEY
```

For Bedrock, prefer `AWS_BEARER_TOKEN_BEDROCK` for model-eval experiments. Use standard AWS credentials only when the Bedrock client path requires SDK auth.

## Optional Slack Secrets

```text
BRAIN_SLACK_SIGNING_SECRET
BRAIN_SLACK_BOT_TOKEN
```

## Recommended Variables

Use GitHub repository variables for non-secret deployment settings. Do not set `BRAIN_RELEASE_ENV`, `BRAIN_RELEASE_SHA`, or `BRAIN_RELEASE_VERSION` here; deployment writes those metadata keys.

```text
PROFILE
CONFIG_ENV
ALLOW_EMBEDDING_DIMENSION_CHANGE
LLM_PROVIDER
LLM_MODEL
LLM_TEMPERATURE
LLM_MAX_TOKENS
BRAIN_LLM_ENABLED
EMBEDDING_PROVIDER
EMBEDDING_MODEL
EMBEDDING_DIMENSIONS
OPENAI_AUTH_MODE
OPENAI_CODEX_AUTH_PROFILE
OPENAI_CODEX_BASE_URL
BRAIN_DATABASE_URL
AWS_REGION
AWS_DEFAULT_REGION
AWS_PROFILE
BRAIN_PUBLIC_BASE_URL
BRAIN_HEALTH_PATH
BRAIN_LAUNCHD_LABEL
BRAIN_MCP_HOST
BRAIN_MCP_PORT
BRAIN_MCP_PATH
BRAIN_APP_MCP_PATH
BRAIN_ADMIN_MCP_PATH
BRAIN_PUBLIC_MCP_PATH
BRAIN_PUBLIC_ADMIN_MCP_PATH
BRAIN_PUBLIC_APP_MCP_PATH
BRAIN_PUBLIC_UI_PATH
BRAIN_PUBLIC_UI_API_PATH
BRAIN_OPENAI_APPS_CHALLENGE_TOKEN
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED
BRAIN_GOOGLE_DRIVE_REMOTE
BRAIN_GOOGLE_DRIVE_FOLDER
BRAIN_GOOGLE_DRIVE_LOCAL_PATH
BRAIN_NEO4J_DUMP_ENABLED
BRAIN_NEO4J_STOP_FOR_DUMP
BRAIN_NEO4J_BREW_SERVICE
BRAIN_NEO4J_DOCKER_CONTAINER
BRAIN_NEO4J_LAUNCHD_LABEL
BRAIN_REQUEST_LOG_ENABLED
BRAIN_REQUEST_LOG_PATH
BRAIN_REQUEST_LOG_MAX_BODY_BYTES
BRAIN_REQUEST_LOG_RETENTION_DAYS
BRAIN_ROUTING_LOG_ENABLED
BRAIN_ROUTING_LOG_PATH
BRAIN_ROUTING_LOG_RETENTION_DAYS
BRAIN_UI_ENABLED
BRAIN_UI_HOST
BRAIN_UI_PROXY_PORT
BRAIN_UI_FRONTEND_PORT
BRAIN_UI_BACKEND_PORT
BRAIN_UI_LAUNCHD_LABEL
BRAIN_UI_SESSION_SECONDS
BRAIN_SLACK_ENABLED
BRAIN_SLACK_AGENT_ENABLED
BRAIN_SLACK_AGENT_HOST
BRAIN_SLACK_AGENT_PORT
BRAIN_SLACK_ALLOWED_TEAM_IDS
BRAIN_SLACK_ALLOWED_CHANNEL_IDS
BRAIN_SLACK_ALLOWED_USER_IDS
BRAIN_SLACK_ADMIN_USER_IDS
BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE
BRAIN_AUTH_ENABLED
BRAIN_AUTH_ACCESS_TOKEN_SECONDS
BRAIN_AUTH_REFRESH_TOKEN_SECONDS
BRAIN_AUTH_REQUIRE_PKCE
BRAIN_AUTH_SCOPES
BRAIN_AUTH_STATE_PATH
BRAIN_AUTH_USERS_FILE
BRAIN_AUTH_SUPERUSER_IDS
BRAIN_AUTH_PASSWORD_FILE

BRAIN_BACKUP_DIR
BRAIN_COGNEE_ENABLED
BRAIN_COGNEE_DATA_DATASET
BRAIN_COGNEE_MEMORY_DATASET
BRAIN_COGNEE_PALATE_DATASET
BRAIN_COGNEE_RECALL_ENABLED
BRAIN_COGNEE_RECALL_TOP_K
BRAIN_COGNEE_SOURCES_DATASET
BRAIN_COGNEE_SYNC_ON_INGEST
BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT
BRAIN_TASTE_ENABLED
BRAIN_TASTE_CANONICAL_STORE
BRAIN_TASTE_LLM_MODEL
BRAIN_TASTE_LLM_REASONING_EFFORT
BRAIN_TASTE_LLM_ROUTING_ENABLED
BRAIN_TASTE_AUTO_ENRICH_ENABLED
BRAIN_TASTE_AUTO_WRITE_THRESHOLD
BRAIN_TASTE_CONFIRMATION_THRESHOLD
BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD
BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD
BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS
BRAIN_TASTE_WEB_ENRICHMENT_ENABLED
BRAIN_INGEST_BACKGROUND_AUTO_CHARS
DATA_ROOT_DIRECTORY
DB_HOST
DB_NAME
DB_PASSWORD
DB_PORT
DB_PROVIDER
DB_USERNAME
ENABLE_BACKEND_ACCESS_CONTROL
GOOGLE_FREE_TIER
GRAPH_DATABASE_NAME
GRAPH_DATABASE_PASSWORD
GRAPH_DATABASE_PROVIDER
GRAPH_DATABASE_URL
GRAPH_DATABASE_USERNAME
SYSTEM_ROOT_DIRECTORY
VECTOR_DATASET_DATABASE_HANDLER
VECTOR_DB_HOST
VECTOR_DB_KEY
VECTOR_DB_NAME
VECTOR_DB_PASSWORD
VECTOR_DB_PORT
VECTOR_DB_PROVIDER
VECTOR_DB_URL
VECTOR_DB_USERNAME
BRAIN_OWNER_FULL_NAME
BRAIN_OWNER_NAME
BRAIN_PROFILE_CONTEXT_PATH
BRAIN_PROVIDER_AUTH_PROFILES_PATH
BRAIN_PROVIDER_AUTH_STATE_DIR
BRAIN_SERVICE_NAME
BRAIN_USER_ID
BRAIN_LOG_LEVEL
BRAIN_PROD_ROOT
BRAIN_APP_WRITE_RATE_LIMIT_COUNT
BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS
```

The renderer also reads additional environment variables in staging and prod, including the `BRAIN_COGNEE_*` family, `BRAIN_COGNEE_SYNC_ON_INGEST`, `BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT`, `BRAIN_INGEST_BACKGROUND_AUTO_CHARS`, `CONFIG_ENV`, `BRAIN_DATABASE_URL`, `BRAIN_GOOGLE_DRIVE_REMOTE`, `BRAIN_HEALTH_PATH`, `BRAIN_LLM_ENABLED`, `BRAIN_MCP_PATH`, `BRAIN_NEO4J_*` service and container labels, `BRAIN_OPENAI_APPS_CHALLENGE_TOKEN`, `BRAIN_AUTH_TOKEN`, `BRAIN_AUTH_SUPERUSER_IDS`, `BRAIN_SLACK_ENABLED`, `BRAIN_SLACK_AGENT_HOST`, `BRAIN_SLACK_AGENT_PORT`, `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE`, `BRAIN_TASTE_*` controls including `BRAIN_TASTE_CANONICAL_STORE`, and the `BRAIN_UI_*` runtime settings shown above.

## Local Backup

Before moving secrets into GitHub, keep a local gitignored backup under `local-secrets/`. A generated `github-secrets.env` file can be loaded with:

```bash
gh secret set -f local-secrets/latest/github-secrets.env
```

<!-- brain-doc-source-hash: 5d3498c917bccccc87f4db032fb5d1a89e6c90ff697925c3050b937969a626e4 -->
<!-- brain-doc-source-commit: 2e3bd4c643a467d06e87c510b7a1d6afd562ba6c -->
