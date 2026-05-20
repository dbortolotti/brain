# OpenAI Submission Checklist

Brain is deployable as a ChatGPT App only after the production service is live, verified, and submitted through the OpenAI app review flow. This document tracks the remaining non-code work for operators preparing the Brain ChatGPT App submission.

## Production Requirements

- Production URL: `https://brain.dceb.net`
- Public MCP URL: `https://brain.dceb.net/mcp`
- Legacy app MCP alias: `https://brain.dceb.net/app/mcp`
- Admin MCP URL: `https://brain.dceb.net/admin/mcp`
- Privacy URL: `https://brain.dceb.net/privacy`
- Terms URL: `https://brain.dceb.net/terms`
- Support URL: `https://brain.dceb.net/support`
- Current submission mode: text-only ChatGPT App tools.
- The browser dashboard remains available at `https://brain.dceb.net`, and production verification checks DNS and TLS for the hostname, the ChatGPT App tool descriptors, OAuth protected-resource and authorization metadata, the public and admin MCP surfaces, the public dashboard, privacy, terms, and support pages, browser security headers, and that the public app component resource (`ui://brain/review.v2.html`) remains text-only.

In production, the public app and admin MCP URLs are configured by `BRAIN_PUBLIC_BASE_URL` together with `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_APP_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`. The public app MCP URL is the configured public base URL plus `BRAIN_PUBLIC_MCP_PATH`; the legacy app alias uses `BRAIN_PUBLIC_APP_MCP_PATH`, and the admin surface uses `BRAIN_PUBLIC_ADMIN_MCP_PATH`.

The current verified production release should be recorded from the deployed environment:

- Version: `BRAIN_RELEASE_VERSION`
- Commit SHA: `BRAIN_RELEASE_SHA`
- Release environment: `BRAIN_RELEASE_ENV`

Workflow reference:

- `Validate` runs on `pull_request` and `workflow_dispatch`.
- `Deploy Local Staging` runs on `push` and `workflow_dispatch`; manual dispatch accepts `version` and `force_config_override`.
- `Release` runs on `workflow_dispatch`; manual dispatch accepts `version` and `force_config_override`.

Run these checks after promoting the staged release:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make prod-check
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared
```

Do not bypass confirmation or normal backup checks in production promotion paths.

## Reviewer Setup And Auth

Browser dashboard auth uses `/login`, an HTTP-only session cookie, and per-session CSRF tokens from `/auth/session` with `/api/session` as a compatibility alias. MCP clients use OAuth bearer tokens.

User-registry passwords are stored as Argon2id hashes. Legacy plaintext user records are migrated after successful login or by running:

```bash
uv run python scripts/migrate_auth_user_passwords.py --env-file /path/to/brain.env
```

Use `--check` to fail deployment verification when any user still needs migration.

Production auth is configured through `BRAIN_AUTH_ENABLED`, `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_SCOPES`, `BRAIN_AUTH_REQUIRE_PKCE`, `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_USERS_FILE`, and `BRAIN_AUTH_SUPERUSER_IDS`.

For authenticated app verification against hashed user registries, configure a dedicated non-admin verifier account with either pair:

```bash
export BRAIN_VERIFIER_USER_ID=brain_verifier
export BRAIN_VERIFIER_PASSWORD_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password

# or

export BRAIN_AUTH_VERIFIER_USER_ID=brain_verifier
export BRAIN_AUTH_VERIFIER_PASSWORD_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password
```

Public dashboard, legal, and app-asset responses include Content Security Policy, HSTS, Referrer Policy, Permissions Policy, and `X-Content-Type-Options`. The CSP includes `frame-ancestors` entries for ChatGPT/OpenAI hosts so the app component can be framed by ChatGPT while excluding arbitrary embedding.

Do not store passwords, API keys, OAuth tokens, or other secrets in Brain memories. Records are retained until the authenticated user or operator removes them, or until an environment backup/retention policy expires.

## Public App Surface

Brain exposes the curated public ChatGPT App MCP surface at `/mcp`. `/app/mcp` remains a legacy alias for older clients. In production, the public app and admin MCP URLs are configured by `BRAIN_PUBLIC_BASE_URL` together with `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_APP_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`.

This surface is curated for user-facing memory workflows and excludes admin tools, raw Cognee primitives, hard-delete operations, and `brain_agent_memory_clear`. Selected Palate read and interaction tools, plus `brain_ingest_source`, `brain_agent_memory`, and `brain_agent_memory_recall`, are included on the public app surface; internal admin-only Palate persistence tools stay on `/admin/mcp`. The internal `/admin/mcp` surface also exposes `brain_app_open_review_panel`; the public app surface does not. Production verification checks the ChatGPT App tool descriptors and confirms the public app component resource (`ui://brain/review.v2.html`) remains text-only.

ChatGPT App responses are minimized on this surface. They strip internal identifiers such as user ids, session ids, OAuth client ids, request ids, raw metadata JSON, datasets, timestamps, tokens, and password fields.

The public ChatGPT App tools are exactly:

- `brain_session`
- `brain_recall`
- `brain_remember`
- `brain_ingest_source`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_undo_last`
- `brain_profile_context_list`
- `brain_profile_context_remember`
- `brain_profile_context_forget`
- `brain_app_data_controls`
- `brain_agent_memory`
- `brain_agent_memory_recall`
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

These are the only public app MCP tools.

Read-only tools advertise and require `brain.memory.read`:

- `brain_session` — resolves the active user's Brain session identity.
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_profile_context_list`
- `brain_app_data_controls`
- `brain_agent_memory_recall`
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`

Write or mutating tools advertise and require `brain.memory.write` as well:

- `brain_remember`
- `brain_ingest_source`
- `brain_profile_context_remember`
- `brain_profile_context_forget`
- `brain_undo_last`
- `brain_agent_memory`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

`brain_remember` opens in preview mode on `/mcp`. Saving the preview requires explicit user confirmation before the write is committed.

Destructive app-surface calls such as `brain_undo_last` and `brain_profile_context_forget` require explicit confirmation. Profile context writes and profile context deletes also require explicit confirmation.

App-surface write attempts are rate-limited using `BRAIN_APP_WRITE_RATE_LIMIT_COUNT` and `BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS`, and append a redacted audit record with the tool name, OAuth client id when available, request id, target id, confirmation flag, status, and short summary. Raw memory text is not stored in the app write audit table.

## App Review Narrative

Explain these points in the submission:

- Brain is a private personal-memory service.
- Users authenticate before any memory is read or written.
- The public ChatGPT App surface is curated and excludes admin tools, raw Cognee primitives, hard-delete operations, and `brain_agent_memory_clear`.
- Selected Palate read and interaction tools plus `brain_ingest_source`, `brain_agent_memory`, and `brain_agent_memory_recall` are exposed on the public app surface.
- Memory writes preview first and require explicit user confirmation before storage or deletion.
- Users can inspect recent writes, profile context, latest session data, open loops, and app write audit records.
- Users can change their password and remove user-level profile context in the dashboard.
- Superuser-only account and service administration is available only in the authenticated browser dashboard, not on the public app MCP surface.

## Dashboard User Controls

- The dashboard exposes Review, Recall, Remember, Profile, Prompt, Data Controls, Account, Users, and Help tabs.
- The Data Controls tab calls `brain_app_data_controls` to show App Write Audit, Export Preview, Profile Data, and Recent Memory Data.
- The Review tab shows Recent Cards and Open Loops.
- The Profile tab is editable, and profile-context forget actions require explicit confirmation before the MCP call.
- The Prompt tab surfaces Personal Info In Session, Custom Preprompt Instructions, Latest Session Data, Bias Protocol, and Agent Memory Protocol.
- The Account tab supports password changes.
- The authenticated browser dashboard supports recent-memory, profile-context, open-loop, and app-write review, while account administration and system administration remain outside the public app MCP surface.

## Assets To Prepare

- App name, short description, and category.
- App icon using the existing Brain icon asset.
- Support contact: `support@dceb.net`.
- Reviewer credentials for the non-admin verifier user.
- A short reviewer test path using the dedicated verifier account.
- Public privacy, terms, and support URLs on the production host.
- Screenshots are not required for the current text-only submission. Browser dashboard screenshots may be kept as supporting assets.
- Latest successful `prod-check` output.
- Latest successful `verify_cloudflare_mcp.py --skip-cloudflared` output.
- Submission-ready copy, reviewer instructions, and screenshots for the submission package.
- ChatGPT App tool descriptor confirmation, including that the app component resource (`ui://brain/review.v2.html`) remains text-only.

## Pre-Submission Gates

- `uv run ruff check src tests scripts`
- `uv run pytest`
- `make docs-check`
- `uv run python scripts/migrate_auth_user_passwords.py --env-file /Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env --check`
- Confirm `https://brain.dceb.net/privacy`, `/terms`, and `/support` load over HTTPS with security headers.
- Confirm the public app MCP verification passes with `uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared` loaded in the production environment.
- When auth is enabled, set `BRAIN_VERIFIER_USER_ID` and `BRAIN_VERIFIER_PASSWORD_FILE` or `BRAIN_AUTH_VERIFIER_USER_ID` and `BRAIN_AUTH_VERIFIER_PASSWORD_FILE` before running the authenticated verifier.
- Confirm the verifier reports the curated text-only ChatGPT App tool surface, DNS and TLS for the hostname, OAuth protected-resource and authorization metadata, the public and admin MCP surfaces, the public dashboard, privacy, terms, support pages, and browser security headers.
- Confirm the deployed release metadata matches the tagged release.

## Operator Checklist

After every merge or push to `main`:

1. Watch the `Deploy Local Staging` GitHub Actions run to completion.
   - The workflow triggers on `push` and `workflow_dispatch`.
   - Manual dispatch accepts `version` and `force_config_override` inputs.
2. Verify the deployed release metadata matches the expected pushed release.
3. Keep your normal backup checks in the promotion path if they are part of your environment.

For a production release:

1. Run the manual `Release` GitHub Actions workflow with the desired `vX.Y.Z` tag.
   - The workflow triggers on `workflow_dispatch`.
   - Manual dispatch accepts `version` and `force_config_override` inputs.
2. Watch production deployment and verification finish successfully.
3. Run `uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared` with the production environment loaded.
   - This verification checks DNS and TLS for the hostname; the public and admin MCP surfaces; the public dashboard, privacy, terms, and support pages; browser security headers; OAuth protected-resource and authorization metadata; and the ChatGPT App tool descriptors. When auth is enabled, it also checks the authenticated public app MCP surface and confirms it remains text-only.
4. Keep confirmation and normal backup checks enabled in the promotion path.

<!-- brain-doc-source-hash: a5b0b33522731f9cf1e5d6bdd11f079cf47a2e0576f9cc07ca2b57063be5b307 -->
