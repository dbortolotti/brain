# Slack Setup Guide

Brain's Slack memory agent is a separate HTTP service from the main Brain/MCP surface. It verifies Slack request signatures and configured allowlists before handling memory operations. Slack writes use proposal rules and confirmation flows, and `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false` is the safer setting.

## Architecture

```text
Slack app -> public HTTPS URL -> Brain Slack agent on /slack/*
MCP clients -> public or local URL -> Brain MCP server on /mcp
```

Do not route Slack traffic to the MCP server. The Slack agent intentionally does not serve `/mcp`.

Local service endpoints are configured with the Brain MCP host/port and Slack agent host/port settings:

```text
MCP/HTTP service: http://{BRAIN_MCP_HOST}:{BRAIN_MCP_PORT}
Slack agent:      http://{BRAIN_SLACK_AGENT_HOST}:{BRAIN_SLACK_AGENT_PORT}
```

Slack agent routes:

```text
GET  /slack/healthz
POST /slack/events
POST /slack/commands
POST /slack/interactions
```

The Slack agent also serves FastAPI documentation endpoints:

```text
GET /docs
GET /docs/oauth2-redirect
GET /openapi.json
GET /redoc
```

## Prerequisites

1. A Slack workspace where you can create or manage an app.
2. A public HTTPS URL that forwards to the Slack agent.
3. A configured `.env` file for Brain.
4. The Brain database and dependencies initialized with `make setup`.

For local development, use a tunnel or reverse proxy that forwards to the Slack agent host and port. In production, route only `/slack/*` to the Slack agent port.

## Configure Brain

Set these values in `.env` or your production environment:

```env
BRAIN_SLACK_ENABLED=true
BRAIN_SLACK_AGENT_ENABLED=true
BRAIN_SLACK_AGENT_HOST=127.0.0.1
BRAIN_SLACK_AGENT_PORT=8003
BRAIN_SLACK_SIGNING_SECRET=0123456789abcdef0123456789abcdef
BRAIN_SLACK_BOT_TOKEN=xoxb-...
BRAIN_SLACK_ALLOWED_TEAM_IDS=T0123456789
BRAIN_SLACK_ALLOWED_CHANNEL_IDS=C0123456789
BRAIN_SLACK_ALLOWED_USER_IDS=U0123456789,U0987654321
BRAIN_SLACK_ADMIN_USER_IDS=U0123456789
BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false
```

Use comma-separated values for multiple teams, channels, users, or admins.

`BRAIN_SLACK_ENABLED` turns on Slack integration, and `BRAIN_SLACK_AGENT_ENABLED` starts the Slack HTTP service.

`BRAIN_SLACK_SIGNING_SECRET` is required. The server fails closed with `503` if the agent is enabled but the signing secret is blank or placeholder-shaped.

`BRAIN_SLACK_BOT_TOKEN` is only required if you want event-based replies from mentions or DMs, because the agent posts those responses with `chat.postMessage`.

`BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false` is the safer default. With this setting, Slack memory writes use the proposal and confirmation flow before committing.

## Create The Slack App

In Slack's app management UI:

1. Create or open the app for your workspace.
2. Copy the app Signing Secret into `BRAIN_SLACK_SIGNING_SECRET`.
3. Configure the slash-command, event subscription, and interactivity Request URLs to point at the Slack agent routes.
4. Install the app to the workspace.
5. Copy the bot token into `BRAIN_SLACK_BOT_TOKEN` if you want event-based replies from mentions or DMs.

## Configure Slash Commands

Create a slash command:

```text
Command: /brain
Request URL: https://your-public-host.example.com/slack/commands
Short Description: Brain memory
Usage Hint: remember <text>
```

Example commands:

```text
/brain remember Sam from Goldman prefers morning calls.
/brain recall What do we know about Sam from Goldman?
/brain profile Sam from Goldman
/brain open-loops Slack
/brain get-memory mem_...
/brain review
/brain undo-last
/brain confirm Sam from Goldman prefers morning calls.
/brain cancel tprop_...
/brain correct tprop_... this is a wine
/brain help
```

`/brain help` returns Block Kit buttons for common command templates.

The Slack slash command sends form-encoded payloads to `/slack/commands`; Brain validates the Slack signature before parsing the command text. The handler combines the `command` and `text` fields into a single command string before routing it, so the command text should be written the way you want Brain to interpret it, for example `/brain remember ...`.

## Configure Events

Enable Event Subscriptions and set:

```text
Request URL: https://your-public-host.example.com/slack/events
```

Slack will send a URL verification challenge. Brain responds to `type=url_verification` after signature verification.

