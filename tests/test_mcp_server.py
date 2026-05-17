from __future__ import annotations

import base64
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.mcp_server import app
from memory_stack import mcp_server
from memory_stack import brain_service
from memory_stack.oauth import BrainOAuthProvider
from memory_stack.request_logging import RequestResponseLogMiddleware, redact_text, redact_url
from memory_stack.session import agent_memory_dataset_for_user, agent_memory_session_id_for_user


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


def test_brain_app_ui_routes() -> None:
    client = TestClient(app)

    root_response = client.get("/")
    app_response = client.get("/app")
    callback_response = client.get("/app/oauth/callback")
    css_response = client.get("/app-assets/app.css")
    js_response = client.get("/app-assets/app.js")
    privacy_response = client.get("/privacy")
    terms_response = client.get("/terms")
    support_response = client.get("/support")

    assert root_response.status_code == 200
    assert "Brain" in root_response.text
    assert "/privacy" in root_response.text
    assert "Memory Contents" in root_response.text
    assert "Latest Session Data" in root_response.text
    assert "Custom Preprompt Instructions" in root_response.text
    assert "Data Controls" in root_response.text
    assert "User Admin" in root_response.text
    assert "Endpoint Help" in root_response.text
    assert app_response.status_code == 200
    assert callback_response.status_code == 200
    assert css_response.status_code == 200
    assert css_response.headers["content-type"].startswith("text/css")
    assert js_response.status_code == 200
    assert privacy_response.status_code == 200
    assert "Brain Privacy" in privacy_response.text
    assert terms_response.status_code == 200
    assert "Brain Terms" in terms_response.text
    assert support_response.status_code == 200
    assert "Brain Support" in support_response.text
    for page_response in (root_response, privacy_response, terms_response, support_response):
        assert "frame-ancestors" in page_response.headers["content-security-policy"]
        assert "chatgpt.com" in page_response.headers["content-security-policy"]
        assert page_response.headers["strict-transport-security"].startswith("max-age=")
        assert page_response.headers["referrer-policy"] == "no-referrer"
        assert page_response.headers["x-content-type-options"] == "nosniff"
    assert "mcpCall" in js_response.text
    assert "loginUser" in js_response.text
    assert "csrfHeader" in js_response.text
    assert "showMemoryDetails" in js_response.text
    assert "refreshPrompt" in js_response.text
    assert "refreshControls" in js_response.text
    assert "refreshUsers" in js_response.text
    assert "refreshEndpointHelp" in js_response.text
    assert "/admin/cognee-api/{path}" in js_response.text
    assert "/slack/commands" in js_response.text
    assert "brain_preprompt" in js_response.text


def test_public_http_redirects_to_https_for_cookie_auth(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app, base_url="http://brain.dceb.net", follow_redirects=False)
        response = client.get("/")
        forwarded_https_response = client.get("/", headers={"X-Forwarded-Proto": "https"})
        local_response = client.get("http://127.0.0.1:18100/healthz")

    assert response.status_code == 307
    assert response.headers["location"] == "https://brain.dceb.net/"
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
        "brain_app_data_controls",
        "brain_profile_context_sync",
        "brain_remember",
        "brain_ingest_source",
        "brain_recall",
        "brain_profile_entity",
        "brain_list_open_loops",
        "brain_get_memory",
        "brain_get_source",
        "brain_resolve_conflict",
        "brain_forget",
        "brain_review_recent",
        "brain_undo_last",
        "brain_sync_cognee",
        "brain_rebuild_cognee",
        "cognee_improve",
        "brain_agent_memory",
        "brain_agent_memory_recall",
        "brain_agent_memory_clear",
        "brain_merge_entities",
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


