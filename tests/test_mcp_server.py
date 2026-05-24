from __future__ import annotations

import base64
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import pytest

from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.mcp_server import app
from memory_stack import mcp_server
from memory_stack import brain_service
from memory_stack.oauth import BrainOAuthProvider
from memory_stack.request_logging import RequestResponseLogMiddleware, redact_text, redact_url


TEST_SERVICE_TOKEN = "test-service-token"


@pytest.fixture(autouse=True)
def authenticated_service_client(monkeypatch):
    previous_settings = mcp_server.settings
    previous_request = TestClient.request
    if mcp_server.oauth_provider is None and not mcp_server.settings.brain_auth_token:
        mcp_server.settings = mcp_server.settings.model_copy(
            update={"brain_auth_token": TEST_SERVICE_TOKEN}
        )

    def request_with_service_token(self, method, url, *args, **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        if mcp_server.oauth_provider is None:
            if not mcp_server.settings.brain_auth_token:
                mcp_server.settings = mcp_server.settings.model_copy(
                    update={"brain_auth_token": TEST_SERVICE_TOKEN}
                )
            if not any(key.lower() == "authorization" for key in headers):
                headers["Authorization"] = f"Bearer {mcp_server.settings.brain_auth_token}"
        return previous_request(self, method, url, *args, headers=headers, **kwargs)

    monkeypatch.setattr(TestClient, "request", request_with_service_token)
    try:
        yield
    finally:
        mcp_server.settings = previous_settings


def test_remember_summary_names_taste_proposal_without_claiming_storage() -> None:
    summary = mcp_server.remember_summary(
        {
            "classification": "taste_proposal",
            "dry_run": True,
            "entities": [],
            "conflicts": [],
            "taste": {
                "proposal_id": "tprop_example",
                "warnings": ["Taste/palate keyword present but item type is not certain."],
            },
        }
    )

    assert "pending Brain Palate proposal tprop_example" in summary
    assert "no durable Brain memories were stored yet" in summary
    assert "Stored 0 memories" not in summary


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["service"] == "Brain"
    assert response.json()["release_version"]
    assert response.json()["release_sha"]


def test_icon_routes() -> None:
    client = TestClient(app)

    icon_response = client.get("/icon.png")
    assert icon_response.status_code == 200
    assert icon_response.headers["content-type"] == "image/png"
    assert icon_response.content.startswith(b"\x89PNG")

    favicon_response = client.get("/favicon.ico")
    assert favicon_response.status_code == 200
    assert favicon_response.headers["content-type"] == "image/x-icon"
    assert favicon_response.content.startswith(b"\x00\x00\x01\x00")


def test_public_http_redirects_to_https_for_cookie_auth(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app, base_url="http://brain.dceb.net", follow_redirects=False)
        response = client.get("/healthz")
        forwarded_https_response = client.get("/healthz", headers={"X-Forwarded-Proto": "https"})
        local_response = client.get("http://127.0.0.1:18100/healthz")

    assert response.status_code == 307
    assert response.headers["location"] == "https://brain.dceb.net/healthz"
    assert forwarded_https_response.status_code == 200
    assert local_response.status_code == 200


def test_mcp_initialize() -> None:
    client = TestClient(app)
    response = client.post("/admin/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert response.status_code == 200
    assert response.json()["result"]["protocolVersion"] == "2024-11-05"
    server_info = response.json()["result"]["serverInfo"]
    assert server_info["name"] == "brain"
    assert server_info["icons"] == [
        {
            "src": f"{mcp_server.settings.brain_public_base_url.rstrip('/')}/icon.png",
            "mimeType": "image/png",
            "sizes": ["512x512"],
        }
    ]
    assert response.json()["result"]["capabilities"]["prompts"] == {}


def test_mcp_initialize_negotiates_requested_protocol_version() -> None:
    client = TestClient(app)
    response = client.post(
        "/admin/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-11-25"},
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["protocolVersion"] == "2025-11-25"


def test_datasource_tools_are_listed() -> None:
    client = TestClient(app)
    response = client.post("/admin/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tool_names = {tool["name"] for tool in response.json()["result"]["tools"]}
    expected_tools = {
        "brain_session",
        "brain_profile_context_remember",
        "brain_profile_context_list",
        "brain_profile_context_forget",
        "brain_bias_context_remember",
        "brain_bias_context_list",
        "brain_bias_context_forget",
        "brain_profile_context_sync",
        "brain_remember",
        "brain_ingest_source",
        "brain_recall",
        "brain_profile_entity",
        "brain_forget",
        "brain_review_recent",
        "brain_undo_last",
        "cognee_improve",
        "brain_palate_describe_item",
        "brain_palate_remember",
        "brain_palate_query",
        "brain_palate_evaluate_options",
        "brain_palate_log_decision",
        "brain_palate_confirm",
        "brain_palate_cancel",
        "brain_palate_correct_proposal",
        "brain_palate_refresh_enrichment",
    }
    assert expected_tools == tool_names
    assert all("." not in tool_name for tool_name in tool_names)
    expected_icons = [
        {
            "src": f"{mcp_server.settings.brain_public_base_url.rstrip('/')}/icon.png",
            "mimeType": "image/png",
            "sizes": ["512x512"],
        }
    ]
    for tool in response.json()["result"]["tools"]:
        assert "outputSchema" in tool
        assert tool["outputSchema"]["type"] == "object"
        assert tool["icons"] == expected_icons
        assert "structuredContent" not in tool["outputSchema"]["properties"]
    assert {
        "add",
        "cognify",
        "list_datasources",
        "create_datasource",
        "delete_datasource",
        "create_node_set",
        "brain.remember",
        "brain.recall",
        "brain.palate.remember",
        "brain.palate.query",
        "brain.taste.remember",
        "brain.taste.query",
    }.isdisjoint(tool_names)


def test_bias_context_tools_update_session(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        remember_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_bias_context_remember",
                    "arguments": {
                        "statement": "Daniele prefers concise answers.",
                        "scope": "response_style",
                    },
                },
            },
        )
        session_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
        context_id = remember_response.json()["result"]["structuredContent"]["id"]
        forget_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "brain_bias_context_forget",
                    "arguments": {"context_id": context_id},
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert remember_response.status_code == 200
    remembered = remember_response.json()["result"]["structuredContent"]
    assert remembered["created"] is True
    assert remembered["kind"] == "bias"
    assert remembered["id"].startswith("bias_context_")
    session_payload = session_response.json()["result"]["structuredContent"]
    assert session_payload["bias_context"][0]["id"] == context_id
    assert session_payload["bias_context"][0]["statement"] == "Daniele prefers concise answers."
    assert forget_response.json()["result"]["structuredContent"]["status"] == "deleted"
    store = BrainStore(
        Settings(
            brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
            brain_profile_context_path=str(tmp_path / "profile_context.json"),
        )
    )
    assert store.list_context_records(kind="bias") == []
    assert store.list_context_records(kind="bias", include_deleted=True)[0]["status"] == "deleted"


def test_memory_tools_expose_node_set_and_search_options() -> None:
    client = TestClient(app)
    response = client.post("/admin/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tools = {tool["name"]: tool for tool in response.json()["result"]["tools"]}
    assert {
        "brain_session",
        "brain_profile_context_remember",
        "brain_profile_context_list",
        "brain_profile_context_forget",
        "brain_profile_context_sync",
        "brain_bias_context_remember",
        "brain_bias_context_list",
        "brain_bias_context_forget",
        "brain_remember",
        "brain_recall",
        "brain_profile_entity",
        "brain_forget",
        "brain_review_recent",
        "brain_undo_last",
        "cognee_improve",
        "brain_palate_remember",
        "brain_palate_evaluate_options",
    } <= set(tools)

    assert tools["brain_session"]["inputSchema"]["properties"] == {}
    assert tools["brain_session"]["outputSchema"]["required"] == ["user_id"]
    session_output = tools["brain_session"]["outputSchema"]["properties"]
    assert "profile_context" in session_output
    assert "bias_context" in session_output
    profile_context_properties = tools["brain_profile_context_remember"]["inputSchema"]["properties"]
    assert {"statement", "scope", "source"} <= set(profile_context_properties)
    bias_context_properties = tools["brain_bias_context_remember"]["inputSchema"]["properties"]
    assert {"statement", "scope", "source"} <= set(bias_context_properties)

    remember_properties = tools["brain_remember"]["inputSchema"]["properties"]
    assert "input" in remember_properties
    assert "source_policy" not in remember_properties
    assert "dataset_name" not in remember_properties
    assert "node_set" not in remember_properties
    ingest_properties = tools["brain_ingest_source"]["inputSchema"]["properties"]
    assert "extract_memories" not in ingest_properties

    recall_properties = tools["brain_recall"]["inputSchema"]["properties"]
    assert recall_properties["mode"]["enum"] == [
        "auto",
        "evidence",
        "profile",
        "memories",
        "debug",
    ]
    assert "dataset" not in recall_properties
    assert "search_type" not in recall_properties
    assert "node_name" not in recall_properties
    assert tools["brain_recall"]["outputSchema"]["required"] == ["answer"]
    assert {"answer", "facts", "evidence"} <= set(
        tools["brain_recall"]["outputSchema"]["properties"]
    )

    improve_properties = tools["cognee_improve"]["inputSchema"]["properties"]
    assert improve_properties["dataset"]["enum"] == ["memory", "data", "palate"]

    taste_properties = tools["brain_palate_remember"]["inputSchema"]["properties"]
    assert {"type", "canonical_name", "description"} <= set(taste_properties)
    assert "taste_records" in tools["brain_palate_remember"]["outputSchema"]["properties"]

    forget_properties = tools["brain_forget"]["inputSchema"]["properties"]
    assert forget_properties["object_type"]["enum"] == [
        "cognee_remember",
        "entity",
    ]
    assert "confirm" in forget_properties


def test_palate_describe_tool_description_covers_read_only_restaurant_requests() -> None:
    client = TestClient(app)
    response = client.post("/admin/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tools = {tool["name"]: tool for tool in response.json()["result"]["tools"]}
    describe = tools["brain_palate_describe_item"]
    remember = tools["brain_remember"]
    query = tools["brain_palate_query"]
    evaluate_options = tools["brain_palate_evaluate_options"]

    description = describe["description"].casefold()
    assert "use palate to describe junsei restaurant in london" in description
    assert "read-only" in description
    assert "without saving" in description or "must not store" in description
    assert "restaurant" in describe["inputSchema"]["properties"]["entity_type"]["description"]
    assert "do not use this for read-only palate describe/enrich requests" in remember[
        "description"
    ].casefold()
    assert "do not use this to describe" in query["description"].casefold()
    assert "single named unsaved item such as junsei" in query["description"].casefold()
    assert "call brain_palate_describe_item" in query["description"]
    assert "do not use this to describe" in evaluate_options["description"].casefold()


def test_brain_session_returns_configured_identity(tmp_path) -> None:
    previous_settings = mcp_server.settings
    active_settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_owner_full_name="Daniele Bortolotti",
        brain_owner_name="Daniele",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    mcp_server.settings = active_settings
    try:
        client = TestClient(app, base_url="https://testserver")
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["user_id"] == "default"
    assert "session_id" not in payload
    assert "cognee_session_id" not in payload
    assert "cognee_dataset" not in payload
    assert "session_map_id" not in payload
    assert payload["profile_name"] == "Daniele"
    assert payload["profile_full_name"] == "Daniele Bortolotti"
    assert payload["profile_context"] == []
    assert payload["bias_context"] == []
    assert payload["bias_context_remember_tool"] == "brain_bias_context_remember"
    assert payload["bias_context_list_tool"] == "brain_bias_context_list"
    assert payload["bias_context_forget_tool"] == "brain_bias_context_forget"
    assert payload["bias_prompt"] == "brain_bias_protocol"


def test_profile_context_tools_update_brain_session(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        remember_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele works in a bank as a quant.",
                        "scope": "answer_tailoring",
                    },
                },
            },
        )
        session_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
        list_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "brain_profile_context_list", "arguments": {}},
            },
        )
        context_id = remember_response.json()["result"]["structuredContent"]["id"]
        forget_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_forget",
                    "arguments": {"context_id": context_id},
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert remember_response.status_code == 200
    remembered = remember_response.json()["result"]["structuredContent"]
    assert remembered["created"] is True
    assert remembered["statement"] == "Daniele works in a bank as a quant."
    session_payload = session_response.json()["result"]["structuredContent"]
    assert session_payload["profile_context"][0]["statement"] == "Daniele works in a bank as a quant."
    assert session_payload["profile_context"][0]["id"] == context_id
    assert session_payload["profile_context_records"][0]["sync_status"] == "control_store"
    assert "memory_id" not in session_payload["profile_context_records"][0]
    assert "owner_entity_id" not in session_payload["profile_context_records"][0]
    listed = list_response.json()["result"]["structuredContent"]["profile_context"]
    assert listed[0]["id"] == context_id
    assert forget_response.json()["result"]["structuredContent"]["status"] == "deleted"
    store = BrainStore(
        Settings(
            brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
            brain_profile_context_path=str(tmp_path / "profile_context.json"),
        )
    )
    assert len(store.list_context_records(kind="profile")) == 0
    assert store.list_context_records(kind="profile", include_deleted=True)[0]["status"] == "deleted"


