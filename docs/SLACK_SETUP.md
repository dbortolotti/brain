# Slack Setup Guide

Brain's Slack memory agent is a separate HTTP service from the MCP server. It
verifies Slack request signatures and allowlists before handling any memory
operation. Slack writes are guarded by proposal rules and require confirmation
by default.

For HTTP and MCP client setup, see [API Setup](API_SETUP_GUIDE.md).

## Architecture

```text
Slack app -> public HTTPS URL -> Brain Slack agent on /slack/*
MCP clients -> public or local URL -> Brain MCP server on /mcp
```

Do not route Slack traffic to the MCP server. The Slack agent intentionally does
not serve `/mcp`.

Default local ports:

```text
MCP/HTTP service: http://127.0.0.1:8000
Slack agent:      http://127.0.0.1:8003
```

Slack routes:

```text
GET  /slack/healthz
POST /slack/events
POST /slack/commands
POST /slack/interactions
```

## Prerequisites

1. A Slack workspace where you can create or manage an app.
2. A public HTTPS URL that forwards to the Slack agent.
3. A configured `.env` file for Brain.
4. The Brain database and dependencies initialized with `make setup`.

For local development, use any HTTPS tunnel that can forward to
`127.0.0.1:8003`. In production, route only `/slack/*` to the Slack agent port.

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

`BRAIN_SLACK_SIGNING_SECRET` is required. The server fails closed with `503` if
the agent is enabled but the signing secret is blank or placeholder-shaped.

`BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false` is the safer default. With this
setting, Slack memory writes dry-run first and require confirmation before
committing.

## Create The Slack App

In Slack's app management UI:

1. Create a new app from scratch.
2. Choose the target workspace.
3. Open **Basic Information** and copy the **Signing Secret** into
   `BRAIN_SLACK_SIGNING_SECRET`.
4. Open **OAuth & Permissions** and add the bot scopes needed for your chosen
   surfaces.

Recommended scopes:

```text
commands
chat:write
app_mentions:read
channels:history
groups:history
im:history
mpim:history
```

The exact scopes depend on whether you use only slash commands, app mentions,
DMs, or channel events. Slash-command-only setups can start with `commands` and
the scopes Slack requires for installation.

Install the app to the workspace and copy the bot token into
`BRAIN_SLACK_BOT_TOKEN` if your deployment needs bot-token-backed Slack API
calls.

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
/brain confirm Sam from Goldman prefers morning calls.
/brain cancel tprop_...
/brain correct tprop_... this is a wine
/brain recall What do we know about Sam from Goldman?
/brain profile Sam from Goldman
/brain open-loops Slack
/brain get-memory mem_...
/brain debug snapshot
/brain help
```

`/brain help` returns Block Kit buttons for common command templates. Slack does
not let app buttons insert text into the user's composer directly, so each
button returns a copyable template instead.

The Slack slash command sends form-encoded payloads to `/slack/commands`; Brain
validates the Slack signature before parsing the command text.

## Configure Events

Enable Event Subscriptions and set:

```text
Request URL: https://your-public-host.example.com/slack/events
```

Slack will send a URL verification challenge. Brain responds to
`type=url_verification` after signature verification.

Subscribe to bot events as needed:

```text
app_mention
message.im
```

Use app mentions or DMs for free-form recall/profile/remember routing. The agent
strips bot mentions before parsing the message. Event-based DMs and mentions do
not use Slack's slash-command response channel, so Brain replies by calling
Slack `chat.postMessage`; this requires `BRAIN_SLACK_BOT_TOKEN` and the
`chat:write` bot scope.

## Configure Interactivity

Enable Interactivity & Shortcuts and set:

```text
Request URL: https://your-public-host.example.com/slack/interactions
```

Interactive confirmations are used for proposed Slack memory commits.

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
make slack-agent-check
```

This verifies:

- `/slack/healthz` returns the Slack service identity.
- `/mcp` is not served by the Slack agent.
- invalid Slack signatures fail closed.

You can also pass a base URL directly:

```bash
uv run python scripts/verify_slack_agent.py \
  --base-url https://your-public-host.example.com
```

## Allowlist Setup

Slack requests are rejected before memory handling if they do not match the
configured allowlists.

Use these IDs from Slack, not display names:

```env
BRAIN_SLACK_ALLOWED_TEAM_IDS=T...
BRAIN_SLACK_ALLOWED_CHANNEL_IDS=C...
BRAIN_SLACK_ALLOWED_USER_IDS=U...
BRAIN_SLACK_ADMIN_USER_IDS=U...
```

Leave an allowlist blank only when you intentionally allow all values for that
dimension. For production, set at least team and user allowlists. Set admin
users separately because debug commands are read-only but can expose operational
state.

## Production Notes

Production launchd support is scaffolded in:

```text
deployment/launchd/com.brain.slack-agent.plist.template
```

The README expects the production Slack agent to run under:

```text
com.brain.slack-agent
```

Keep route separation at the reverse proxy or tunnel layer:

```text
/slack/* -> 127.0.0.1:8003
/mcp     -> 127.0.0.1:8000
```

Production secrets and variables are described in
[Production Secrets](production-secrets.md). Slack secrets are:

```text
BRAIN_SLACK_SIGNING_SECRET
BRAIN_SLACK_BOT_TOKEN
```

Slack non-secret deployment variables are:

```text
BRAIN_SLACK_AGENT_ENABLED
BRAIN_SLACK_ALLOWED_TEAM_IDS
BRAIN_SLACK_ALLOWED_CHANNEL_IDS
BRAIN_SLACK_ALLOWED_USER_IDS
BRAIN_SLACK_ADMIN_USER_IDS
```

## Troubleshooting

`503 Slack memory agent is disabled.`

Set `BRAIN_SLACK_AGENT_ENABLED=true` and restart the Slack agent.

`503 Slack signing secret is not configured.`

Set `BRAIN_SLACK_SIGNING_SECRET` to the Slack app signing secret and restart.

`401 Missing Slack signature` or `401 Invalid Slack signature`.

Send traffic through Slack or reproduce Slack's signature calculation exactly.
Normal unsigned `curl` requests to Slack write routes should fail.

`401 Stale Slack timestamp`.

Check system time and tunnel/proxy behavior. Slack signatures are accepted only
within a five-minute freshness window.

`403 Slack team/channel/user is not allowed.`

Add the Slack ID to the relevant allowlist or confirm the request is coming from
the expected workspace, channel, and user.

`Debug tools are admin-only.`

Add the Slack user ID to `BRAIN_SLACK_ADMIN_USER_IDS`.

Slack URL verification fails.

Confirm the Event Subscriptions request URL points to `/slack/events`, the
public URL forwards to the Slack agent port, and the signing secret matches the
Slack app.

<!-- brain-doc-source-hash: 0ddb58a0bafb949ef865f0351e3b89e85b94ece3ca43a95768521c339ff8f1f6 -->