def test_chatgpt_app_surface_lists_only_safe_tools() -> None:
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 200
    tool_names = {tool["name"] for tool in response.json()["result"]["tools"]}
    assert tool_names == mcp_server.CHATGPT_APP_TOOLS
    assert {
        "brain_forget",
        "brain_sync_cognee",
        "brain_rebuild_cognee",
        "cognee_improve",
        "brain_agent_memory_clear",
        "brain_palate_remember",
    }.isdisjoint(tool_names)
    remember = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_remember")
    assert "previews by default" in remember["description"]
    ingest_source = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_ingest_source")
    assert "previews by default" in ingest_source["description"]
    palate_query = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_palate_query")
    palate_confirm = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_palate_confirm")
    for tool in response.json()["result"]["tools"]:
        assert tool["securitySchemes"] == tool["_meta"]["securitySchemes"]
        if tool["name"] in {"brain_session", "brain_review_recent", "brain_app_data_controls"}:
            assert tool["_meta"]["ui"] == {
                "visibility": ["model", "app"],
                "resourceUri": "ui://brain/review.html",
            }
            assert tool["_meta"]["openai/outputTemplate"] == "ui://brain/review.html"
        else:
            assert tool["_meta"]["ui"] == {"visibility": ["model"]}
        assert tool["_meta"]["openai/visibility"] == "public"
        assert isinstance(tool["_meta"]["openai/toolInvocation/invoking"], str)
        assert isinstance(tool["_meta"]["openai/toolInvocation/invoked"], str)
        assert tool["annotations"]["openWorldHint"] is False
        expected_scopes = (
            ["brain.memory.read", "brain.memory.write"]
            if tool["name"] in mcp_server.APP_MUTATING_TOOLS
            else ["brain.memory.read"]
        )
        assert tool["securitySchemes"] == [{"type": "oauth2", "scopes": expected_scopes}]
    assert remember["annotations"]["readOnlyHint"] is False
    assert remember["annotations"]["destructiveHint"] is False
    assert remember["_meta"]["brain/requiresUserConfirmation"] is True
    assert ingest_source["annotations"]["readOnlyHint"] is False
    assert ingest_source["_meta"]["brain/requiresUserConfirmation"] is True
    assert palate_query["annotations"]["readOnlyHint"] is True
    assert palate_query["_meta"]["brain/requiresUserConfirmation"] is False
    assert palate_confirm["annotations"]["readOnlyHint"] is False
    assert palate_confirm["_meta"]["brain/requiresUserConfirmation"] is True
    recall = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_recall")
    assert recall["annotations"]["readOnlyHint"] is True
    assert recall["_meta"]["brain/requiresUserConfirmation"] is False
    data_controls = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_app_data_controls")
    assert data_controls["annotations"]["readOnlyHint"] is True
    undo = next(tool for tool in response.json()["result"]["tools"] if tool["name"] == "brain_undo_last")
    assert undo["annotations"]["destructiveHint"] is True


def test_chatgpt_app_surface_blocks_admin_tool_call() -> None:
    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "brain_rebuild_cognee", "arguments": {"confirm": True}},
        },
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == -32000
    assert "not available on the chatgpt_app MCP surface" in response.json()["error"]["message"]


def test_chatgpt_app_destructive_tools_require_confirmation(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        context_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele prefers confirmation gates.",
                        "confirmed_by_user": True,
                    },
                },
            },
        )
        context_id = context_response.json()["result"]["structuredContent"]["id"]
        unconfirmed_forget = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_forget",
                    "arguments": {"context_id": context_id},
                },
            },
        )
        confirmed_forget = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_forget",
                    "arguments": {
                        "context_id": context_id,
                        "confirmed_by_user": True,
                    },
                },
            },
        )
        unconfirmed_undo = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "brain_undo_last", "arguments": {}},
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert unconfirmed_forget.status_code == 200
    assert "Explicit user confirmation is required" in unconfirmed_forget.json()["error"]["message"]
    assert confirmed_forget.status_code == 200
    assert confirmed_forget.json()["result"]["structuredContent"]["status"] == "deleted"
    assert unconfirmed_undo.status_code == 200
    assert "Explicit user confirmation is required" in unconfirmed_undo.json()["error"]["message"]


def test_chatgpt_app_profile_context_remember_requires_confirmation(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        unconfirmed_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {"statement": "Daniele prefers explicit saves."},
                },
            },
        )
        confirmed_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele prefers explicit saves.",
                        "confirmed_by_user": True,
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert unconfirmed_response.status_code == 200
    assert "Explicit user confirmation is required" in unconfirmed_response.json()["error"]["message"]
    assert confirmed_response.status_code == 200
    assert confirmed_response.json()["result"]["structuredContent"]["created"] is True


