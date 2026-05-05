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
from memory_stack import name_resolution
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


def test_memory_tools_expose_node_set_and_search_options() -> None:
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tools = {tool["name"]: tool for tool in response.json()["result"]["tools"]}
    assert {"remember", "recall", "add", "cognify"} <= set(tools)
    assert {
        "ingest_source",
        "profile_entity",
        "list_open_loops",
        "get_memory",
        "resolve_conflict",
        "forget",
        "sync_cognee",
    } <= set(tools)

    remember_properties = tools["remember"]["inputSchema"]["properties"]
    assert "input" in remember_properties
    assert "node_set" in remember_properties

    add_properties = tools["add"]["inputSchema"]["properties"]
    assert "node_set" in add_properties

    recall_properties = tools["recall"]["inputSchema"]["properties"]
    assert "TEMPORAL" in recall_properties["search_type"]["enum"]
    assert "GRAPH_COMPLETION" in recall_properties["search_type"]["enum"]
    assert "node_name" in recall_properties
    assert recall_properties["node_name_filter_operator"]["enum"] == ["OR", "AND"]
    assert {"create_dataset", "list_node_sets", "create_node_set"} <= set(tools)


def test_high_level_brain_remember_and_recall_mcp_tools(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    try:
        client = TestClient(app)
        remember_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "remember",
                    "arguments": {
                        "input": "Sam from Goldman mentioned that he likes Bill Evans.",
                    },
                },
            },
        )
        recall_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "recall",
                    "arguments": {
                        "query": "Tell me everything about Sam from Goldman",
                        "mode": "profile",
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert remember_response.status_code == 200
    remember_payload = json.loads(remember_response.json()["result"]["content"][0]["text"])
    assert remember_payload["classification"] == "person_interaction"
    assert remember_payload["memory_cards"][0]["kind"] == "person_interaction"

    assert recall_response.status_code == 200
    recall_payload = json.loads(recall_response.json()["result"]["content"][0]["text"])
    assert "likes Bill Evans" in recall_payload["answer"]
    assert recall_payload["facts"][0]["kind"] == "person_interaction"


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


def test_remember_mcp_tool_passes_node_set(monkeypatch) -> None:
    captured = {}

    async def fake_resolve_dataset_name(value, *, settings):
        assert value == "daily-log"
        return value

    def fake_resolve_node_set_names(values, *, settings, for_write):
        assert values == ["decision", "2026-q2"]
        assert for_write is True
        return values

    async def fake_remember_text(text, *, dataset_name, temporal, node_set, settings):
        captured.update(
            {
                "text": text,
                "dataset_name": dataset_name,
                "temporal": temporal,
                "node_set": node_set,
                "settings": settings,
            }
        )

    monkeypatch.setattr(mcp_server, "resolve_dataset_name", fake_resolve_dataset_name)
    monkeypatch.setattr(mcp_server, "resolve_node_set_names", fake_resolve_node_set_names)
    monkeypatch.setattr(mcp_server, "remember_text", fake_remember_text)

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "remember",
                "arguments": {
                    "text": "decision text",
                    "dataset_name": "daily-log",
                    "temporal": False,
                    "node_set": ["decision", "2026-q2"],
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["content"][0]["text"] == "remembered"
    assert captured["text"] == "decision text"
    assert captured["dataset_name"] == "daily-log"
    assert captured["temporal"] is False
    assert captured["node_set"] == ["decision", "2026-q2"]
    assert captured["settings"] is mcp_server.settings


def test_add_and_cognify_mcp_tools(monkeypatch) -> None:
    captured = {}

    async def fake_resolve_dataset_name(value, *, settings):
        assert value == "melcombe-court"
        return value

    def fake_resolve_node_set_names(values, *, settings, for_write):
        assert values == "contract"
        assert for_write is True
        return ["contract"]

    async def fake_add_text(text, *, dataset_name, node_set, settings):
        captured["add"] = {
            "text": text,
            "dataset_name": dataset_name,
            "node_set": node_set,
            "settings": settings,
        }

    async def fake_cognify_dataset(dataset_name, *, temporal, settings):
        captured["cognify"] = {
            "dataset_name": dataset_name,
            "temporal": temporal,
            "settings": settings,
        }

    monkeypatch.setattr(mcp_server, "resolve_dataset_name", fake_resolve_dataset_name)
    monkeypatch.setattr(mcp_server, "resolve_node_set_names", fake_resolve_node_set_names)
    monkeypatch.setattr(mcp_server, "add_text", fake_add_text)
    monkeypatch.setattr(mcp_server, "cognify_dataset", fake_cognify_dataset)

    client = TestClient(app)
    add_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {
                    "text": "batch item",
                    "dataset_name": "melcombe-court",
                    "node_set": "contract",
                },
            },
        },
    )
    cognify_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "cognify",
                "arguments": {"dataset_name": "melcombe-court", "temporal": True},
            },
        },
    )

    assert add_response.status_code == 200
    assert add_response.json()["result"]["content"][0]["text"] == "added"
    assert captured["add"]["text"] == "batch item"
    assert captured["add"]["dataset_name"] == "melcombe-court"
    assert captured["add"]["node_set"] == ["contract"]
    assert captured["add"]["settings"] is mcp_server.settings

    assert cognify_response.status_code == 200
    assert cognify_response.json()["result"]["content"][0]["text"] == "cognified"
    assert captured["cognify"] == {
        "dataset_name": "melcombe-court",
        "temporal": True,
        "settings": mcp_server.settings,
    }


