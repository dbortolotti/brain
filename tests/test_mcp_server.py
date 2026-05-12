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
    expected_tools = {
        "brain.remember",
        "brain.ingest_source",
        "brain.recall",
        "brain.profile_entity",
        "brain.list_open_loops",
        "brain.get_memory",
        "brain.get_source",
        "brain.resolve_conflict",
        "brain.forget",
        "brain.review_recent",
        "brain.undo_last",
        "brain.sync_cognee",
        "brain.rebuild_cognee",
        "brain.merge_entities",
        "brain.taste.describe_item",
        "brain.taste.remember",
        "brain.taste.query",
        "brain.taste.evaluate_options",
        "brain.taste.log_decision",
        "brain.taste.confirm",
        "brain.taste.cancel",
        "brain.taste.correct_proposal",
        "brain.taste.refresh_enrichment",
    }
    assert expected_tools == tool_names
    assert {
        "add",
        "cognify",
        "list_datasources",
        "create_datasource",
        "delete_datasource",
        "create_node_set",
    }.isdisjoint(tool_names)


def test_memory_tools_expose_node_set_and_search_options() -> None:
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tools = {tool["name"]: tool for tool in response.json()["result"]["tools"]}
    assert {
        "brain.remember",
        "brain.recall",
        "brain.profile_entity",
        "brain.list_open_loops",
        "brain.get_memory",
        "brain.get_source",
        "brain.resolve_conflict",
        "brain.forget",
        "brain.review_recent",
        "brain.undo_last",
        "brain.sync_cognee",
        "brain.rebuild_cognee",
        "brain.merge_entities",
        "brain.taste.remember",
        "brain.taste.evaluate_options",
    } <= set(tools)

    remember_properties = tools["brain.remember"]["inputSchema"]["properties"]
    assert "input" in remember_properties
    assert "dataset_name" not in remember_properties
    assert "node_set" not in remember_properties

    recall_properties = tools["brain.recall"]["inputSchema"]["properties"]
    assert recall_properties["mode"]["enum"] == [
        "auto",
        "evidence",
        "profile",
        "open_loops",
        "sources",
        "memories",
        "debug",
    ]
    assert "dataset" not in recall_properties
    assert "search_type" not in recall_properties
    assert "node_name" not in recall_properties

    taste_properties = tools["brain.taste.remember"]["inputSchema"]["properties"]
    assert {"type", "canonical_name", "description"} <= set(taste_properties)

    forget_properties = tools["brain.forget"]["inputSchema"]["properties"]
    assert forget_properties["object_type"]["enum"] == [
        "memory",
        "source",
        "entity",
        "relationship",
        "open_loop",
    ]
    assert "confirm" in forget_properties


def test_mcp_resources_are_listed_and_schema_can_be_read() -> None:
    client = TestClient(app)
    list_response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "resources/list"},
    )
    templates_response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "resources/templates/list"},
    )
    read_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {"uri": "brain://schema/memory-card"},
        },
    )

    assert list_response.status_code == 200
    assert {
        resource["uri"] for resource in list_response.json()["result"]["resources"]
    } == {
        "brain://schema/memory-card",
        "brain://schema/source",
        "brain://schema/entity",
    }
    assert templates_response.status_code == 200
    template_uris = {
        template["uriTemplate"]
        for template in templates_response.json()["result"]["resourceTemplates"]
    }
    assert "brain://memory/{memory_id}" in template_uris
    assert "brain://source/{source_id}" in template_uris
    assert read_response.status_code == 200
    content = read_response.json()["result"]["contents"][0]
    assert content["uri"] == "brain://schema/memory-card"
    assert json.loads(content["text"])["schema"] == "memory-card"


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
                    "name": "brain.remember",
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
                    "name": "brain.recall",
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
    remember_result = remember_response.json()["result"]
    remember_payload = remember_result["structuredContent"]
    assert "Stored 1 memories" in remember_result["content"][0]["text"]
    assert remember_payload["classification"] == "person_interaction"
    assert remember_payload["memory_cards"][0]["kind"] == "person_interaction"

    assert recall_response.status_code == 200
    recall_result = recall_response.json()["result"]
    recall_payload = recall_result["structuredContent"]
    assert json.loads(recall_result["content"][1]["text"]) == recall_payload
    assert "likes Bill Evans" in recall_payload["answer"]
    assert recall_payload["facts"][0]["kind"] == "person_interaction"


def test_brain_ingest_source_and_get_source_mcp_tools(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    try:
        client = TestClient(app)
        ingest_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain.ingest_source",
                    "arguments": {
                        "source": "# Source\nKnowledge graphs matter for Brain.",
                        "source_kind": "markdown",
                        "title": "Knowledge graph note",
                    },
                },
            },
        )
        ingest_payload = ingest_response.json()["result"]["structuredContent"]
        source_id = ingest_payload["source_id"]
        source_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain.get_source",
                    "arguments": {"source_id": source_id, "include_text": True},
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert ingest_response.status_code == 200
    assert ingest_payload["memory_cards_created"]
    assert source_response.status_code == 200
    source_payload = source_response.json()["result"]["structuredContent"]
    assert source_payload["source"]["id"] == source_id
    assert source_payload["source"]["kind"] == "markdown"
    assert "Knowledge graphs matter" in source_payload["text"]


def test_brain_ingest_source_rest_accepts_source_schema(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    try:
        client = TestClient(app)
        response = client.post(
            "/memory/ingest_source",
            json={
                "source": "# Source\nKnowledge graphs matter for Brain.",
                "source_kind": "markdown",
                "title": "Knowledge graph note",
                "metadata": {"origin": "test"},
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "markdown"
    assert payload["source"]["created"] is True
    assert payload["memory_cards"][0]["kind"] == "source_summary"


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


def test_low_level_legacy_mcp_tools_are_rejected() -> None:
    client = TestClient(app)
    stale_names = [
        "remember",
        "recall",
        "add",
        "cognify",
        "list_datasources",
        "create_dataset",
        "create_node_set",
        "list_node_sets",
        "delete_datasource",
        "sync_cognee",
    ]
    for idx, name in enumerate(stale_names, start=1):
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": idx,
                "method": "tools/call",
                "params": {"name": name, "arguments": {}},
            },
        )
        assert response.status_code == 200
        assert response.json()["error"]["message"] == f"Unknown tool: {name}"


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