def test_chatgpt_app_accepts_context_confirmation_and_audits_write(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        confirmed_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "ctx-confirm",
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele accepts context confirmation.",
                        "context": {"confirmed_by_user": True},
                    },
                },
            },
        )
        controls_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_app_data_controls", "arguments": {"limit": 10}},
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert confirmed_response.status_code == 200
    context_id = confirmed_response.json()["result"]["structuredContent"]["id"]
    assert controls_response.status_code == 200
    assert len(controls_response.json()["result"]["content"]) == 1
    controls = controls_response.json()["result"]["structuredContent"]
    assert any(item["id"] == context_id for item in controls["profile_context"])
    assert any(
        item["tool_name"] == "brain_profile_context_remember"
        and item["target_id"] == context_id
        and item["confirmed_by_user"] == 1
        for item in controls["app_write_audit"]
    )
    controls_json = json.dumps(controls)
    for forbidden in [
        "user_id",
        "password",
        "password_hash",
        "client_id",
        "request_id",
        "remote_addr",
        "resolved_agent_memory_dataset",
    ]:
        assert forbidden not in controls_json


def test_chatgpt_app_remember_requires_confirmation(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        preview_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_remember",
                    "arguments": {
                        "input": "Remember that app-surface writes require user confirmation.",
                        "input_type": "fact",
                    },
                },
            },
        )
        confirmed_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_remember",
                    "arguments": {
                        "input": "Remember that app-surface writes require user confirmation.",
                        "input_type": "fact",
                        "dry_run": False,
                        "context": {"confirmed_by_user": True},
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert preview_response.status_code == 200
    preview = preview_response.json()["result"]["structuredContent"]
    assert preview["dry_run"] is True
    assert all(card["created"] is False for card in preview["memory_cards"])

    assert confirmed_response.status_code == 200
    confirmed = confirmed_response.json()["result"]["structuredContent"]
    assert confirmed["dry_run"] is False
    assert any(card["created"] is True for card in confirmed["memory_cards"])


def test_chatgpt_app_ingest_source_previews_until_confirmed(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
    )
    try:
        client = TestClient(app, base_url="https://testserver")
        preview_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_ingest_source",
                    "arguments": {
                        "source": "Article: app-surface source ingestion previews first.",
                        "source_kind": "article",
                        "title": "App source preview",
                    },
                },
            },
        )
        confirmed_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_ingest_source",
                    "arguments": {
                        "source": "Article: app-surface source ingestion saves after confirmation.",
                        "source_kind": "article",
                        "title": "App source confirmed",
                        "dry_run": False,
                        "confirmed_by_user": True,
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert preview_response.status_code == 200
    preview = preview_response.json()["result"]["structuredContent"]
    assert preview["ingestion"]["dry_run"] is True
    assert preview["source_id"] is None

    assert confirmed_response.status_code == 200
    confirmed = confirmed_response.json()["result"]["structuredContent"]
    assert confirmed["ingestion"]["dry_run"] is False
    assert confirmed["source_id"]


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
        "brain_remember",
        "brain_recall",
        "brain_profile_entity",
        "brain_list_open_loops",
        "brain_get_memory",
        "brain_get_source",
        "brain_resolve_conflict",
        "brain_forget",
        "brain_review_recent",
        "brain_undo_last",
        "brain_sync_cognee",
        "brain_rebuild_cognee",
        "cognee_improve",
        "brain_agent_memory",
        "brain_agent_memory_recall",
        "brain_agent_memory_clear",
        "brain_merge_entities",
        "brain_palate_remember",
        "brain_palate_evaluate_options",
    } <= set(tools)

    assert tools["brain_session"]["inputSchema"]["properties"] == {}
    assert tools["brain_session"]["outputSchema"]["required"] == ["session_id"]
    session_output = tools["brain_session"]["outputSchema"]["properties"]
    assert "profile_context" in session_output
    assert "agent_memory_workflow" in session_output
    assert "resolved_agent_memory_dataset" in session_output
    profile_context_properties = tools["brain_profile_context_remember"]["inputSchema"]["properties"]
    assert {"statement", "scope", "source"} <= set(profile_context_properties)

    remember_properties = tools["brain_remember"]["inputSchema"]["properties"]
    assert "input" in remember_properties
    assert "dataset_name" not in remember_properties
    assert "node_set" not in remember_properties
    assert "memory_cards" in tools["brain_remember"]["outputSchema"]["properties"]

    recall_properties = tools["brain_recall"]["inputSchema"]["properties"]
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
    assert tools["brain_recall"]["outputSchema"]["required"] == ["answer"]
    assert {"answer", "facts", "evidence"} <= set(
        tools["brain_recall"]["outputSchema"]["properties"]
    )

    improve_properties = tools["cognee_improve"]["inputSchema"]["properties"]
    assert improve_properties["dataset"]["enum"] == ["memory", "sources", "data", "palate", "agent_memory"]
    assert "session_ids" in improve_properties

    agent_memory_properties = tools["brain_agent_memory"]["inputSchema"]["properties"]
    assert "session_id" in agent_memory_properties
    assert tools["brain_agent_memory"]["inputSchema"]["required"] == ["session_id"]

    taste_properties = tools["brain_palate_remember"]["inputSchema"]["properties"]
    assert {"type", "canonical_name", "description"} <= set(taste_properties)
    assert "taste_records" in tools["brain_palate_remember"]["outputSchema"]["properties"]

    forget_properties = tools["brain_forget"]["inputSchema"]["properties"]
    assert forget_properties["object_type"]["enum"] == [
        "memory",
        "source",
        "entity",
        "relationship",
        "open_loop",
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
        brain_agent_memory_session_id="portable_agent_session",
        brain_cognee_agent_memory_dataset="agent_memory_test",
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
    assert payload["session_id"] == agent_memory_session_id_for_user(active_settings)
    assert payload["profile_name"] == "Daniele"
    assert payload["profile_full_name"] == "Daniele Bortolotti"
    assert payload["profile_context"] == []
    assert payload["bias_prompt"] == "brain_bias_protocol"
    assert payload["agent_memory_workflow"] == "brain_agent_memory"
    assert payload["resolved_agent_memory_dataset"] == agent_memory_dataset_for_user(active_settings)


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
    assert session_payload["profile_context"] == ["Daniele works in a bank as a quant."]
    assert session_payload["profile_context_records"][0]["memory_id"].startswith("mem_")
    assert session_payload["profile_context_records"][0]["owner_entity_id"].startswith("ent_")
    listed = list_response.json()["result"]["structuredContent"]["profile_context"]
    assert listed[0]["id"] == context_id
    assert forget_response.json()["result"]["structuredContent"]["status"] == "deleted"


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
    assert sync_payload["profile_context"][0]["memory_id"].startswith("mem_")
    assert "Daniele has a PhD in theoretical physics." in profile_response.json()["result"][
        "structuredContent"
    ]["answer"]
    raw_profile = BrainStore(
        Settings(
            brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
            brain_owner_full_name="Daniele Bortolotti",
            brain_owner_name="Daniele",
            brain_profile_context_path=str(tmp_path / "profile_context.json"),
        )
    ).entity_profile("Daniele")
    assert raw_profile["entity"]["canonical_name"] == "Daniele Bortolotti"
    aliases = {alias["alias"] for alias in raw_profile["aliases"]}
    assert "Daniele" not in aliases
    assert "me" in aliases


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
                        "session_ids": ["session-1"],
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["resolved_dataset"] == "palate_live"
    assert payload["session_ids"] == ["session-1"]
    assert calls[0]["dataset"] == "palate_live"
    assert calls[0]["node_name"] == ["Wine"]
    assert calls[0]["session_ids"] == ["session-1"]


def test_brain_agent_memory_uses_single_session_and_dedicated_dataset(tmp_path, monkeypatch) -> None:
    calls = []

    async def fake_improve_cognee(**kwargs):
        calls.append(kwargs)
        return {"run_id": "agent-memory-1"}

    monkeypatch.setattr(mcp_server, "improve_cognee", fake_improve_cognee)
    previous_settings = mcp_server.settings
    active_settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_cognee_agent_memory_dataset="agent_memory_test",
    )
    mcp_server.settings = active_settings
    session_id = agent_memory_session_id_for_user(active_settings)
    resolved_dataset = agent_memory_dataset_for_user(active_settings)
    try:
        client = TestClient(app)
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_agent_memory",
                    "arguments": {
                        "session_id": session_id,
                        "node_name": ["project-x"],
                    },
                },
            },
        )
        rejected = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_agent_memory",
                    "arguments": {
                        "session_id": "portable_agent_session:u_not_this_user",
                        "node_name": ["project-x"],
                    },
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["session_id"] == session_id
    assert payload["resolved_dataset"] == resolved_dataset
    assert calls[0]["dataset"] == resolved_dataset
    assert calls[0]["session_ids"] == [session_id]
    assert calls[0]["node_name"] == ["project-x"]
    assert rejected.status_code == 200
    assert "active user's session_id" in rejected.json()["error"]["message"]
    assert len(calls) == 1


