# Brain OpenAI Submission Assets

This directory contains the working package for submitting Brain as a ChatGPT
App.

## Screenshots

Current public screenshots are in `screenshots/`:

- `01-dashboard-login.png`
- `02-privacy.png`
- `03-terms.png`
- `04-support.png`

Regenerate them with:

```bash
scripts/capture_openai_submission_screenshots.sh
```

Set `BRAIN_SUBMISSION_BASE_URL` to capture staging instead of production.

## Demo Recording

Use the public MP4 recording for the submission demo:

- `openai-demo.mp4`
- Public URL after push:
  `https://raw.githubusercontent.com/dbortolotti/brain/main/docs/openai-submission-assets/openai-demo.mp4`

## Reviewer Credentials

Use the dedicated non-admin verifier account:

- User id: `brain_verifier`
- Password file: `/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password`

Do not commit the password value. Paste it only into the OpenAI submission
portal reviewer-credentials field.

## Verified Release

- Version: `v2.0.4`
- Commit: `906f26f00fdb6490123080f1e48e66a8928f70ab`
- Production URL: `https://brain.dceb.net`
- Public MCP URL: `https://brain.dceb.net/mcp`
- Privacy URL: `https://brain.dceb.net/privacy`
- Terms URL: `https://brain.dceb.net/terms`
- Support URL: `https://brain.dceb.net/support`
- Staging workflow: `https://github.com/dbortolotti/brain/actions/runs/26003993400`
- Release workflow: `https://github.com/dbortolotti/brain/actions/runs/26004028449`

## Verification Commands

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env \
  uv run python scripts/verify_mcp_production.py

ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env \
BRAIN_VERIFIER_USER_ID=brain_verifier \
BRAIN_VERIFIER_PASSWORD_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password \
  uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared
```

Both checks passed after the `v2.0.4` production promotion.
