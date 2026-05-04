from __future__ import annotations

import base64
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from memory_stack.config import Settings
from memory_stack.mcp_server import app
from memory_stack import mcp_server
from memory_stack.oauth import BrainOAuthProvider
from memory_stack.request_logging import RequestResponseLogMiddleware, redact_text, redact_url


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["service"] == "Brain"


def test_mcp_initialize() -> None:
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "brain"


def test_datasource_tools_are_listed() -> None:
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tool_names = {tool["name"] for tool in response.json()["result"]["tools"]}
    assert {"list_datasources", "create_datasource", "delete_datasource"} <= tool_names


def test_list_datasources_http_endpoint(monkeypatch) -> None:
    async def fake_list_datasources(*, settings):
        return [{"id": "datasource-1", "name": "property_trial"}]

    monkeypatch.setattr(mcp_server, "list_cognee_datasources", fake_list_datasources)

    client = TestClient(app)
    response = client.get("/list_datasources")

    assert response.status_code == 200
    assert response.json() == {
        "datasources": [{"id": "datasource-1", "name": "property_trial"}]
    }


def test_create_datasource_http_endpoint(monkeypatch) -> None:
    async def fake_create_datasource(name, *, settings):
        return {"id": "datasource-2", "name": name}

    monkeypatch.setattr(mcp_server, "create_cognee_datasource", fake_create_datasource)

    client = TestClient(app)
    response = client.post("/create_datasource", json={"name": "new_source"})

    assert response.status_code == 201
    assert response.json() == {"datasource": {"id": "datasource-2", "name": "new_source"}}


def test_delete_datasource_http_endpoint(monkeypatch) -> None:
    async def fake_delete_datasource(datasource, *, settings):
        return {"id": datasource, "name": "old_source", "status": "deleted"}

    monkeypatch.setattr(mcp_server, "delete_cognee_datasource", fake_delete_datasource)

    client = TestClient(app)
    response = client.delete("/delete_datasource/datasource-3")

    assert response.status_code == 200
    assert response.json() == {
        "datasource": {"id": "datasource-3", "name": "old_source", "status": "deleted"}
    }


def test_list_datasources_mcp_tool(monkeypatch) -> None:
    async def fake_list_datasources(*, settings):
        return [{"id": "datasource-1", "name": "property_trial"}]

    monkeypatch.setattr(mcp_server, "list_cognee_datasources", fake_list_datasources)

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "list_datasources", "arguments": {}},
        },
    )

    assert response.status_code == 200
    content = response.json()["result"]["content"][0]
    assert json.loads(content["text"]) == {
        "datasources": [{"id": "datasource-1", "name": "property_trial"}]
    }


def test_auth_enabled_mcp_fails_closed(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.get("/mcp")

    assert response.status_code == 401
    assert "Brain" in response.headers["www-authenticate"]
    assert "oauth-protected-resource/mcp" in response.headers["www-authenticate"]


def test_auth_enabled_datasources_fail_closed(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.get("/list_datasources")

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_required"
    assert "Brain" in response.headers["www-authenticate"]


def test_oauth_authorization_code_flow(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app, follow_redirects=False)
        register_response = client.post(
            "/register",
            json={
                "client_name": "test-client",
                "redirect_uris": ["http://127.0.0.1/callback"],
                "token_endpoint_auth_method": "none",
                "scope": "brain.memory.read brain.memory.write",
            },
        )
        assert register_response.status_code == 201
        client_id = register_response.json()["client_id"]

        verifier = "test-code-verifier"
        challenge = pkce_challenge(verifier)
        authorize_response = client.get(
            "/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": "http://127.0.0.1/callback",
                "scope": "brain.memory.read brain.memory.write",
                "state": "abc",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        assert authorize_response.status_code == 200
        request_id_match = re.search(
            r'name="request_id" value="([^"]+)"',
            authorize_response.text,
        )
        assert request_id_match
        request_id = request_id_match.group(1)

        password = (tmp_path / "brain-auth-password").read_text(encoding="utf-8").strip()
        complete_response = client.post(
            "/authorize",
            data={"request_id": request_id, "password": password},
        )
        assert complete_response.status_code == 302
        callback_query = parse_qs(urlsplit(complete_response.headers["location"]).query)
        assert callback_query["state"] == ["abc"]
        code = callback_query["code"][0]

        token_response = client.post(
            "/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "code": code,
                "redirect_uri": "http://127.0.0.1/callback",
                "code_verifier": verifier,
            },
        )
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]

        mcp_response = client.get("/mcp", headers={"Authorization": f"Bearer {access_token}"})
        assert mcp_response.status_code == 200
        assert mcp_response.json()["service"] == "Brain"


def test_request_response_logger_redacts_secrets(tmp_path) -> None:
    log_path = tmp_path / "requests.jsonl"
    settings = Settings(
        brain_request_log_path=str(log_path),
        brain_request_log_max_body_bytes=0,
    )
    test_app = FastAPI()
    test_app.add_middleware(RequestResponseLogMiddleware, settings=settings)

    @test_app.post("/echo")
    async def echo(request: Request) -> JSONResponse:
        return JSONResponse(await request.json())

    client = TestClient(test_app)
    response = client.post(
        "/echo?code=abc123",
        headers={"Authorization": "Bearer secret-token"},
        json={
            "text": "keep this refinement text",
            "password": "secret-password",
            "access_token": "secret-access-token",
        },
    )

    assert response.status_code == 200
    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["request"]["query"]["code"] == "[REDACTED]"
    assert record["request"]["headers"]["authorization"] == "[REDACTED]"
    assert record["request"]["body"]["text"] == "keep this refinement text"
    assert record["request"]["body"]["password"] == "[REDACTED]"
    assert record["response"]["body"]["access_token"] == "[REDACTED]"


def test_request_logger_redacts_auth_urls_and_html() -> None:
    redacted_url = redact_url("http://127.0.0.1/callback?code=abc&state=keep")
    assert "code=%5BREDACTED%5D" in redacted_url
    assert "abc" not in redacted_url
    assert "state=keep" in redacted_url

    redacted_html = redact_text('<input name="request_id" value="secret-request-id">')
    assert "secret-request-id" not in redacted_html
    assert "[REDACTED]" in redacted_html


class oauth_settings:
    def __init__(self, tmp_path) -> None:
        self.tmp_path = tmp_path
        self.previous_settings = mcp_server.settings
        self.previous_provider = mcp_server.oauth_provider

    def __enter__(self) -> None:
        settings = Settings(
            brain_auth_enabled=True,
            brain_auth_password_file=str(self.tmp_path / "brain-auth-password"),
            brain_auth_state_path=str(self.tmp_path / "brain-oauth.json"),
            brain_public_base_url="https://brain.dceb.net",
            brain_public_mcp_path="/mcp",
        )
        mcp_server.settings = settings
        mcp_server.oauth_provider = BrainOAuthProvider(settings)

    def __exit__(self, exc_type, exc, tb) -> None:
        mcp_server.settings = self.previous_settings
        mcp_server.oauth_provider = self.previous_provider


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