def test_brain_agent_memory_recall_uses_dedicated_dataset(tmp_path, monkeypatch) -> None:
    calls = []

    async def fake_recall_text(**kwargs):
        calls.append(kwargs)
        return [{"text": "remembered agent context"}]

    monkeypatch.setattr(mcp_server, "recall_text", fake_recall_text)
    previous_settings = mcp_server.settings
    active_settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_cognee_agent_memory_dataset="agent_memory_test",
    )
    mcp_server.settings = active_settings
    resolved_dataset = agent_memory_dataset_for_user(active_settings)
    try:
        client = TestClient(app)
        response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_agent_memory_recall",
                    "arguments": {"query": "what happened last chat?"},
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["resolved_dataset"] == resolved_dataset
    assert payload["result"] == [{"text": "remembered agent context"}]
    assert calls[0]["dataset"] == resolved_dataset
    assert calls[0]["search_type"] == "GRAPH_COMPLETION"


def test_brain_agent_memory_clear_requires_confirmation(tmp_path, monkeypatch) -> None:
    calls = []

    async def fake_delete_datasource(datasource, *, settings):
        calls.append({"datasource": datasource, "settings": settings})
        return {"name": datasource, "status": "deleted"}

    monkeypatch.setattr(mcp_server, "delete_cognee_datasource", fake_delete_datasource)
    previous_settings = mcp_server.settings
    active_settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_cognee_agent_memory_dataset="agent_memory_test",
    )
    mcp_server.settings = active_settings
    resolved_dataset = agent_memory_dataset_for_user(active_settings)
    try:
        client = TestClient(app)
        rejected = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_agent_memory_clear",
                    "arguments": {},
                },
            },
        )
        accepted = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_agent_memory_clear",
                    "arguments": {"confirm": True},
                },
            },
        )
    finally:
        mcp_server.settings = previous_settings

    assert rejected.status_code == 200
    assert "confirm=true" in rejected.json()["error"]["message"]
    assert accepted.status_code == 200
    assert calls[0]["datasource"] == resolved_dataset


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
            "params": {"uri": "brain://schema/memory-card"},
        },
    )
    component_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": "ui://brain/review.html"},
        },
    )

    assert list_response.status_code == 200
    assert {
        resource["uri"] for resource in list_response.json()["result"]["resources"]
    } == {
        "ui://brain/review.html",
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
    assert component_response.status_code == 200
    component = component_response.json()["result"]["contents"][0]
    assert component["mimeType"] == "text/html+skybridge"
    assert "window.openai.callTool" in component["text"]
    assert component["_meta"]["openai/widgetCSP"]["connect_domains"]


def test_agent_memory_protocol_prompt_can_be_inserted_with_session_id() -> None:
    client = TestClient(app)
    list_response = client.post(
        "/admin/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "prompts/list"},
    )
    get_response = client.post(
        "/admin/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "prompts/get",
            "params": {
                "name": "brain_agent_memory_protocol",
                "arguments": {"session_id": "daniele"},
            },
        },
    )

    assert list_response.status_code == 200
    prompts = list_response.json()["result"]["prompts"]
    prompt_names = {prompt["name"] for prompt in prompts}
    assert {"brain_agent_memory_protocol", "brain_bias_protocol"} <= prompt_names
    agent_prompt = next(prompt for prompt in prompts if prompt["name"] == "brain_agent_memory_protocol")
    assert agent_prompt["arguments"][0]["name"] == "session_id"
    assert get_response.status_code == 200
    text = get_response.json()["result"]["messages"][0]["content"]["text"]
    assert 'Use session_id="daniele" consistently' in text
    assert "brain_agent_memory" in text
    assert "brain_agent_memory_recall" in text
    assert "Do not use `brain_remember` for chat/session memory" in text
    assert "Cognee MCP server with `remember`" not in text
    assert "Don't narrate" in text