The Slack agent ignores events with `bot_id` and ignores bot messages and message edits/deletions with the `bot_message`, `message_deleted`, and `message_changed` subtypes.

Subscribe to bot events as needed:

```text
app_mention
message.im
```

Use app mentions or DMs for free-form recall/profile/remember routing. The agent strips bot mentions before parsing the message. Event-based DMs and mentions do not use Slack's slash-command response channel, so Brain replies by calling Slack `chat.postMessage`; this requires `BRAIN_SLACK_BOT_TOKEN`. If the original event includes a thread timestamp, Brain posts the reply in that thread.

## Configure Interactivity

Enable Interactivity & Shortcuts and set:

```text
Request URL: https://your-public-host.example.com/slack/interactions
```

Interactive confirmations are used for proposed Slack memory commits, taste proposal actions, and help-template buttons. The Slack agent reads the interactive `payload` form field, so the endpoint must receive Slack's form-encoded interaction payloads. The first action in the payload is parsed, and its `value` must be JSON containing fields such as `proposed_memory`, `taste_proposal_id`, `taste_action`, or `help_command`.

## Start The Services Locally

Start the Brain MCP/HTTP service in one terminal:

```bash
make mcp-http
```

Start the Slack agent in another terminal:

```bash
make slack-agent
```

Check health:

```bash
curl http://127.0.0.1:8003/slack/healthz
```

Expected shape:

```json
{
  "status": "ok",
  "service": "brain-slack-agent",
  "enabled": true
}
```

## Verify The Slack Agent

With the Slack agent running:

```bash
uv run python scripts/verify_slack_agent.py
```

You can also pass a base URL directly:

```bash
uv run python scripts/verify_slack_agent.py \
  --base-url https://your-public-host.example.com
```

This verifies:

- `/slack/healthz` returns the Slack service identity.
- `/mcp` is not served by the Slack agent.
- invalid Slack signatures fail closed with `401` or `503`.

## Allowlist Setup

Slack requests are rejected before memory handling if they do not match the configured allowlists.

Use these IDs from Slack, not display names:

```env
BRAIN_SLACK_ALLOWED_TEAM_IDS=T...
BRAIN_SLACK_ALLOWED_CHANNEL_IDS=C...
BRAIN_SLACK_ALLOWED_USER_IDS=U...
BRAIN_SLACK_ADMIN_USER_IDS=U...
```

Set admin users separately from the general allowlists. The same allowlists are applied before memory handling on Slack requests.

## Production Notes

Keep route separation at the reverse proxy or tunnel layer:

```text
/slack/* -> 127.0.0.1:8003
/mcp     -> 127.0.0.1:8000
```

Treat `BRAIN_SLACK_SIGNING_SECRET` and `BRAIN_SLACK_BOT_TOKEN` as secrets.

Slack non-secret deployment variables are:

```text
BRAIN_SLACK_ENABLED
BRAIN_SLACK_AGENT_ENABLED
BRAIN_SLACK_AGENT_HOST
BRAIN_SLACK_AGENT_PORT
BRAIN_SLACK_ALLOWED_TEAM_IDS
BRAIN_SLACK_ALLOWED_CHANNEL_IDS
BRAIN_SLACK_ALLOWED_USER_IDS
BRAIN_SLACK_ADMIN_USER_IDS
BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE
```

## Troubleshooting

`503 Slack memory agent is disabled.`

Set `BRAIN_SLACK_AGENT_ENABLED=true` and restart the Slack agent.

`503 Slack signing secret is not configured.`

Set `BRAIN_SLACK_SIGNING_SECRET` to the Slack app signing secret and restart.

`401 Missing Slack signature` or `401 Invalid Slack signature`.

Send traffic through Slack or reproduce Slack's signature calculation exactly. Normal unsigned `curl` requests to Slack write routes should fail.

`401 Invalid Slack timestamp`.

Check the request timestamp and header parsing. Slack signatures require an integer timestamp.

`401 Stale Slack timestamp`.

Check system time and tunnel/proxy behavior. Slack signatures are accepted only within a five-minute freshness window.

`403 Slack team/channel/user is not allowed.`

Add the Slack ID to the relevant allowlist or confirm the request is coming from the expected workspace, channel, and user.

Slack URL verification fails.

Confirm the Event Subscriptions request URL points to `/slack/events`, the public URL forwards to the Slack agent port, and the signing secret matches the Slack app.

<!-- brain-doc-source-hash: 1ce23ed8de294dfc5d58fd6a74cdb0a6a81afa85a85b8d4ef4df11a4a0973741 -->
