# ChatGPT App Hardening

Brain exposes the curated public ChatGPT App MCP surface at `/mcp`. `/app/mcp` remains a legacy alias for older clients. In production, the public app and admin MCP URLs are configured by `BRAIN_PUBLIC_BASE_URL` together with `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_APP_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`. The public app MCP URL is the configured public base URL plus `BRAIN_PUBLIC_MCP_PATH`; the legacy app alias uses `BRAIN_PUBLIC_APP_MCP_PATH`, and the admin surface uses `BRAIN_PUBLIC_ADMIN_MCP_PATH`. This surface is curated for user-facing memory workflows and excludes admin tools, raw Cognee primitives, hard-delete operations, and `brain_agent_memory_clear`. The public app includes the curated ChatGPT App tool set listed below, including Palate read and interaction tools, `brain_ingest_source`, `brain_agent_memory`, and `brain_agent_memory_recall`; internal admin-only Palate persistence tools stay on `/admin/mcp`. The internal `/admin/mcp` surface also exposes `brain_app_open_review_panel`; the public app surface does not. Production verification checks the ChatGPT App tool descriptors and confirms the public app component resource (`ui://brain/review.v2.html`) remains text-only.

## Public App Tools

The public ChatGPT App surface includes exactly these tools:

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

## Confirmation And Audit

`brain_remember` opens in preview mode on `/mcp`. Saving the preview requires explicit user confirmation before the write is committed.

Destructive app-surface calls such as `brain_undo_last` and `brain_profile_context_forget` require explicit confirmation. Profile context writes and profile context deletes also require explicit confirmation. App-surface write attempts are rate-limited using `BRAIN_APP_WRITE_RATE_LIMIT_COUNT` and `BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS`, and append a redacted audit record with the tool name, OAuth client id when available, request id, target id, confirmation flag, status, and short summary. Raw memory text is not stored in the app write audit table.

Do not bypass confirmation or normal backup checks in production promotion paths.

## Authentication And Transport

Browser dashboard auth uses `/login`, an HTTP-only session cookie, and per-session CSRF tokens from `/auth/session` (with `/api/session` as a compatibility alias). MCP clients use OAuth bearer tokens. User-registry passwords are stored as Argon2id hashes; legacy plaintext user records are migrated after successful login or by running:

```bash
uv run python scripts/migrate_auth_user_passwords.py --env-file /path/to/brain.env
```

Use `--check` to fail deployment verification when any user still needs migration.

Production auth is configured through `BRAIN_AUTH_ENABLED`, `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_SCOPES`, `BRAIN_AUTH_REQUIRE_PKCE`, `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_USERS_FILE`, and `BRAIN_AUTH_SUPERUSER_IDS`.

Public dashboard, legal, and app-asset responses include Content Security Policy, HSTS, Referrer Policy, Permissions Policy, and `X-Content-Type-Options`. The CSP includes `frame-ancestors` entries for ChatGPT/OpenAI hosts so the app component can be framed by ChatGPT while excluding arbitrary embedding.

## User Controls

The dashboard exposes Review, Recall, Remember, Profile, Prompt, Data Controls, Account, Users, and Help tabs. The Data Controls tab calls `brain_app_data_controls` to show App Write Audit, Export Preview, Profile Data, and Recent Memory Data. The Review tab shows Recent Cards and Open Loops. The Profile tab is editable, and profile-context forget actions require explicit confirmation before the MCP call.

The Prompt tab surfaces Personal Info In Session, Custom Preprompt Instructions, Latest Session Data, Bias Protocol, and Agent Memory Protocol.

Recent-memory, profile-context, open-loop, and app-write review are available through model-visible MCP tools and the authenticated browser dashboard, while account administration and system administration remain outside the public app MCP surface.

## Submission Readiness

Before submitting Brain as a ChatGPT App, complete the non-code submission assets:

- App name, description, icon, category, and support contact.
- Public privacy, terms, and support URLs on the production host.
- A short reviewer test path using a dedicated non-admin verifier user.
- Clear explanation that memory writes preview first and require explicit confirmation.
- Confirmation that admin tools, raw Cognee operations, hard-delete tools, `brain_agent_memory_clear`, tokens, secrets, and password hashes are not exposed on the public app surface.
- Confirmation that the ChatGPT App tool descriptors match the release and the public app component resource (`ui://brain/review.v2.html`) remains text-only.
- Production verification output from `make prod-check` and `uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared`.

## Operator Checklist

Workflow reference:

- `Validate` runs on `pull_request` and `workflow_dispatch`.
- `Deploy Local QA` runs on `push` and `workflow_dispatch`; manual dispatch accepts `force_config_override`.
- `Deploy Local Staging` runs on `workflow_dispatch`; manual dispatch requires `version` and accepts `force_config_override`.
- `Release` runs on `workflow_dispatch`; manual dispatch accepts `version` and `force_config_override`.

After every merge or push to `main`:

1. Watch the `Deploy Local QA` GitHub Actions run to completion.
   - The workflow triggers on `push` and `workflow_dispatch`.
   - Manual dispatch accepts `force_config_override`.
2. Verify the deployed release metadata matches the expected pushed release.
3. Keep your normal backup checks in the promotion path if they are part of your environment.

For a production release:

1. Run the manual `Deploy Local Staging` workflow with the desired `vX.Y.Z` tag; it updates generated docs, stamps the docs with that tag, pushes the docs commit to `main`, deploys staging, and creates the tag.
2. Run the manual `Release` GitHub Actions workflow with the same staged tag.
   - The workflow triggers on `workflow_dispatch`.
   - Manual dispatch accepts `version` and `force_config_override` inputs.
3. Watch production deployment and verification finish successfully.
4. Run `uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared` with the production environment loaded.
   - This verification checks DNS and TLS for the hostname; the public and admin MCP surfaces; the public dashboard, privacy, terms, and support pages; browser security headers; OAuth protected-resource and authorization metadata; and the ChatGPT App tool descriptors. When auth is enabled, it also checks the authenticated public app MCP surface and confirms it remains text-only.
   - For hashed user registries, set `BRAIN_VERIFIER_USER_ID` and `BRAIN_VERIFIER_PASSWORD_FILE` or `BRAIN_AUTH_VERIFIER_USER_ID` and `BRAIN_AUTH_VERIFIER_PASSWORD_FILE` before running the authenticated verifier.
5. Confirm the deployed release metadata matches the tagged release.

<!-- brain-doc-source-hash: b9ab74c176413cc8c26295101123d2cba501598166b3cc5e6cf57c9732ad1548 -->