def test_brain_session_migrates_legacy_string_profile_context(tmp_path) -> None:
    profile_context_path = tmp_path / "profile_context.json"
    profile_context_path.write_text(
        json.dumps(
            [
                "Daniele's GitHub profile https://github.com/dbortolotti is the starting point for all his repositories."
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(profile_context_path),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["profile_context"][0]["statement"].startswith("Daniele's GitHub profile")
    assert payload["profile_context"][0]["scope"] == "answer_tailoring"
    assert payload["profile_context"][0]["id"].startswith("profile_context_")
    stored = json.loads(profile_context_path.read_text(encoding="utf-8"))
    assert isinstance(stored[0], dict)


def test_profile_context_sync_projects_owner_entity_without_first_name_alias(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_owner_full_name="Daniele Bortolotti",
        brain_owner_name="Daniele",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app)
        remember_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele has a PhD in theoretical physics.",
                    },
                },
            },
        )
        sync_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_profile_context_sync", "arguments": {}},
            },
        )
        profile_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_entity",
                    "arguments": {"name": "Daniele"},
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert remember_response.status_code == 200
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()["result"]["structuredContent"]
    assert sync_payload["synced_count"] == 1
    assert sync_payload["profile_context_count"] == 1
    assert sync_payload["profile_context"][0]["sync_status"] == "control_store"
    assert "memory_id" not in sync_payload["profile_context"][0]
    assert "Daniele has a PhD in theoretical physics." in profile_response.json()["result"][
        "structuredContent"
    ]["answer"]
    store = BrainStore(
        Settings(
            brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
            brain_owner_full_name="Daniele Bortolotti",
            brain_owner_name="Daniele",
            brain_profile_context_path=str(tmp_path / "profile_context.json"),
        )
    )
    assert store.list_context_records(kind="profile")[0]["statement"] == "Daniele has a PhD in theoretical physics."


