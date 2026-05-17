# Production Secrets

Deploys run on the self-hosted `brain-prod` runner with three environments:

- `dev`: local developer runs.
- `staging`: `main` deploys through `.github/workflows/deploy-local-staging.yml`
  to `/Volumes/xpg_usb4/staging/brain`.
- `prod`: manual release promotion runs through `.github/workflows/release.yml`
  and deploys the currently staged release version to
  `/Volumes/xpg_usb4/prod/brain`.

`.github/workflows/deploy-local-production.yml` remains available as a manual
production deploy escape hatch. It is not triggered by pushes to `main`.

The staging, production, and release workflows render each environment's
`shared/secrets/brain.env` from GitHub Secrets and GitHub Variables with
`scripts/render_prod_env.py`, then run `scripts/deploy-local-production.sh`
with `BRAIN_DEPLOY_ENV=staging` or `BRAIN_DEPLOY_ENV=prod`.

`force_config_override` is available only on workflow-dispatch runs for staging,
production, and release. It defaults to `false`. Push-based staging deploys do
not use it.

## Release Versioning

Every deploy writes runtime release metadata into:

```text
/Volumes/xpg_usb4/{staging|prod}/brain/current/release.json
/Volumes/xpg_usb4/{staging|prod}/brain/shared/release.json
```

The release metadata records the app name, environment, version, SHA,
deployment directory, deploy time, and source. The source is `github-actions`
for workflow runs and `local` for local runs.

Normal pushes to `main` deploy staging with an automatic build version such as
`staging-1a2b3c4d5e6f`. To create a promotable release, manually run the staging
workflow with a version like `v2.1.0` or `v2.1.0-rc.1`. That staged workflow
deploys the SHA, records `BRAIN_RELEASE_VERSION`, and creates the annotated git
tag at the staged SHA when the version starts with `v`. If the tag already
exists at a different SHA, the staging run fails instead of retagging.

Production promotion does not mint a new version. The release workflow reads
staging `shared/release.json`, verifies the requested version is the active
staged version, verifies the git tag already exists at that exact SHA, checks
that the staging `current` symlink points at the same commit, and then deploys
production with the same `BRAIN_RELEASE_VERSION`.

GitHub Secrets and GitHub Variables are the source of truth. Live config can
still be edited directly for an emergency, but the next deploy for that
environment will fail unless that change has been propagated back to GitHub.

## Config Conflict Rule

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

The renderer ignores metadata keys when it compares configs. The metadata set
includes:

```text
BRAIN_CONFIG_RENDER_SHA
BRAIN_CONFIG_RENDERED_AT
BRAIN_CONFIG_RENDER_SOURCE
BRAIN_RELEASE_ENV
BRAIN_RELEASE_SHA
BRAIN_RELEASE_VERSION
```

After a successful render, both `brain.env` and `brain.env.last-deployed` are
updated to the proposed config.

`force_config_override=true` bypasses the three-way conflict check and
establishes a new baseline. Use it only for an intentional bootstrap or
re-baseline. Otherwise, resolve a conflict by propagating the live change back
to GitHub Secrets/Variables or by intentionally reconciling the environment
back to the last deployed baseline before redeploying.

`BRAIN_AUTH_PASSWORD` is handled similarly, but it is written to the
environment's `shared/secrets/brain-auth-password` with a matching
`brain-auth-password.last-deployed` snapshot.

## Deployment Metadata and Auth Registry