def test_agent_memory_protocol_prompt_defaults_to_portable_session() -> None:
    client = TestClient(app)
    response = client.post(
        "/admin/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {"name": "brain_agent_memory_protocol"},
        },
    )

    assert response.status_code == 200
    text = response.json()["result"]["messages"][0]["content"]["text"]
    expected_session_id = agent_memory_session_id_for_user(mcp_server.settings)
    assert f'Use session_id="{expected_session_id}" consistently' in text


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


def test_high_level_brain_remember_and_recall_mcp_tools(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
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
        recall_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_recall",
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
        source_id = ingest_payload["source_id"]
        source_response = client.post(
            "/admin/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_get_source",
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
    assert source_payload["text"] == "# Source\nKnowledge graphs matter for Brain."
    assert source_payload["source"]["metadata_json"]["raw_text_storage"] == "brain_db_pending_cognee"


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
    assert payload["source_id"] is None
    assert payload["memory_cards_created"] == []
    assert payload["cognee_sync_status"] == "queued"
    assert submitted
    assert submitted[0].run_in_background is False


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
    assert payload["memory_cards"][0]["kind"] == "source_record"


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


def test_auth_enabled_mcp_fails_closed(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app)
        response = client.get("/admin/mcp")

    assert response.status_code == 401
    assert "Brain" in response.headers["www-authenticate"]
    assert "oauth-protected-resource/admin/mcp" in response.headers["www-authenticate"]


def test_auth_enabled_app_mcp_fails_closed_with_app_resource(tmp_path) -> None:
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


def test_chatgpt_app_requires_write_scope_for_mutating_tools(tmp_path) -> None:
    with oauth_settings(tmp_path):
        client = TestClient(app, follow_redirects=False)
        access_token = issue_test_oauth_token(client, tmp_path, scope="brain.memory.read")
        read_response = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        write_response = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "This should be blocked by scope.",
                        "confirmed_by_user": True,
                    },
                },
            },
        )

    assert read_response.status_code == 200
    assert write_response.status_code == 200
    assert "Insufficient OAuth scope" in write_response.json()["error"]["message"]