def test_recall_mcp_tool_passes_search_and_node_filters(monkeypatch) -> None:
    captured = {}

    async def fake_resolve_dataset_name(value, *, settings):
        assert value == "daily-log"
        return value

    def fake_resolve_node_set_names(values, *, settings, for_write):
        assert values == ["2026-q2", "decision"]
        assert for_write is False
        return values

    async def fake_recall_text(
        *,
        query,
        dataset,
        search_type,
        top_k,
        node_name,
        node_name_filter_operator,
        settings,
    ):
        captured.update(
            {
                "query": query,
                "dataset": dataset,
                "search_type": search_type,
                "top_k": top_k,
                "node_name": node_name,
                "node_name_filter_operator": node_name_filter_operator,
                "settings": settings,
            }
        )
        return ["matched"]

    monkeypatch.setattr(mcp_server, "resolve_dataset_name", fake_resolve_dataset_name)
    monkeypatch.setattr(mcp_server, "resolve_node_set_names", fake_resolve_node_set_names)
    monkeypatch.setattr(mcp_server, "recall_text", fake_recall_text)

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "recall",
                "arguments": {
                    "query": "What happened?",
                    "dataset": "daily-log",
                    "search_type": "GRAPH_COMPLETION",
                    "top_k": 5,
                    "node_name": ["2026-q2", "decision"],
                    "node_name_filter_operator": "AND",
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["content"][0]["text"] == "['matched']"
    assert captured == {
        "query": "What happened?",
        "dataset": "daily-log",
        "search_type": "GRAPH_COMPLETION",
        "top_k": 5,
        "node_name": ["2026-q2", "decision"],
        "node_name_filter_operator": "AND",
        "settings": mcp_server.settings,
    }


def test_fuzzy_dataset_match_requests_choice(monkeypatch) -> None:
    async def fake_list_datasources(*, settings):
        return [{"id": "1", "name": "my-health"}]

    async def fake_remember_text(*args, **kwargs):
        raise AssertionError("remember_text should not run until the user chooses")

    monkeypatch.setattr(name_resolution, "list_datasources", fake_list_datasources)
    monkeypatch.setattr(mcp_server, "remember_text", fake_remember_text)

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "remember",
                "arguments": {
                    "text": "blood pressure note",
                    "dataset_name": "my_health",
                },
            },
        },
    )

    assert response.status_code == 200
    error = response.json()["error"]["message"]
    assert "I couldn't find dataset 'my_health', but found 'my-health'." in error
    assert "a) my-health" in error
    assert "create it first using create_dataset" in error


def test_create_dataset_alias_creates_datasource(monkeypatch) -> None:
    async def fake_create_datasource(name, *, settings):
        return {"id": "dataset-1", "name": name}

    monkeypatch.setattr(mcp_server, "create_cognee_datasource", fake_create_datasource)

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_dataset",
                "arguments": {"name": "my_health"},
            },
        },
    )

    assert response.status_code == 200
    assert json.loads(response.json()["result"]["content"][0]["text"]) == {
        "datasource": {"id": "dataset-1", "name": "my_health"}
    }


def test_node_set_registry_tools(monkeypatch) -> None:
    captured = {}

    def fake_register_node_sets(settings, node_sets):
        captured["node_sets"] = node_sets

    def fake_load_node_set_registry(settings):
        return ["decision", "health"]

    monkeypatch.setattr(mcp_server, "register_node_sets", fake_register_node_sets)
    monkeypatch.setattr(mcp_server, "load_node_set_registry", fake_load_node_set_registry)

    client = TestClient(app)
    create_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_node_set",
                "arguments": {"name": "my-health"},
            },
        },
    )
    list_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "list_node_sets", "arguments": {}},
        },
    )

    assert create_response.status_code == 200
    assert json.loads(create_response.json()["result"]["content"][0]["text"]) == {
        "node_set": "my-health"
    }
    assert captured["node_sets"] == ["my-health"]
    assert json.loads(list_response.json()["result"]["content"][0]["text"]) == {
        "node_sets": ["decision", "health"]
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