Deployment also configures `BRAIN_AUTH_USERS_FILE` under
`shared/secrets/brain-auth-users.json` and `BRAIN_AUTH_SUPERUSER_IDS=default`.
If the users file does not exist yet, deployment creates one with `default` as a
root superuser and `daniele` as a regular user using the existing shared auth
password. Auth-enabled Brain instances fail closed when the configured registry
is missing. A superuser can create, edit, and delete user records from the
dashboard User Admin tab without restarting the service.

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
/authorize            OAuth authorization endpoint
/token                OAuth token endpoint
/revoke               OAuth token revocation endpoint
/register             OAuth client registration endpoint
/.well-known/oauth-authorization-server
/.well-known/oauth-protected-resource
/.well-known/oauth-protected-resource/{resource_path:path}
/auth/session         session endpoint
/api/session          session endpoint
/mcp                  curated user/app MCP surface
/admin/mcp            full admin MCP surface
/cognee               user Cognee UI entry point
/admin/cognee         root Cognee UI entry point
```

`/app/mcp`, `/ui`, and `/ui-api` remain compatibility aliases, and the Cognee
UI proxy also exposes `/ui-login`, `/ui-logout`, `/cognee-login`, and
`/cognee-logout`.

## Required Secrets

Configure these in GitHub repository secrets for staging and production deploys:

```text
OPENAI_API_KEY
GRAPH_DATABASE_PASSWORD
BRAIN_AUTH_PASSWORD
BRAIN_AUTH_TOKEN
```

`GRAPH_DATABASE_PASSWORD` is treated as required by the renderer. `BRAIN_AUTH_PASSWORD`
is written to each deployed environment's `shared/secrets/brain-auth-password`.
The staging and production workflows also pass `BRAIN_AUTH_TOKEN` into
`render_prod_env.py`.

## Optional Taste Integration Secrets

```text
BRAIN_TASTE_OMDB_API_KEY
BRAIN_TASTE_GOOGLE_PLACES_API_KEY
```

Set these only when the corresponding Taste integrations are enabled.

## Optional Eval Provider Secrets

Runtime uses the configured LLM and embedding provider/model settings.
Set these only when you want explicit eval or smoke experiments against
additional `provider:model` refs:

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

For Bedrock, prefer `AWS_BEARER_TOKEN_BEDROCK` for model-eval experiments. Use
standard AWS credentials only when the Bedrock client path requires SDK auth.

## Optional Slack Secrets

```text
BRAIN_SLACK_SIGNING_SECRET
BRAIN_SLACK_BOT_TOKEN
```

## Recommended Variables

Use GitHub repository variables for non-secret deployment settings:

```text
PROFILE
LLM_PROVIDER
LLM_MODEL
EMBEDDING_PROVIDER
EMBEDDING_MODEL
EMBEDDING_DIMENSIONS
AWS_REGION
AWS_DEFAULT_REGION
AWS_PROFILE
BRAIN_PUBLIC_BASE_URL
BRAIN_APP_MCP_PATH
BRAIN_PUBLIC_MCP_PATH
BRAIN_PUBLIC_APP_MCP_PATH
BRAIN_PUBLIC_ADMIN_MCP_PATH
BRAIN_PUBLIC_UI_PATH
BRAIN_PUBLIC_UI_API_PATH
BRAIN_MCP_PATH
BRAIN_ADMIN_MCP_PATH
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED
BRAIN_GOOGLE_DRIVE_FOLDER
BRAIN_GOOGLE_DRIVE_LOCAL_PATH
BRAIN_NEO4J_DUMP_ENABLED
BRAIN_NEO4J_STOP_FOR_DUMP
BRAIN_REQUEST_LOG_ENABLED
BRAIN_REQUEST_LOG_PATH
BRAIN_REQUEST_LOG_MAX_BODY_BYTES
BRAIN_REQUEST_LOG_RETENTION_DAYS
BRAIN_ROUTING_LOG_ENABLED
BRAIN_ROUTING_LOG_PATH
BRAIN_ROUTING_LOG_RETENTION_DAYS
BRAIN_UI_ENABLED
BRAIN_SLACK_AGENT_ENABLED
BRAIN_SLACK_ALLOWED_TEAM_IDS
BRAIN_SLACK_ALLOWED_CHANNEL_IDS
BRAIN_SLACK_ALLOWED_USER_IDS
BRAIN_SLACK_ADMIN_USER_IDS
BRAIN_AUTH_ENABLED
BRAIN_AUTH_ACCESS_TOKEN_SECONDS
BRAIN_AUTH_REFRESH_TOKEN_SECONDS
BRAIN_AUTH_REQUIRE_PKCE
BRAIN_AUTH_SCOPES
BRAIN_AUTH_STATE_PATH
BRAIN_AUTH_USERS_FILE
BRAIN_AUTH_PASSWORD_FILE
BRAIN_AUTH_SUPERUSER_IDS
BRAIN_BACKUP_DIR
BRAIN_COGNEE_ENABLED
BRAIN_LOG_LEVEL
BRAIN_OWNER_FULL_NAME
BRAIN_OWNER_NAME
BRAIN_PROFILE_CONTEXT_PATH
BRAIN_PROVIDER_AUTH_PROFILES_PATH
BRAIN_PROVIDER_AUTH_STATE_DIR
BRAIN_SERVICE_NAME
BRAIN_USER_ID
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
LLM_MAX_TOKENS
LLM_TEMPERATURE
OPENAI_AUTH_MODE
OPENAI_CODEX_AUTH_PROFILE
OPENAI_CODEX_BASE_URL
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
```

The renderer also reads additional environment variables in staging and prod,
including the broader `BRAIN_COGNEE_*` family and other deployment keys such as
`BRAIN_LAUNCHD_LABEL`, `BRAIN_MCP_HOST`, `BRAIN_MCP_PORT`,
`BRAIN_PROD_ROOT`, `BRAIN_PUBLIC_ADMIN_MCP_PATH`, `BRAIN_TASTE_*`, and the
`BRAIN_SLACK_*` allow-list controls shown above.

## Local Backup

Before moving secrets into GitHub, keep a local gitignored backup under
`local-secrets/`. A generated `github-secrets.env` file can be loaded with:

```bash
gh secret set -f local-secrets/latest/github-secrets.env
```

<!-- brain-doc-source-hash: 9317199594d26a8aadd7caefcf57cd50b589bd358afdd0f791b30936f8772d24 -->
