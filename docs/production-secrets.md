# Production Secrets

Production deploys run through `.github/workflows/deploy-local-production.yml` on the
self-hosted `brain-prod` runner. The workflow renders
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env` from GitHub Secrets and
GitHub Variables before running `scripts/deploy-local-production.sh`.

The renderer preserves existing values when a GitHub Secret or Variable is empty, so
adding the workflow does not blank a working local production config.

## Required Secrets

Set these in GitHub repository secrets:

```text
OPENAI_API_KEY
GRAPH_DATABASE_PASSWORD
BRAIN_AUTH_PASSWORD
```

`BRAIN_AUTH_PASSWORD` is written to
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-password`.

## Optional Model Provider Secrets

Set these when you want the full model registry available:

```text
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
BRAIN_PUBLIC_MCP_PATH
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