def test_oauth_user_id_scopes_app_and_http_memory_data(tmp_path) -> None:
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
                        "confirmed_by_user": True,
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
    assert "user_id" not in session_payload
    assert session_payload["session_id"] == agent_memory_session_id_for_user(user_b_settings)
    assert "resolved_agent_memory_dataset" not in session_payload
    assert session_payload["session_id"] != agent_memory_session_id_for_user(default_settings)
    assert profile_response.status_code == 200
    assert "user_id" not in profile_response.json()["result"]["structuredContent"]
    assert http_response.status_code == 200

    assert BrainStore(user_b_settings).search_memory("tenant scoped coffee")
    assert BrainStore(user_b_settings).search_memory("tenant scoped profile context")
    assert BrainStore(default_settings).search_memory("tenant scoped coffee") == []
    assert BrainStore(default_settings).search_memory("tenant scoped profile context") == []


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
    assert "user_id" not in session_response.json()["result"]["structuredContent"]
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


def test_chatgpt_app_write_rate_limit(tmp_path) -> None:
    previous_settings = mcp_server.settings
    mcp_server.settings = Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_profile_context_path=str(tmp_path / "profile_context.json"),
        brain_app_write_rate_limit_count=1,
        brain_app_write_rate_limit_window_seconds=60,
    )
    mcp_server._rate_limit_buckets.clear()
    try:
        client = TestClient(app)
        first = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele rate limit first.",
                        "confirmed_by_user": True,
                    },
                },
            },
        )
        second = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {
                        "statement": "Daniele rate limit second.",
                        "confirmed_by_user": True,
                    },
                },
            },
        )
    finally:
        mcp_server._rate_limit_buckets.clear()
        mcp_server.settings = previous_settings

    assert first.status_code == 200
    assert first.json()["result"]["structuredContent"]["created"] is True
    assert second.status_code == 200
    assert "Rate limit exceeded" in second.json()["error"]["message"]


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
            brain_auth_enabled=True,
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