def test_cognee_improve_mcp_tool_calls_configured_dataset(tmp_path, monkeypatch) -> None:
    calls = []

    async def fake_improve_cognee(**kwargs):
        calls.append(kwargs)
        return {"run_id": "improve-1"}

    monkeypatch.setattr(mcp_server, "improve_cognee", fake_improve_cognee)
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_cognee_palate_dataset="palate_live",
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "cognee_improve",
                    "arguments": {
                        "dataset": "palate",
                        "node_name": ["Wine"],
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["resolved_dataset"] == "palate_live"
    assert calls[0]["dataset"] == "palate_live"
    assert calls[0]["node_name"] == ["Wine"]


def test_mcp_resources_are_listed_and_schema_can_be_read() -> None:
    client = TestClient(app)
    list_response = client.post(
        "/admin/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "resources/list"},
    )
    templates_response = client.post(
        "/admin/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "resources/templates/list"},
    )
    read_response = client.post(
        "/admin/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {"uri": "brain://schema/entity"},
        },
    )
    assert list_response.status_code == 200
    assert {
        resource["uri"] for resource in list_response.json()["result"]["resources"]
    } == {"brain://schema/entity"}
    assert templates_response.status_code == 200
    template_uris = {
        template["uriTemplate"]
        for template in templates_response.json()["result"]["resourceTemplates"]
    }
    assert template_uris == {"brain://entity/{entity_id}", "brain://schema/{schema_name}"}
    assert read_response.status_code == 200
    content = read_response.json()["result"]["contents"][0]
    assert content["uri"] == "brain://schema/entity"
    assert json.loads(content["text"])["schema"] == "entity"


