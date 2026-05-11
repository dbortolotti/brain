from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from memory_stack.config import Settings
from memory_stack import slack_agent_server
from memory_stack.slack_agent_server import app, verify_slack_request


def test_invalid_slack_signature_returns_unauthorized(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path)
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    body = {"type": "url_verification", "challenge": "ok"}

    response = client.post(
        "/slack/events",
        json=body,
        headers={
            "X-Slack-Request-Timestamp": str(int(time.time())),
            "X-Slack-Signature": "v0=bad",
        },
    )

    assert response.status_code == 401


def test_placeholder_slack_signing_secret_fails_closed(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path, brain_slack_signing_secret="replace-me")
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    body = {"type": "url_verification", "challenge": "ok"}

    response = client.post(
        "/slack/events",
        json=body,
        headers={
            "X-Slack-Request-Timestamp": str(int(time.time())),
            "X-Slack-Signature": "v0=bad",
        },
    )

    assert response.status_code == 503


def test_stale_slack_timestamp_is_rejected(tmp_path) -> None:
    settings = slack_settings(tmp_path)
    body = b"{}"
    stale = "1700000000"
    signature = slack_signature(settings.brain_slack_signing_secret, stale, body)

    try:
        verify_slack_request(body, signature, stale, settings, now=1700001000)
    except Exception as exc:
        assert getattr(exc, "status_code") == 401
    else:
        raise AssertionError("Expected stale Slack timestamp to be rejected.")


def test_non_allowlisted_user_is_rejected(tmp_path, monkeypatch) -> None:
    settings = slack_settings(
        tmp_path,
        brain_slack_allowed_user_ids="U2",
    )
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    body = json.dumps(
        {
            "type": "event_callback",
            "team_id": "T1",
            "event": {"text": "recall Bill Evans", "user": "U1", "channel": "C1"},
        }
    ).encode("utf-8")

    response = client.post(
        "/slack/events",
        content=body,
        headers=signed_headers(settings, body),
    )

    assert response.status_code == 403


def test_slack_dm_event_posts_response_with_bot_token(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path, brain_slack_bot_token="xoxb-test")
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    posted: list[dict[str, object]] = []

    async def fake_post_slack_message(settings, *, channel, response, thread_ts=None):
        posted.append(
            {
                "settings": settings,
                "channel": channel,
                "response": response,
                "thread_ts": thread_ts,
            }
        )
        return True

    monkeypatch.setattr(slack_agent_server, "post_slack_message", fake_post_slack_message)
    client = TestClient(app)
    body = json.dumps(
        {
            "type": "event_callback",
            "team_id": "T1",
            "event": {
                "type": "message",
                "channel_type": "im",
                "text": "help",
                "user": "U1",
                "channel": "C1",
                "ts": "1700000000.0001",
            },
        }
    ).encode("utf-8")

    response = client.post(
        "/slack/events",
        content=body,
        headers=signed_headers(settings, body),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True, "posted": True}
    assert posted[0]["channel"] == "C1"
    assert posted[0]["thread_ts"] is None
    assert "/brain remember <memory>" in posted[0]["response"]["text"]


def test_slack_threaded_event_replies_in_thread(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path, brain_slack_bot_token="xoxb-test")
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    posted: list[dict[str, object]] = []

    async def fake_post_slack_message(settings, *, channel, response, thread_ts=None):
        posted.append({"channel": channel, "response": response, "thread_ts": thread_ts})
        return True

    monkeypatch.setattr(slack_agent_server, "post_slack_message", fake_post_slack_message)
    client = TestClient(app)
    body = json.dumps(
        {
            "type": "event_callback",
            "team_id": "T1",
            "event": {
                "type": "message",
                "channel_type": "im",
                "text": "help",
                "user": "U1",
                "channel": "C1",
                "ts": "1700000000.0002",
                "thread_ts": "1700000000.0001",
            },
        }
    ).encode("utf-8")

    response = client.post(
        "/slack/events",
        content=body,
        headers=signed_headers(settings, body),
    )

    assert response.status_code == 200
    assert posted[0]["thread_ts"] == "1700000000.0001"


