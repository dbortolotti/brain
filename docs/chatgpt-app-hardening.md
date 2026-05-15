# ChatGPT App Hardening

Brain exposes the public app MCP surface at `/app/mcp`. This surface is curated
for user-facing memory workflows and excludes admin, raw Cognee, hard-delete,
agent-memory-clear, and Palate write tools.

## Public App Tools

Read-only tools advertise and require `brain.memory.read`:

- `brain_session`
- `brain_recall`
- `brain_profile_entity`
- `brain_list_open_loops`
- `brain_get_memory`
- `brain_review_recent`
- `brain_profile_context_list`
- `brain_app_data_controls`

Write or destructive tools advertise and require `brain.memory.read` and
`brain.memory.write`:

- `brain_remember`
- `brain_profile_context_remember`
- `brain_profile_context_forget`
- `brain_undo_last`

## Confirmation And Audit

`brain_remember` previews by default on `/app/mcp`. Saving requires explicit user
confirmation via either `context.confirmed_by_user=true` or top-level
`confirmed_by_user=true`.

Profile context writes, profile context deletes, and undo also require explicit
confirmation. App-surface write attempts are rate-limited and append a redacted
audit record with the tool name, OAuth client id when available, request id,
target id, confirmation flag, status, and short summary. Raw memory text is not
stored in the app write audit table.

## User Controls

The dashboard Data Controls tab calls `brain_app_data_controls` to show recent
app writes, profile context, custom preprompt items, recent memories, and open
loops. Profile/preprompt items remain editable through the Profile and Prompt
tabs, and deletes require browser confirmation before calling the confirmed MCP
delete.

## Operator Checklist

After every merge or push to `main`:

1. Watch the `Deploy Local Production` GitHub Actions run to completion.
2. Run `ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/verify_mcp_production.py --skip-backups`.
3. Run `ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/verify_cloudflare_mcp.py --skip-cloudflared`.
4. Confirm `/Volumes/xpg_usb4/prod/brain/current` points to the pushed release.