def test_bias_protocol_prompt_can_be_inserted_with_profile_name() -> None:
    client = TestClient(app)
    response = client.post(
        "/admin/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {
                "name": "brain_bias_protocol",
                "arguments": {"profile_name": "Daniele"},
            },
        },
    )

    assert response.status_code == 200
    text = response.json()["result"]["messages"][0]["content"]["text"]
    assert "Bias and Preference Protocol" in text
    assert "brain_recall" in text
    assert "brain_remember" in text
    assert "Daniele prefers short answers" in text
    assert "Don't narrate memory calls" in text


def test_bias_protocol_prompt_defaults_to_owner_name() -> None:
    client = TestClient(app)
    response = client.post(
        "/admin/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {"name": "brain_bias_protocol"},
        },
    )

    assert response.status_code == 200
    text = response.json()["result"]["messages"][0]["content"]["text"]
    assert f"for {mcp_server.settings.brain_owner_name}" in text


def test_high_level_brain_remember_mcp_tool_returns_cognee_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    calls = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))
    try:
        client = TestClient(app)
        remember_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_remember",
                    "arguments": {
                        "input": "Sam from Goldman mentioned that he likes Bill Evans.",
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert remember_response.status_code == 200
    remember_result = remember_response.json()["result"]
    remember_payload = remember_result["structuredContent"]
    assert "Stored data once in Cognee" in remember_result["content"][0]["text"]
    assert remember_payload["classification"] == "direct_memory"
    assert remember_payload["cognee_sync_status"] == "synced"
    assert calls[0]["dataset_name"] == "memory"
    assert calls[0]["text"] == "Sam from Goldman mentioned that he likes Bill Evans."


def test_brain_ingest_source_mcp_tool_returns_cognee_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    calls = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))
    try:
        client = TestClient(app)
        ingest_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_ingest_source",
                    "arguments": {
                        "source": "# Source\nKnowledge graphs matter for Brain.",
                        "source_kind": "markdown",
                        "title": "Knowledge graph note",
                    },
                },
            },
        )
        ingest_payload = ingest_response.json()["result"]["structuredContent"]
    finally:
        mcp_server.settings = previous_settings

    assert ingest_response.status_code == 200
    assert ingest_payload["status"] == "processed"
    assert ingest_payload["cognee_sync_status"] == "synced"
    assert [call["dataset_name"] for call in calls] == ["memory"]
    assert calls[0]["text"] == "# Source\nKnowledge graphs matter for Brain."
    assert "brain_source" not in calls[0]["node_set"]
    assert "brain_memory" not in calls[0]["node_set"]


