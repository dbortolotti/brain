# ChatGPT App Hardening

Brain exposes the public ChatGPT App MCP surface at `/mcp`. `/app/mcp` remains a legacy alias for older clients. In production, the public app and admin MCP paths are configured by `BRAIN_PUBLIC_BASE_URL`, `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_APP_MCP_PATH`, and `BRAIN_PUBLIC_ADMIN_MCP_PATH`. The public app MCP URL is the configured public base URL plus `BRAIN_PUBLIC_MCP_PATH`. This surface is curated for user-facing memory workflows and excludes admin tools, raw Cognee primitives, hard-delete operations, and `brain_agent_memory_clear`. Selected Palate read and interaction tools, plus `brain_ingest_source`, are included on the public app surface; internal admin-only Palate persistence tools stay on `/admin/mcp`.

## Public App Tools

The ChatGPT App surface includes exactly these tools:

- `brain_session`
- `brain_remember`
- `brain_ingest_source`
- `brain_profile_context_remember`
- `brain_profile_context_list`
- `brain_profile_context_forget`
- `brain_app_data_controls`
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_undo_last`
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

Read-only tools advertise and require `brain.memory.read`:

- `brain_session` — resolves the active user's Brain session identity.
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_profile_context_list`
- `brain_app_data_controls`
- `brain_palate_describe_item`
- `brain_palate_query`
- `brain_palate_evaluate_options`

Write or mutating tools advertise and require `brain.memory.write` as well:

- `brain_remember`
- `brain_ingest_source`
- `brain_profile_context_remember`
- `brain_profile_context_forget`
- `brain_undo_last`
- `brain_palate_confirm`
- `brain_palate_cancel`
- `brain_palate_correct_proposal`

## Confirmation And Audit

`brain_remember` opens in preview mode on `/mcp`. Saving the preview requires explicit user confirmation before the write is committed.

Destructive app-surface calls such as `brain_undo_last` and `brain_profile_context_forget` require explicit confirmation. Profile context writes and profile context deletes also require explicit confirmation. App-surface write attempts are rate-limited using `BRAIN_APP_WRITE_RATE_LIMIT_COUNT` and `BRAIN_APP_WRITE_RATE_LIMIT_WINDOW_SECONDS`, and append a redacted audit record with the tool name, OAuth client id when available, request id, target id, confirmation flag, status, and short summary. Raw memory text is not stored in the app write audit table.

## User Controls

The dashboard Data Controls tab calls `brain_app_data_controls` to show App Write Audit, Export Preview, Profile Data, and Recent Memory Data. The Review tab shows Recent Cards and Open Loops. Profile and Prompt tabs remain editable, and profile-context forget actions require explicit confirmation before the MCP call.

The Prompt tab surfaces Personal Info In Session, Custom Preprompt Instructions, Latest Session Data, Bias Protocol, and Agent Memory Protocol.

## Operator Checklist

The `Validate` workflow runs on pull requests and manual dispatch.

After every merge or push to `main`:

1. Watch the `Deploy Local Staging` GitHub Actions run to completion.
   - The workflow triggers on `push` and `workflow_dispatch`.
   - Manual dispatch accepts `version` and `force_config_override` inputs.
2. Run `ENV_FILE=/Volumes/xpg_usb4/staging/brain/shared/secrets/brain.env uv run python scripts/verify_mcp_production.py --skip-backups`.
3. Confirm `/Volumes/xpg_usb4/staging/brain/current` points to the pushed release.

For a production release:

1. Run the manual `Release` GitHub Actions workflow with the desired `vX.Y.Z` tag.
   - The workflow triggers on `workflow_dispatch`.
   - Manual dispatch accepts `version` and `force_config_override` inputs.
2. Watch production deployment and verification finish successfully.
3. Run `ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared`.
4. Confirm `/Volumes/xpg_usb4/prod/brain/current` points to the tagged release.

<!-- brain-doc-source-hash: 5bbfcf7176a05e792b72d78da82b99c3b90a0b61450cacc43994460fa2b9c147 -->
