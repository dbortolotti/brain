# Production Secrets

Deploys run on the self-hosted `brain-prod` runner with three environments:

- `dev`: local developer runs.
- `staging`: `main` deploys through `.github/workflows/deploy-local-staging.yml`
  to `/Volumes/xpg_usb4/staging/brain`.
- `prod`: manual release promotion runs through `.github/workflows/release.yml`
  and deploys the currently deployed staging SHA to `/Volumes/xpg_usb4/prod/brain`,
  then creates an annotated git tag.

`.github/workflows/deploy-local-production.yml` remains available as a manual
production deploy escape hatch. It is not triggered by pushes to `main`.

The workflows render each environment's `shared/secrets/brain.env` from GitHub
Secrets and GitHub Variables before running `scripts/deploy-local-production.sh`
with `BRAIN_DEPLOY_ENV=staging` or `BRAIN_DEPLOY_ENV=prod`.

GitHub Secrets and Variables are the source of truth. Live config can still be
edited directly for an emergency, but the next deploy for that environment will
fail unless that change has been propagated back to GitHub.

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

After a successful render, both `brain.env` and `brain.env.last-deployed` are
updated to the proposed config.

The GitHub Actions staging, production, and release workflows expose
`force_config_override` only as an explicit manual-dispatch option, and it
defaults to `false`. Normal push deploys and manual deploys without that option
enabled use the conflict rule above.

Use `force_config_override=true` only for an intentional bootstrap or
re-baseline. Otherwise, resolve a conflict by propagating the live change back
to GitHub Secrets/Variables or by intentionally reconciling the environment back
to the last deployed baseline before redeploying.

## Live Model Smoke

After deployment, staging and production run `scripts/live_model_smoke.py` against the
configured live model scope. By default this is `active`, which calls the active
`LLM_PROVIDER`/`LLM_MODEL` and `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL` with tiny
requests. Set repository variable `BRAIN_MODEL_SMOKE_SCOPE` to control deploys:

```text
active   current configured LLM and embedding models
none     disable live provider smoke
```

Normal smoke runs fail on missing credentials.

The generated config includes metadata for diagnostics:

```text
BRAIN_CONFIG_RENDER_SHA
BRAIN_CONFIG_RENDERED_AT
BRAIN_CONFIG_RENDER_SOURCE
```

These metadata keys are ignored during conflict comparison.

`BRAIN_AUTH_PASSWORD` is handled similarly, but is written to the environment's
`shared/secrets/brain-auth-password` with a matching
`brain-auth-password.last-deployed` snapshot.

## Required Secrets

Set these in GitHub repository secrets:

```text
OPENAI_API_KEY
GRAPH_DATABASE_PASSWORD
BRAIN_AUTH_PASSWORD
```

`BRAIN_AUTH_PASSWORD` is written to each deployed environment's
`shared/secrets/brain-auth-password`.

Deployment also configures `BRAIN_AUTH_USERS_FILE` under
`shared/secrets/brain-auth-users.json` and `BRAIN_AUTH_SUPERUSER_IDS=default`.
If the users file does not exist yet, deployment creates one with `default` as a
root superuser and `daniele` as a regular user using the existing shared auth
password. Auth-enabled Brain instances fail closed when the configured registry
is missing. A superuser can create and edit user records from the dashboard User
Admin tab without restarting the service.

Dashboard browser sessions are stored as opaque server-side records in
`shared/secrets/brain-web-sessions.json`. The browser receives only a
`Secure`, `HttpOnly`, `SameSite=Lax` session cookie plus an in-memory CSRF token
from `/auth/session`; OAuth bearer tokens remain reserved for MCP clients.

## Optional Eval Provider Secrets

Runtime uses the configured OpenAI LLM and local FastEmbed embedding model.
Set these only when you want explicit eval/smoke experiments against additional
`provider:model` refs:

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
BRAIN_PUBLIC_BASE_URL
BRAIN_APP_MCP_PATH
BRAIN_PUBLIC_MCP_PATH
BRAIN_PUBLIC_APP_MCP_PATH
BRAIN_PUBLIC_UI_PATH
BRAIN_PUBLIC_UI_API_PATH
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED
BRAIN_GOOGLE_DRIVE_FOLDER
BRAIN_GOOGLE_DRIVE_LOCAL_PATH
BRAIN_NEO4J_DUMP_ENABLED
BRAIN_NEO4J_STOP_FOR_DUMP
BRAIN_REQUEST_LOG_ENABLED
BRAIN_REQUEST_LOG_MAX_BODY_BYTES
BRAIN_UI_ENABLED
BRAIN_SLACK_AGENT_ENABLED
BRAIN_SLACK_ALLOWED_TEAM_IDS
BRAIN_SLACK_ALLOWED_CHANNEL_IDS
BRAIN_SLACK_ALLOWED_USER_IDS
BRAIN_SLACK_ADMIN_USER_IDS
```

## Local Backup

Before moving secrets into GitHub, keep a local gitignored backup under
`local-secrets/`. A generated `github-secrets.env` file can be loaded with:

```bash
gh secret set -f local-secrets/latest/github-secrets.env
```