def test_brain_ingest_source_mcp_rejects_input_payload(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    try:
        client = TestClient(app)
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_ingest_source",
                    "arguments": {
                        "input": "# Source\nKnowledge graphs matter for Brain.",
                        "input_type": "markdown",
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    error = response.json()["error"]
    assert error["code"] == -32000
    assert "source" in error["message"]


def test_brain_ingest_source_mcp_background_returns_queued(tmp_path, monkeypatch) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    submitted = []

    def fake_submit_background_ingest(request, active_settings, *, llm_client=None):
        del llm_client
        assert active_settings is mcp_server.settings
        submitted.append(request)
        return None

    monkeypatch.setattr(
        brain_service,
        "_submit_background_ingest",
        fake_submit_background_ingest,
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_ingest_source",
                    "arguments": {
                        "source": "# Source\nKnowledge graphs matter for Brain.",
                        "source_kind": "markdown",
                        "run_in_background": True,
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["status"] == "queued"
    assert payload["cognee_sync_status"] == "queued"
    assert submitted
    assert submitted[0].run_in_background is False


def test_brain_ingest_source_mcp_auto_backgrounds_large_source(tmp_path, monkeypatch) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_ingest_background_auto_chars=10,
    )
    submitted = []

    def fake_submit_background_ingest(request, active_settings, *, llm_client=None):
        del llm_client
        assert active_settings is mcp_server.settings
        submitted.append(request)
        return None

    monkeypatch.setattr(
        brain_service,
        "_submit_background_ingest",
        fake_submit_background_ingest,
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_ingest_source",
                    "arguments": {
                        "source": "# Source\nKnowledge graphs matter for Brain.",
                        "source_kind": "markdown",
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["status"] == "queued"
    assert payload["cognee_sync_status"] == "queued"
    assert submitted
    assert submitted[0].run_in_background is False


def test_brain_ingest_source_rest_accepts_source_schema(tmp_path, monkeypatch) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
    calls = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))
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
    assert payload["cognee_sync_status"] == "synced"
    assert [call["dataset_name"] for call in calls] == ["memory"]
    assert calls[0]["text"] == "# Source\nKnowledge graphs matter for Brain."


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
        "brain.remember",
        "brain.recall",
        "brain.get_source",
        "brain.palate.describe_item",
        "brain.palate.remember",
        "brain.taste.describe_item",
        "brain.taste.remember",
    ]
    for idx, name in enumerate(stale_names, start=1):
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": idx,
                "method": "tools/call",
                "params": {"name": name, "arguments": {}},
            },
        )
        assert response.status_code == 200
        assert response.json()["error"]["message"] == f"Unknown tool: {name}"


