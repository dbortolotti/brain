# Production Secrets

Production deploys run through `.github/workflows/deploy-local-production.yml` on the
self-hosted `brain-prod` runner. The workflow renders
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env` from GitHub Secrets and
GitHub Variables before running `scripts/deploy-local-production.sh`.

GitHub Secrets and Variables are the source of truth. Production config can still
be edited directly for an emergency, but the next deploy will fail unless that
change has been propagated back to GitHub.

## Conflict Rule

The renderer compares three files:

```text
proposed: newly rendered GitHub Secrets/Vars config
prod:     /Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env
base:     /Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env.last-deployed
```

For each non-metadata key:

```text
if proposed == prod:
  no change
elif prod == base:
  prod has not been manually edited; overwrite with proposed
else:
  fail deploy
```

After a successful render, both `brain.env` and `brain.env.last-deployed` are
updated to the proposed config.

The GitHub Actions deploy workflow exposes `force_config_override` only as an
explicit manual-dispatch option, and it defaults to `false`. Normal push deploys,
and manual deploys without that option enabled, use the conflict rule above.

Use `force_config_override=true` only for an intentional bootstrap or
re-baseline. Otherwise, resolve a conflict by propagating the production change
back to GitHub Secrets/Variables or by intentionally reconciling production back
to the last deployed baseline before redeploying.

## Live Model Smoke

After deployment, production runs `scripts/live_model_smoke.py` against the
configured live model scope. By default this is `active`, which calls the active
`LLM_PROVIDER`/`LLM_MODEL` and `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL` with tiny
requests. Set repository variable `BRAIN_MODEL_SMOKE_SCOPE` to control push
deploys:

```text
active   current configured LLM and embedding models
none     disable live provider smoke
```

Manual workflow dispatch exposes the same scope plus
`model_smoke_skip_missing_keys`. Normal smoke runs fail on missing credentials.
Use `skip_missing_keys=true` only when you want to check the providers currently
available without blocking on unfetched keys.

The generated config includes metadata for diagnostics:

```text
BRAIN_CONFIG_RENDER_SHA
BRAIN_CONFIG_RENDERED_AT
BRAIN_CONFIG_RENDER_SOURCE
```

These metadata keys are ignored during conflict comparison.

`BRAIN_AUTH_PASSWORD` is handled similarly, but is written to
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-password` with a matching
`brain-auth-password.last-deployed` snapshot.

## Required Secrets

Set these in GitHub repository secrets:

```text
OPENAI_API_KEY
GRAPH_DATABASE_PASSWORD
BRAIN_AUTH_PASSWORD
```

`BRAIN_AUTH_PASSWORD` is written to
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-password`.

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
