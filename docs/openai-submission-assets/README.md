# Brain OpenAI Submission Assets

This directory contains the working package for submitting Brain as a ChatGPT
App.

## Screenshots

The current public app submission is text-only, so screenshots are not required
by the app review form. Supporting browser-dashboard screenshots are kept in
`screenshots/`:

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

- Version: record the promoted production release used for submission.
- Commit: record the promoted production commit used for submission.
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

Run both checks after the production promotion used for submission and record
the result in the reviewer notes.