def test_mcp_fails_closed_without_auth(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.get("/admin/mcp")

    assert response.status_code == 401
    assert "Brain" in response.headers["www-authenticate"]
    assert "oauth-protected-resource/admin/mcp" in response.headers["www-authenticate"]


def test_app_mcp_fails_closed_without_auth_with_app_resource(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.get("/mcp")

    assert response.status_code == 401
    assert "Brain" in response.headers["www-authenticate"]
    assert "oauth-protected-resource/mcp" in response.headers["www-authenticate"]


def test_app_mcp_post_without_json_fails_closed_without_auth(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.post("/mcp", content=b"")

    assert response.status_code == 401
    assert "Brain" in response.headers["www-authenticate"]
    assert "oauth-protected-resource/mcp" in response.headers["www-authenticate"]


def test_datasources_fail_closed_without_auth(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.get("/list_datasources")

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_required"
    assert "Brain" in response.headers["www-authenticate"]


def test_openid_configuration_aliases_oauth_metadata(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        oauth_response = client.get("/.well-known/oauth-authorization-server")
        openid_response = client.get("/.well-known/openid-configuration")

    assert openid_response.status_code == 200
    assert openid_response.json() == oauth_response.json()


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
        assert '<label for="user_id">Username</label>' in authorize_response.text
        assert 'placeholder="username"' in authorize_response.text
        assert 'autocomplete="off"' in authorize_response.text
        assert "Daniele Bortolotti" not in authorize_response.text
        assert "autocomplete=\"username\"" not in authorize_response.text
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

        mcp_response = client.get("/admin/mcp", headers={"Authorization": f"Bearer {access_token}"})
        assert mcp_response.status_code == 200
        assert mcp_response.json()["service"] == "Brain"


def test_oauth_user_id_scopes_mcp_and_http_memory_data(tmp_path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps(
            [
                {"id": "user_a", "password": "pass-a", "display_name": "User A"},
                {"id": "user_b", "password": "pass-b", "display_name": "User B"},
            ]
        ),
        encoding="utf-8",
    )
    db_url = f"sqlite:///{tmp_path / 'brain.db'}"
    with oauth_settings(
        tmp_path,
        brain_auth_users_file=str(users_file),
        brain_database_url=db_url,
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    ):
        client = TestClient(app, follow_redirects=False)
        access_token = issue_test_oauth_token(
            client,
            tmp_path,
            scope="brain.memory.read brain.memory.write",
            user_id="user_b",
            password="pass-b",
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        session_response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
        profile_response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele has tenant scoped profile context.",
                    },
                },
            },
        )
        http_response = client.post(
            "/memory/remember",
            headers=headers,
            json={"input": "Daniele likes tenant scoped coffee."},
        )

    assert session_response.status_code == 200
    session_payload = session_response.json()["result"]["structuredContent"]
    user_b_settings = Settings(
        brain_database_url=db_url,
        brain_user_id="user_b",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    default_settings = Settings(
        brain_database_url=db_url,
        brain_user_id="default",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    assert session_payload["user_id"] == "user_b"
    assert profile_response.status_code == 200
    assert profile_response.json()["result"]["structuredContent"]["user_id"] == "user_b"
    assert http_response.status_code == 200

    user_b_receipts = BrainStore(user_b_settings).list_external_receipts(action="remember")
    default_receipts = BrainStore(default_settings).list_external_receipts(action="remember")
    assert user_b_receipts
    assert default_receipts == []
    assert BrainStore(user_b_settings).list_context_records(kind="profile")
    assert BrainStore(default_settings).list_context_records(kind="profile") == []


def test_personal_access_token_scopes_headless_agent_to_user(tmp_path) -> None:
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps(
            [
                {"id": "admin", "password": "admin-pass", "superuser": True},
                {"id": "agent_user", "password": "agent-pass", "display_name": "Agent User"},
            ]
        ),
        encoding="utf-8",
    )
    with oauth_settings(
        tmp_path,
        brain_auth_users_file=str(users_file),
        brain_user_id="admin",
    ):
        client = TestClient(app, follow_redirects=False)
        admin_token = issue_test_oauth_token(
            client,
            tmp_path,
            scope="brain.memory.read brain.memory.write",
            user_id="admin",
            password="admin-pass",
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        create_response = client.post(
            "/admin/tokens",
            headers=admin_headers,
            json={
                "user_id": "agent_user",
                "name": "local-agent",
                "scopes": ["brain.memory.read", "brain.memory.write"],
            },
        )
        token_payload = create_response.json()
        pat = token_payload["token"]
        token_id = token_payload["personal_access_token"]["id"]
        agent_headers = {"Authorization": f"Bearer {pat}"}
        session_response = client.post(
            "/mcp",
            headers=agent_headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
        list_response = client.get("/admin/tokens?user_id=agent_user", headers=admin_headers)
        revoke_response = client.delete(f"/admin/tokens/{token_id}", headers=admin_headers)
        revoked_session_response = client.post(
            "/mcp",
            headers=agent_headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )

    assert create_response.status_code == 201
    assert pat.startswith("brain_pat_")
    assert pat not in (tmp_path / "brain-oauth.json").read_text(encoding="utf-8")
    assert session_response.status_code == 200
    assert session_response.json()["result"]["structuredContent"]["user_id"] == "agent_user"
    listed = list_response.json()["personal_access_tokens"]
    assert [token["id"] for token in listed] == [token_id]
    assert listed[0]["last_used_at"]
    assert revoke_response.status_code == 200
    assert revoke_response.json()["revoked"]["revoked_at"]
    assert revoked_session_response.status_code == 401


def test_superuser_can_manage_auth_users_without_restart(tmp_path) -> None:
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps(
            [
                {"id": "admin", "password": "admin-pass", "display_name": "Admin", "superuser": True},
                {"id": "user_a", "password": "pass-a", "display_name": "User A"},
            ]
        ),
        encoding="utf-8",
    )
    with oauth_settings(
        tmp_path,
        brain_auth_users_file=str(users_file),
        brain_user_id="admin",
    ):
        client = TestClient(app, follow_redirects=False)
        admin_token = issue_test_oauth_token(
            client,
            tmp_path,
            scope="brain.memory.read brain.memory.write",
            user_id="admin",
            password="admin-pass",
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        list_response = client.get("/admin/users", headers=admin_headers)
        create_response = client.post(
            "/admin/users",
            headers=admin_headers,
            json={
                "id": "user_b",
                "password": "pass-b",
                "display_name": "User B",
                "email": "user-b@example.com",
            },
        )
        update_response = client.put(
            "/admin/users/user_b",
            headers=admin_headers,
            json={"display_name": "User Bee", "superuser": False},
        )
        user_b_token = issue_test_oauth_token(
            client,
            tmp_path,
            scope="brain.memory.read brain.memory.write",
            user_id="user_b",
            password="pass-b",
        )
        forbidden_response = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {user_b_token}"},
        )

    assert list_response.status_code == 200
    assert list_response.json()["users_file"] == str(users_file)
    assert list_response.json()["current_user_id"] == "admin"
    assert all("password" not in user for user in list_response.json()["users"])
    assert create_response.status_code == 201
    assert create_response.json()["user"]["id"] == "user_b"
    assert create_response.json()["user"]["display_name"] == "User B"
    assert create_response.json()["user"]["email"] == "user-b@example.com"
    assert create_response.json()["user"]["superuser"] is False
    assert create_response.json()["user"]["password_scheme"] == "argon2id"
    assert update_response.status_code == 200
    assert update_response.json()["user"]["display_name"] == "User Bee"
    assert forbidden_response.status_code == 403
    stored = json.loads(users_file.read_text(encoding="utf-8"))
    user_b = next(record for record in stored if record["id"] == "user_b")
    assert "password" not in user_b
    assert user_b["password_hash"].startswith("$argon2id$")


def test_superuser_cannot_delete_self_or_last_superuser(tmp_path) -> None:
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps([{"id": "admin", "password": "admin-pass", "superuser": True}]),
        encoding="utf-8",
    )
    with oauth_settings(
        tmp_path,
        brain_auth_users_file=str(users_file),
        brain_user_id="admin",
    ):
        client = TestClient(app, follow_redirects=False)
        admin_token = issue_test_oauth_token(
            client,
            tmp_path,
            scope="brain.memory.read brain.memory.write",
            user_id="admin",
            password="admin-pass",
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        delete_response = client.delete("/admin/users/admin", headers=headers)
        demote_response = client.put("/admin/users/admin", headers=headers, json={"superuser": False})

    assert delete_response.status_code == 400
    assert demote_response.status_code == 400


def test_dashboard_cookie_session_scopes_mcp_without_bearer_token(tmp_path) -> None:
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps([{"id": "daniele", "password": "pass-a", "display_name": "Daniele"}]),
        encoding="utf-8",
    )
    with oauth_settings(
        tmp_path,
        brain_auth_users_file=str(users_file),
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    ):
        client = TestClient(app, base_url="https://testserver")
        login_response = client.post("/login", json={"user_id": "daniele", "password": "pass-a"})
        csrf = login_response.json()["csrf_token"]
        no_csrf_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
        session_response = client.post(
            "/mcp",
            headers={"X-Brain-CSRF": csrf},
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_session", "arguments": {}},
            },
        )
        internal_response = client.post(
            "/admin/mcp",
            headers={"X-Brain-CSRF": csrf},
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
            },
        )
        session_info = client.get("/auth/session")

    assert login_response.status_code == 200
    assert "brain_web_session" in login_response.headers["set-cookie"]
    assert "httponly" in login_response.headers["set-cookie"].lower()
    assert no_csrf_response.status_code == 403
    assert session_response.status_code == 200
    assert session_response.json()["result"]["structuredContent"]["user_id"] == "daniele"
    assert internal_response.status_code == 403
    assert session_info.status_code == 200
    assert session_info.json()["user"]["id"] == "daniele"


def test_dashboard_cookie_session_can_change_own_password(tmp_path) -> None:
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps([{"id": "daniele", "password": "old-pass", "display_name": "Daniele"}]),
        encoding="utf-8",
    )
    with oauth_settings(tmp_path, brain_auth_users_file=str(users_file)):
        client = TestClient(app, base_url="https://testserver")
        login_response = client.post("/login", json={"user_id": "daniele", "password": "old-pass"})
        csrf = login_response.json()["csrf_token"]
        change_response = client.put(
            "/account/password",
            headers={"X-Brain-CSRF": csrf},
            json={"current_password": "old-pass", "new_password": "new-pass"},
        )
        old_login_response = client.post("/login", json={"user_id": "daniele", "password": "old-pass"})
        new_login_response = client.post("/login", json={"user_id": "daniele", "password": "new-pass"})

    assert change_response.status_code == 200
    assert old_login_response.status_code == 401
    assert new_login_response.status_code == 200