def test_slack_bot_event_is_ignored_to_avoid_reply_loop(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path, brain_slack_bot_token="xoxb-test")
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    body = json.dumps(
        {
            "type": "event_callback",
            "team_id": "T1",
            "event": {
                "type": "message",
                "subtype": "bot_message",
                "bot_id": "B1",
                "text": "help",
                "channel": "C1",
            },
        }
    ).encode("utf-8")

    response = client.post(
        "/slack/events",
        content=body,
        headers=signed_headers(settings, body),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True, "ignored": True}


def test_slack_routes_are_separate_from_mcp(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path)
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)

    response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "tools/list"})

    assert response.status_code == 404


def test_slack_command_dry_run_returns_confirmation_payload(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path)
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    body = urlencode(
        {
            "command": "/brain",
            "text": "remember Sam likes Bill Evans.",
            "user_id": "U1",
            "channel_id": "C1",
            "team_id": "T1",
        }
    ).encode("utf-8")

    response = client.post(
        "/slack/commands",
        content=body,
        headers={**signed_headers(settings, body), "Content-Type": "application/x-www-form-urlencoded"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["payload"]["requires_confirmation"] is True
    assert payload["payload"]["dry_run"]["dry_run"] is True
    assert payload["blocks"][1]["elements"][0]["action_id"] == "brain_confirm_memory"


def test_slack_interaction_confirmation_commits_proposed_memory(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path)
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    command = command_body("remember Sam likes Bill Evans.", user_id="U1")
    command_response = client.post(
        "/slack/commands",
        content=command,
        headers={**signed_headers(settings, command), "Content-Type": "application/x-www-form-urlencoded"},
    )
    action_value = command_response.json()["blocks"][1]["elements"][0]["value"]
    interaction = urlencode(
        {
            "payload": json.dumps(
                {
                    "user": {"id": "U1"},
                    "channel": {"id": "C1"},
                    "team": {"id": "T1"},
                    "actions": [{"value": action_value}],
                }
            )
        }
    ).encode("utf-8")

    response = client.post(
        "/slack/interactions",
        content=interaction,
        headers={**signed_headers(settings, interaction), "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    assert response.json()["payload"]["receipt"]["dry_run"] is False


def test_slack_help_command_returns_text_only_payload(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path)
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)
    command = command_body("help", user_id="U1")
    response = client.post(
        "/slack/commands",
        content=command,
        headers={**signed_headers(settings, command), "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "blocks" not in payload
    assert "/brain remember <memory>" in payload["text"]
    assert "/brain recall <query>" in payload["text"]


def test_admin_debug_works_for_admin_and_rejects_non_admin(tmp_path, monkeypatch) -> None:
    settings = slack_settings(tmp_path, brain_slack_admin_user_ids="UADMIN")
    monkeypatch.setattr(slack_agent_server, "settings", settings)
    client = TestClient(app)

    non_admin_body = command_body("debug snapshot", user_id="U1")
    admin_body = command_body("debug snapshot", user_id="UADMIN")
    non_admin_response = client.post(
        "/slack/commands",
        content=non_admin_body,
        headers={**signed_headers(settings, non_admin_body), "Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_response = client.post(
        "/slack/commands",
        content=admin_body,
        headers={**signed_headers(settings, admin_body), "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert non_admin_response.json()["payload"]["status"] == "forbidden"
    assert "counts" in admin_response.json()["payload"]


def command_body(text: str, *, user_id: str) -> bytes:
    return urlencode(
        {
            "command": "/brain",
            "text": text,
            "user_id": user_id,
            "channel_id": "C1",
            "team_id": "T1",
        }
    ).encode("utf-8")


def signed_headers(settings: Settings, body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    return {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": slack_signature(
            settings.brain_slack_signing_secret,
            timestamp,
            body,
        ),
    }


def slack_signature(secret: str, timestamp: str, body: bytes) -> str:
    base = f"v0:{timestamp}:{body.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def slack_settings(tmp_path, **overrides) -> Settings:
    values = {
        "brain_database_url": f"sqlite:///{tmp_path / 'brain.db'}",
        "brain_slack_agent_enabled": True,
        "brain_slack_signing_secret": "test-secret",
        "brain_slack_allowed_team_ids": "T1",
        "brain_slack_allowed_channel_ids": "C1",
    }
    values.update(overrides)
    return Settings(**values)
