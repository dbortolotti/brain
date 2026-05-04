from __future__ import annotations

import argparse
import json
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from memory_stack.cognee_adapter import (
    DatasourceNotFoundError,
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    list_datasources as list_cognee_datasources,
    recall_text,
    remember_text,
)
from memory_stack.config import Settings, load_settings
from memory_stack.oauth import BrainOAuthProvider, parse_bearer
from memory_stack.request_logging import RequestResponseLogMiddleware

STARTED_AT = time.time()
settings = load_settings()
oauth_provider = BrainOAuthProvider(settings) if settings.brain_auth_enabled else None

app = FastAPI(title="Brain MCP", version="0.1.0")
if settings.brain_request_log_enabled:
    app.add_middleware(RequestResponseLogMiddleware, settings=settings)


class CreateDatasourceRequest(BaseModel):
    name: str


class DeleteDatasourceRequest(BaseModel):
    name: str | None = None
    id: str | None = None


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    headers = dict(exc.headers or {})
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        headers.update({"Cache-Control": "no-store", "Pragma": "no-cache"})
        return JSONResponse(
            exc.detail,
            status_code=exc.status_code,
            headers=headers,
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=headers)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.brain_service_name,
        "mcp_path": settings.brain_mcp_path,
        "public_mcp_url": settings.public_mcp_url,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
    }


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/{resource_path:path}")
async def oauth_protected_resource(resource_path: str = "") -> dict[str, Any]:
    if oauth_provider:
        return oauth_provider.protected_resource_metadata()

    normalized_resource_path = "/" + resource_path.strip("/")
    resource_url = f"{settings.brain_public_base_url.rstrip('/')}{normalized_resource_path}"
    return {
        "resource": resource_url,
        "resource_name": settings.brain_service_name,
        "authorization_servers": [settings.brain_public_base_url.rstrip("/")],
        "scopes_supported": settings.oauth_scopes,
        "bearer_methods_supported": ["header"],
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server() -> dict[str, Any]:
    if oauth_provider:
        return oauth_provider.authorization_server_metadata()
    base = settings.brain_public_base_url.rstrip("/")
    return {
        "issuer": base,
        "service": settings.brain_service_name,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "scopes_supported": settings.oauth_scopes,
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
    }


@app.post("/register")
async def register_client(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.register_client(request)


@app.api_route("/authorize", methods=["GET", "POST"])
async def authorize(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.authorize(request)


@app.post("/token")
async def token(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.token(request)


@app.post("/revoke")
async def revoke(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.revoke(request)


@app.get("/datasources")
@app.get("/list_datasources")
async def list_datasources_endpoint(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {"datasources": await list_cognee_datasources(settings=settings)}


@app.post("/datasources", status_code=201)
@app.post("/create_datasource", status_code=201)
async def create_datasource_endpoint(
    payload: CreateDatasourceRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {
        "datasource": await create_cognee_datasource(payload.name, settings=settings),
    }


@app.delete("/datasources/{datasource}")
@app.delete("/delete_datasource/{datasource}")
async def delete_datasource_path_endpoint(
    datasource: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {"datasource": await delete_datasource_or_404(datasource)}


@app.post("/delete_datasource")
async def delete_datasource_endpoint(
    payload: DeleteDatasourceRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    datasource = payload.id or payload.name
    if datasource is None:
        raise HTTPException(status_code=422, detail="Provide datasource id or name.")
    return {"datasource": await delete_datasource_or_404(datasource)}


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def mcp_route(
    path: str,
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    requested_path = "/" + path.strip("/")
    if requested_path != settings.brain_mcp_path:
        raise HTTPException(status_code=404, detail="Not found")

    if settings.brain_auth_enabled and not valid_bearer(authorization, settings):
        return auth_challenge(settings)

    if request.method == "GET":
        return JSONResponse(
            {
                "service": settings.brain_service_name,
                "mcp_path": settings.brain_mcp_path,
                "public_mcp_url": settings.public_mcp_url,
                "status": "ready",
            }
        )

    payload = await request.json()
    response_payload = await handle_json_rpc(payload)
    return JSONResponse(response_payload)


def valid_bearer(header_value: str | None, active_settings: Settings) -> bool:
    if active_settings.brain_auth_token:
        expected = f"Bearer {active_settings.brain_auth_token}"
        if header_value == expected:
            return True
    token = parse_bearer(header_value)
    if oauth_provider and token:
        return oauth_provider.validate_access_token(
            token,
            active_settings.brain_auth_scope_list,
        )
    return False


def auth_challenge(active_settings: Settings) -> Response:
    return JSONResponse(
        authentication_required_payload(active_settings),
        status_code=401,
        headers=auth_challenge_headers(active_settings),
    )


def require_api_auth(header_value: str | None, active_settings: Settings) -> None:
    if active_settings.brain_auth_enabled and not valid_bearer(header_value, active_settings):
        raise HTTPException(
            status_code=401,
            detail=authentication_required_payload(active_settings),
            headers=auth_challenge_headers(active_settings),
        )


def authentication_required_payload(active_settings: Settings) -> dict[str, str]:
    return {"error": "authentication_required", "service": active_settings.brain_service_name}


def auth_challenge_headers(active_settings: Settings) -> dict[str, str]:
    return {
        "WWW-Authenticate": (
            'Bearer realm="Brain", '
            f'resource_metadata="{active_settings.protected_resource_metadata_url}", '
            f'scope="{" ".join(active_settings.brain_auth_scope_list)}"'
        )
    }


async def delete_datasource_or_404(datasource: str) -> dict[str, Any]:
    try:
        return await delete_cognee_datasource(datasource, settings=settings)
    except DatasourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def handle_json_rpc(payload: Any) -> Any:
    if isinstance(payload, list):
        return [await handle_json_rpc(item) for item in payload]

    request_id = payload.get("id") if isinstance(payload, dict) else None
    method = payload.get("method") if isinstance(payload, dict) else None
    params = payload.get("params", {}) if isinstance(payload, dict) else {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "brain", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "remember",
                        "description": "Store text in Cognee memory.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "dataset_name": {"type": "string"},
                                "temporal": {"type": "boolean", "default": True},
                            },
                            "required": ["text", "dataset_name"],
                        },
                    },
                    {
                        "name": "recall",
                        "description": "Recall text from Cognee memory.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "dataset": {"type": "string", "default": "property_trial"},
                                "search_type": {"type": "string", "default": "TEMPORAL"},
                                "top_k": {"type": "integer", "default": 10},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "list_datasources",
                        "description": "List Cognee datasources.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                    {
                        "name": "create_datasource",
                        "description": "Create a Cognee datasource.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                    {
                        "name": "delete_datasource",
                        "description": "Delete a Cognee datasource by name or id.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "id": {"type": "string"},
                            },
                        },
                    },
                ]
            }
        elif method == "tools/call":
            result = await call_tool(params)
        elif method and method.startswith("notifications/"):
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        else:
            return json_rpc_error(request_id, -32601, f"Unknown method: {method}")
    except Exception as exc:
        return json_rpc_error(request_id, -32000, str(exc))

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


async def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name == "remember":
        text = str(arguments["text"])
        dataset_name = str(arguments["dataset_name"])
        temporal = bool(arguments.get("temporal", True))
        await remember_text(text, dataset_name=dataset_name, temporal=temporal, settings=settings)
        return {"content": [{"type": "text", "text": "remembered"}]}

    if name == "recall":
        result = await recall_text(
            query=str(arguments["query"]),
            dataset=str(arguments.get("dataset", "property_trial")),
            search_type=str(arguments.get("search_type", "TEMPORAL")),
            top_k=int(arguments.get("top_k", 10)),
            settings=settings,
        )
        return {"content": [{"type": "text", "text": str(result)}]}

    if name == "list_datasources":
        datasources = await list_cognee_datasources(settings=settings)
        return json_tool_response({"datasources": datasources})

    if name == "create_datasource":
        datasource = await create_cognee_datasource(str(arguments["name"]), settings=settings)
        return json_tool_response({"datasource": datasource})

    if name == "delete_datasource":
        datasource = arguments.get("id") or arguments.get("name")
        if datasource is None:
            raise ValueError("delete_datasource requires name or id.")
        return json_tool_response(
            {"datasource": await delete_cognee_datasource(str(datasource), settings=settings)}
        )

    raise ValueError(f"Unknown tool: {name}")


def json_tool_response(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


def json_rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=settings.brain_mcp_host)
    parser.add_argument("--port", type=int, default=settings.brain_mcp_port)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "memory_stack.mcp_server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