def test_superuser_cookie_session_can_manage_users(tmp_path) -> None:
    users_file = tmp_path / "brain-users.json"
    users_file.write_text(
        json.dumps([{"id": "root", "password": "root-pass", "display_name": "Root", "superuser": True}]),
        encoding="utf-8",
    )
    with oauth_settings(tmp_path, brain_auth_users_file=str(users_file), brain_user_id="root"):
        client = TestClient(app, base_url="https://testserver")
        login_response = client.post("/login", json={"user_id": "root", "password": "root-pass"})
        csrf = login_response.json()["csrf_token"]
        create_response = client.post(
            "/admin/users",
            headers={"X-Brain-CSRF": csrf},
            json={"id": "daniele", "password": "pass-a", "display_name": "Daniele"},
        )
        list_response = client.get("/admin/users")

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert {user["id"] for user in list_response.json()["users"]} == {"root", "daniele"}


def test_oauth_register_rate_limit(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "OAUTH_RATE_LIMITS",
        {**mcp_server.OAUTH_RATE_LIMITS, "register": (2, 60)},
    )
    mcp_server._rate_limit_buckets.clear()
    try:
        with oauth_settings(tmp_path):
            client = TestClient(app)
            payload = {
                "client_name": "test-client",
                "redirect_uris": ["http://127.0.0.1/callback"],
                "token_endpoint_auth_method": "none",
                "scope": "brain.memory.read brain.memory.write",
            }
            first = client.post("/register", json=payload)
            second = client.post("/register", json=payload)
            third = client.post("/register", json=payload)
    finally:
        mcp_server._rate_limit_buckets.clear()

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429
    assert third.json()["error"] == "rate_limited"


