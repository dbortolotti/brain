from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qs

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from memory_stack.config import Settings, load_settings
from memory_stack.slack_memory_agent import SlackAgentRequest, SlackMemoryAgent


settings = load_settings()
app = FastAPI(title="Brain Slack Memory Agent", version="0.1.0")


@app.get("/slack/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "brain-slack-agent",
        "enabled": settings.brain_slack_agent_enabled,
    }


@app.post("/slack/events")
async def slack_events(
    request: Request,
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
) -> JSONResponse:
    body = await request.body()
    verify_slack_request(body, x_slack_signature, x_slack_request_timestamp, settings)
    payload = await request.json()
    if payload.get("type") == "url_verification":
        return JSONResponse({"challenge": payload.get("challenge")})

    event = payload.get("event") or {}
    if should_ignore_event(event):
        return JSONResponse({"ok": True, "ignored": True})

    slack_request = SlackAgentRequest(
        text=strip_bot_mention(str(event.get("text") or "")),
        user_id=str(event.get("user") or payload.get("user_id") or ""),
        channel_id=str(event.get("channel") or payload.get("channel_id") or ""),
        team_id=str(payload.get("team_id") or event.get("team") or ""),
        thread_ts=event.get("thread_ts"),
        message_ts=event.get("ts"),
        source="event",
    )
    require_slack_allowlist(slack_request, settings)
    response = SlackMemoryAgent(settings).handle(slack_request)
    posted = await post_slack_message(
        settings,
        channel=slack_request.channel_id,
        response=response.as_slack_payload(),
        thread_ts=slack_request.thread_ts,
    )
    return JSONResponse({"ok": True, "posted": posted})


@app.post("/slack/commands")
async def slack_commands(
    request: Request,
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
) -> JSONResponse:
    body = await request.body()
    verify_slack_request(body, x_slack_signature, x_slack_request_timestamp, settings)
    form = parse_qs(body.decode("utf-8"))
    slack_request = SlackAgentRequest(
        text=f"{_form_value(form, 'command')} {_form_value(form, 'text')}".strip(),
        user_id=_form_value(form, "user_id"),
        channel_id=_form_value(form, "channel_id"),
        team_id=_form_value(form, "team_id"),
        thread_ts=_form_value(form, "thread_ts") or None,
        message_ts=_form_value(form, "trigger_id") or None,
        source="slash_command",
    )
    require_slack_allowlist(slack_request, settings)
    response = SlackMemoryAgent(settings).handle(slack_request)
    return JSONResponse(response.as_slack_payload())


@app.post("/slack/interaction")
@app.post("/slack/interactions")
async def slack_interactions(
    request: Request,
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
) -> JSONResponse:
    body = await request.body()
    verify_slack_request(body, x_slack_signature, x_slack_request_timestamp, settings)
    form = parse_qs(body.decode("utf-8"))
    payload = json.loads(_form_value(form, "payload") or "{}")
    user = payload.get("user") or {}
    channel = payload.get("channel") or {}
    team = payload.get("team") or {}
    action = (payload.get("actions") or [{}])[0]
    action_value = json.loads(action.get("value") or "{}")
    proposed_memory = action_value.get("proposed_memory")
    help_command = action_value.get("help_command")
    slack_request = SlackAgentRequest(
        text=f"help-template {help_command}" if help_command else "confirm",
        user_id=str(user.get("id") or ""),
        channel_id=str(channel.get("id") or ""),
        team_id=str(team.get("id") or ""),
        thread_ts=(payload.get("message") or {}).get("thread_ts"),
        message_ts=(payload.get("message") or {}).get("ts"),
        source="interaction",
        confirmed=help_command is None,
        proposed_memory=proposed_memory,
        help_command=help_command,
    )
    require_slack_allowlist(slack_request, settings)
    response = SlackMemoryAgent(settings).handle(slack_request)
    return JSONResponse(response.as_slack_payload())


def verify_slack_request(
    body: bytes,
    signature: str | None,
    timestamp: str | None,
    active_settings: Settings,
    *,
    now: int | None = None,
) -> None:
    if not active_settings.brain_slack_agent_enabled:
        raise HTTPException(status_code=503, detail="Slack memory agent is disabled.")
    if is_placeholder_secret(active_settings.brain_slack_signing_secret):
        raise HTTPException(status_code=503, detail="Slack signing secret is not configured.")
    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing Slack signature.")
    try:
        timestamp_int = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Slack timestamp.") from exc
    active_now = now or int(time.time())
    if abs(active_now - timestamp_int) > 60 * 5:
        raise HTTPException(status_code=401, detail="Stale Slack timestamp.")

    base = f"v0:{timestamp}:{body.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(
        active_settings.brain_slack_signing_secret.encode("utf-8"),
        base,
        hashlib.sha256,
    ).hexdigest()
    expected = f"v0={digest}"
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature.")


def should_ignore_event(event: dict[str, Any]) -> bool:
    return bool(
        event.get("bot_id")
        or event.get("subtype") in {"bot_message", "message_deleted", "message_changed"}
    )


async def post_slack_message(
    active_settings: Settings,
    *,
    channel: str,
    response: dict[str, Any],
    thread_ts: str | None = None,
) -> bool:
    if not active_settings.brain_slack_bot_token:
        return False
    payload: dict[str, Any] = {
        "channel": channel,
        "text": str(response.get("text") or ""),
    }
    if response.get("blocks"):
        payload["blocks"] = response["blocks"]
    if thread_ts:
        payload["thread_ts"] = thread_ts
    async with httpx.AsyncClient(timeout=10) as client:
        slack_response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {active_settings.brain_slack_bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
        )
    if slack_response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Slack chat.postMessage failed: HTTP {slack_response.status_code}",
        )
    try:
        data = slack_response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Slack chat.postMessage returned invalid JSON.") from exc
    if not data.get("ok"):
        raise HTTPException(
            status_code=502,
            detail=f"Slack chat.postMessage failed: {data.get('error', 'unknown_error')}",
        )
    return True


def require_slack_allowlist(slack_request: SlackAgentRequest, active_settings: Settings) -> None:
    if active_settings.brain_slack_allowed_team_id_list and (
        slack_request.team_id not in active_settings.brain_slack_allowed_team_id_list
    ):
        raise HTTPException(status_code=403, detail="Slack team is not allowed.")
    if active_settings.brain_slack_allowed_channel_id_list and (
        slack_request.channel_id not in active_settings.brain_slack_allowed_channel_id_list
    ):
        raise HTTPException(status_code=403, detail="Slack channel is not allowed.")
    if active_settings.brain_slack_allowed_user_id_list and (
        slack_request.user_id not in active_settings.brain_slack_allowed_user_id_list
    ):
        raise HTTPException(status_code=403, detail="Slack user is not allowed.")


def is_placeholder_secret(value: str | None) -> bool:
    return not value or value.strip().lower() in {"replace-me", "change-me", "changeme"}


def strip_bot_mention(text: str) -> str:
    return " ".join(part for part in text.split() if not part.startswith("<@"))


def _form_value(form: dict[str, list[str]], key: str) -> str:
    values = form.get(key)
    return values[0] if values else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=settings.brain_slack_agent_host)
    parser.add_argument("--port", type=int, default=settings.brain_slack_agent_port)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "memory_stack.slack_agent_server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
