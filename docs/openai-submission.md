# OpenAI Submission Checklist

Brain is deployable as a ChatGPT App only after the production service is live,
verified, and submitted through the OpenAI app review flow. This document tracks
the remaining non-code work.

## Production Requirements

- Production URL: `https://brain.dceb.net`
- Public MCP URL: `https://brain.dceb.net/mcp`
- Admin MCP URL: `https://brain.dceb.net/admin/mcp`
- Privacy URL: `https://brain.dceb.net/privacy`
- Terms URL: `https://brain.dceb.net/terms`
- Support URL: `https://brain.dceb.net/support`
- App component resource: `ui://brain/review.v2.html`

The current verified production release is:

- Version: `v2.0.4`
- Commit: `906f26f00fdb6490123080f1e48e66a8928f70ab`
- Staging workflow:
  `https://github.com/dbortolotti/brain/actions/runs/26003993400`
- Release workflow:
  `https://github.com/dbortolotti/brain/actions/runs/26004028449`

Run these checks after promoting the staged release:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make prod-check
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make cloudflare-verify
```

For authenticated app verification against hashed user registries, configure a
dedicated non-admin verifier account:

```bash
export BRAIN_VERIFIER_USER_ID=brain_verifier
export BRAIN_VERIFIER_PASSWORD_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password
```

Submission-ready copy, reviewer instructions, and screenshots are stored under
`docs/openai-submission-assets/`.

## App Review Narrative

Explain these points in the submission:

- Brain is a private personal-memory service.
- Users authenticate before any memory is read or written.
- Public ChatGPT App tools are curated and exclude system-admin, raw Cognee,
  hard-delete, token, secret, and password-management operations.
- Memory writes preview first and require explicit user confirmation before
  storage or deletion.
- Users can inspect recent writes, profile context, latest session data, open
  loops, and app write audit records.
- Users can change their password and remove user-level profile context in the
  dashboard.
- Superuser-only account and service administration is available only in the
  authenticated browser dashboard, not on the public app MCP surface.

## Assets To Prepare

- App name and short description.
- App icon using the existing Brain icon asset.
- Support contact.
- Reviewer credentials for the non-admin verifier user.
- Screenshots of the embedded ChatGPT component and browser dashboard.
- Latest successful `prod-check` and `cloudflare-verify` output.

## Pre-Submission Gates

- `uv run ruff check src tests scripts`
- `uv run pytest`
- `make docs-check`
- `uv run python scripts/migrate_auth_user_passwords.py --env-file /Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env --check`
- Confirm `https://brain.dceb.net/privacy`, `/terms`, and `/support` load over
  HTTPS with security headers.
- Confirm `tools/list` on `/mcp` lists only the curated ChatGPT App tools.
- Confirm `resources/read` for `ui://brain/review.v2.html` returns
  `text/html;profile=mcp-app` and includes `_meta.ui.csp` plus
  `_meta.ui.domain`.

<!-- brain-doc-source-hash: 663c5ff1dc231de048a73114740d369b200000745c7f4da828565744f5469877 -->