def test_request_response_logger_redacts_secrets(tmp_path) -> None:
    log_path = tmp_path / "requests.jsonl"
    settings = Settings(
        brain_request_log_path=str(log_path),
        brain_request_log_max_body_bytes=8192,
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


def test_request_logger_zero_body_limit_omits_bodies(tmp_path) -> None:
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
    response = client.post("/echo", json={"text": "do not log this body"})

    assert response.status_code == 200
    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["request"]["body"] is None
    assert record["request"]["body_truncated"] is True
    assert record["response"]["body"] is None
    assert record["response"]["body_truncated"] is True


def test_request_logger_writes_dated_logs_and_summarizes_large_sources(tmp_path) -> None:
    log_template = tmp_path / "requests" / "{date}.jsonl"
    settings = Settings(
        brain_request_log_path=str(log_template),
        brain_request_log_max_body_bytes=8192,
        brain_request_log_retention_days=30,
    )
    test_app = FastAPI()
    test_app.add_middleware(RequestResponseLogMiddleware, settings=settings)

    @test_app.post("/echo")
    async def echo(request: Request) -> JSONResponse:
        return JSONResponse(await request.json())

    large_source = "source text " * 200
    client = TestClient(test_app)
    response = client.post(
        "/echo",
        json={"source": large_source, "title": "large source"},
    )

    assert response.status_code == 200
    log_files = list((tmp_path / "requests").glob("*.jsonl"))
    assert len(log_files) == 1
    record = json.loads(log_files[0].read_text(encoding="utf-8"))
    source = record["request"]["body"]["source"]
    assert source["body_omitted"] is True
    assert source["chars"] == len(large_source)
    assert source["sha256"] == hashlib.sha256(large_source.encode("utf-8")).hexdigest()
    assert source["preview"] == large_source[:500]


def test_request_logger_redacts_auth_urls_and_html() -> None:
    redacted_url = redact_url("http://127.0.0.1/callback?code=abc&state=keep")
    assert "code=%5BREDACTED%5D" in redacted_url
    assert "abc" not in redacted_url
    assert "state=keep" in redacted_url

    redacted_html = redact_text('<input name="request_id" value="secret-request-id">')
    assert "secret-request-id" not in redacted_html
    assert "[REDACTED]" in redacted_html


class oauth_settings:
    def __init__(self, tmp_path, **overrides) -> None:
        self.tmp_path = tmp_path
        self.overrides = overrides
        self.previous_settings = mcp_server.settings
        self.previous_provider = mcp_server.oauth_provider

    def __enter__(self) -> None:
        overrides = dict(self.overrides)
        password_file = self.tmp_path / "brain-auth-password"
        users_file = overrides.get("brain_auth_users_file")
        if users_file is None:
            password_file.write_text("test-auth-password\n", encoding="utf-8")
            users_file = self.tmp_path / "brain-auth-users.json"
            users_file.write_text(
                json.dumps(
                    [
                        {
                            "id": overrides.get("brain_user_id", "default"),
                            "password": "test-auth-password",
                            "display_name": "Test User",
                            "superuser": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            overrides["brain_auth_users_file"] = str(users_file)
        settings = Settings(
            brain_auth_password_file=str(password_file),
            brain_auth_state_path=str(self.tmp_path / "brain-oauth.json"),
            brain_public_base_url="https://brain.dceb.net",
            brain_public_mcp_path="/mcp",
            brain_public_admin_mcp_path="/admin/mcp",
            **overrides,
        )
        mcp_server.settings = settings
        mcp_server.oauth_provider = BrainOAuthProvider(settings)

    def __exit__(self, exc_type, exc, tb) -> None:
        mcp_server.settings = self.previous_settings
        mcp_server.oauth_provider = self.previous_provider


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def fake_cognee(calls):
    def remember_text(
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> dict[str, str]:
        del settings
        calls.append(
            {
                "text": text,
                "dataset_name": dataset_name,
                "node_set": node_set or [],
            }
        )
        return {"id": f"fake-{len(calls)}"}

    return remember_text


def issue_test_oauth_token(
    client: TestClient,
    tmp_path,
    *,
    scope: str,
    user_id: str | None = None,
    password: str | None = None,
) -> str:
    register_response = client.post(
        "/register",
        json={
            "client_name": "test-client",
            "redirect_uris": ["http://127.0.0.1/callback"],
            "token_endpoint_auth_method": "none",
            "scope": scope,
        },
    )
    assert register_response.status_code == 201
    client_id = register_response.json()["client_id"]
    verifier = "test-code-verifier"
    authorize_response = client.get(
        "/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "http://127.0.0.1/callback",
            "scope": scope,
            "state": "abc",
            "code_challenge": pkce_challenge(verifier),
            "code_challenge_method": "S256",
        },
    )
    assert authorize_response.status_code == 200
    request_id_match = re.search(r'name="request_id" value="([^"]+)"', authorize_response.text)
    assert request_id_match
    password = password or (tmp_path / "brain-auth-password").read_text(encoding="utf-8").strip()
    authorization_data = {"request_id": request_id_match.group(1), "password": password}
    if user_id is not None:
        authorization_data["user_id"] = user_id
    complete_response = client.post(
        "/authorize",
        data=authorization_data,
    )
    assert complete_response.status_code == 302
    code = parse_qs(urlsplit(complete_response.headers["location"]).query)["code"][0]
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
    return token_response.json()["access_token"]
