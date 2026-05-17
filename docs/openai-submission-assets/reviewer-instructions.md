# OpenAI Reviewer Instructions

## App

- Name: Brain
- Production URL: `https://brain.dceb.net`
- MCP URL: `https://brain.dceb.net/mcp`
- Privacy: `https://brain.dceb.net/privacy`
- Terms: `https://brain.dceb.net/terms`
- Support: `https://brain.dceb.net/support`

## Test Account

Use the non-admin reviewer account:

- User id: `brain_verifier`
- Password: paste from
  `/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password`

The reviewer account is intentionally non-admin. It can read and write only its
own Brain data. It cannot access system administration, raw Cognee operations,
hard deletes, backup controls, or other users' data.

## Suggested Review Flow

1. Connect the ChatGPT App to `https://brain.dceb.net/mcp`.
2. Complete OAuth sign-in with the reviewer account.
3. Ask: `Open my Brain review panel.`
4. Ask: `Remember that the verifier prefers concise release notes.`
   Brain should preview the write and require confirmation before storing it.
5. Confirm the write.
6. Ask: `Show my recent Brain memories.`
   The newly confirmed verifier memory should appear.
7. Ask: `Remove the profile context you just added.`
   Brain should require confirmation before deletion.
8. Visit `https://brain.dceb.net/` in a browser and sign in with the same
   reviewer account to inspect dashboard review/profile/account controls.

## Expected Safety Behavior

- Unauthenticated MCP requests fail closed and return Brain OAuth metadata.
- Public app tools are curated for user memory workflows.
- Public app tools exclude system administration, raw Cognee primitives,
  hard-delete operations, token handling, password management, backups, and
  other users' data.
- Public app write/delete actions require explicit confirmation.
- App-facing tool responses redact internal user ids, session ids, OAuth client
  ids, request ids, raw metadata JSON, datasets, timestamps, tokens, and
  password fields.
- Browser dashboard sessions use an HTTP-only cookie and CSRF token.
- User-registry passwords are stored as Argon2id hashes.

## Verification Evidence

- Verified release: `v2.0.4`
- Verified commit: `906f26f00fdb6490123080f1e48e66a8928f70ab`
- Staging workflow: `https://github.com/dbortolotti/brain/actions/runs/26003993400`
- Release workflow: `https://github.com/dbortolotti/brain/actions/runs/26004028449`
- Production local verifier: passed.
- Production public Cloudflare/MCP verifier: passed.
