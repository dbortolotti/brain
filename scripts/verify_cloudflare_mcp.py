#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import secrets
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cfg import load_settings
from production_check_utils import command_exists, uid


console = Console()

CHATGPT_APP_TOOLS = {
    "brain_session",
    "brain_recall",
    "brain_remember",
    "brain_ingest_source",
    "brain_profile_entity",
    "brain_list_open_loops",
    "brain_get_memory",
    "brain_review_recent",
    "brain_undo_last",
    "brain_profile_context_list",
    "brain_profile_context_remember",
    "brain_profile_context_forget",
    "brain_app_data_controls",
}

APP_READ_ONLY_TOOLS = {
    "brain_session",
    "brain_recall",
    "brain_profile_entity",
    "brain_list_open_loops",
    "brain_get_memory",
    "brain_review_recent",
    "brain_profile_context_list",
    "brain_app_data_controls",
}

APP_MUTATING_TOOLS = {
    "brain_remember",
    "brain_ingest_source",
    "brain_profile_context_remember",
    "brain_profile_context_forget",
    "brain_undo_last",
}

APP_DESTRUCTIVE_TOOLS = {"brain_undo_last", "brain_profile_context_forget"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", default=None)
    parser.add_argument("--skip-local", action="store_true")
    parser.add_argument("--skip-cloudflared", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    hostname = args.hostname or settings.brain_public_base_url.removeprefix("https://")
    failures: list[str] = []

    check_dns(hostname, failures)
    check_tls(hostname, failures)
    if not args.skip_local:
        check_url(
            f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_health_path}",
            "local health",
            failures,
            require_brain=True,
        )
    check_public_mcp(settings, failures)
    check_public_admin_mcp(settings, failures)
    check_url(
        f"https://{hostname}/",
        "public Brain dashboard",
        failures,
        require_text="Brain",
    )
    for path, label in [
        ("/privacy", "public privacy page"),
        ("/terms", "public terms page"),
        ("/support", "public support page"),
    ]:
        check_url(f"https://{hostname}{path}", label, failures, require_text="Brain")
    check_protected_resource_metadata(
        f"https://{hostname}/.well-known/oauth-protected-resource{settings.brain_public_mcp_path}",
        settings,
        failures,
    )
    check_protected_resource_metadata(
        f"https://{hostname}/.well-known/oauth-protected-resource{settings.brain_public_app_mcp_path}",
        settings,
        failures,
        expected_resource=settings.public_app_mcp_url,
        label="OAuth app protected-resource metadata",
    )
    check_protected_resource_metadata(
        f"https://{hostname}/.well-known/oauth-protected-resource{settings.brain_public_admin_mcp_path}",
        settings,
        failures,
        expected_resource=settings.public_admin_mcp_url,
        label="OAuth admin protected-resource metadata",
    )
    check_authorization_server_metadata(
        f"https://{hostname}/.well-known/oauth-authorization-server",
        settings,
        failures,
    )
    if settings.brain_auth_enabled:
        check_authenticated_public_app_mcp(settings, hostname, failures)
    if not args.skip_cloudflared:
        check_cloudflared(failures)

    if failures:
        for failure in failures:
            console.print(f"[red][FAIL][/red] {failure}")
        return 1

    console.print("[green][OK][/green] Cloudflare MCP verification passed")
    return 0


def check_dns(hostname: str, failures: list[str]) -> None:
    try:
        addresses = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        failures.append(f"DNS lookup failed for {hostname}: {exc}")
        return
    if not addresses:
        failures.append(f"DNS lookup returned no addresses for {hostname}")
        return
    console.print(f"[green][OK][/green] DNS resolves for {hostname}")


def check_tls(hostname: str, failures: list[str]) -> None:
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, 443), timeout=8) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls:
                cert = tls.getpeercert()
    except Exception as exc:
        failures.append(f"TLS check failed for {hostname}: {exc}")
        return
    names = [value for key, value in cert.get("subjectAltName", []) if key == "DNS"]
    if hostname not in names and not any(name.startswith("*.") and hostname.endswith(name[1:]) for name in names):
        failures.append(f"TLS certificate SAN does not include {hostname}: {names}")
        return
    console.print(f"[green][OK][/green] TLS certificate valid for {hostname}")


def check_public_mcp(settings, failures: list[str]) -> None:
    check_public_mcp_url(
        settings.public_mcp_url,
        settings.protected_resource_metadata_url,
        settings,
        failures,
        label="public curated MCP",
    )


def check_public_admin_mcp(settings, failures: list[str]) -> None:
    check_public_mcp_url(
        settings.public_admin_mcp_url,
        settings.protected_resource_metadata_url_for_path(settings.brain_public_admin_mcp_path),
        settings,
        failures,
        label="public admin MCP",
    )


def check_public_mcp_url(
    url: str,
    expected_metadata_url: str,
    settings,
    failures: list[str],
    *,
    label: str,
) -> None:
    status, headers, body = fetch(url)
    if status is None:
        failures.append(f"{label} request failed: {body}")
        return
    if settings.brain_auth_enabled:
        if status != 401:
            failures.append(f"auth-enabled {label} did not fail closed; status={status}")
            return
        challenge = headers.get("www-authenticate") or headers.get("WWW-Authenticate") or ""
        if "Brain" not in challenge and "brain" not in challenge:
            failures.append(f"{label} auth challenge does not identify Brain: {challenge}")
            return
        if expected_metadata_url not in challenge:
            failures.append(f"{label} challenge points at wrong OAuth metadata: {challenge}")
            return
        console.print(f"[green][OK][/green] {label} fails closed with Brain auth metadata")
        return
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {body[:200]}")
        return
    if "Brain" not in body and "brain" not in body:
        failures.append(f"{label} response does not identify Brain")
        return
    console.print(f"[green][OK][/green] {label} routes to Brain")


def check_url(
    url: str,
    label: str,
    failures: list[str],
    *,
    require_brain: bool = False,
    require_text: str | None = None,
) -> None:
    status, _headers, body = fetch(url)
    if status is None:
        failures.append(f"{label} failed: {body}")
        return
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return
    if require_brain and "Brain" not in body and "brain" not in body:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body[:300]
        failures.append(f"{label} does not identify Brain: {payload}")
        return
    if require_text and require_text not in body:
        failures.append(f"{label} did not include expected text {require_text!r}")
        return
    console.print(f"[green][OK][/green] {label}: {url}")


def check_protected_resource_metadata(
    url: str,
    settings,
    failures: list[str],
    *,
    expected_resource: str | None = None,
    label: str = "OAuth protected-resource metadata",
) -> None:
    payload = fetch_json(url, label, failures)
    if not payload:
        return
    if payload.get("resource_name") != "Brain":
        failures.append(f"{label} is not Brain: {payload}")
    if payload.get("resource") != (expected_resource or settings.public_mcp_url):
        failures.append(f"{label} resource is wrong: {payload}")


def check_authorization_server_metadata(url: str, settings, failures: list[str]) -> None:
    payload = fetch_json(url, "OAuth authorization-server metadata", failures)
    if not payload:
        return
    if payload.get("service") != "Brain":
        failures.append(f"OAuth authorization-server metadata is not Brain: {payload}")
    if payload.get("issuer") != settings.brain_public_base_url.rstrip("/"):
        failures.append(f"OAuth authorization-server issuer is wrong: {payload}")


def check_authenticated_public_app_mcp(settings, hostname: str, failures: list[str]) -> None:
    failure_count = len(failures)
    issued = issue_oauth_token(settings, hostname, failures)
    if not issued:
        return
    token, refresh_token, client_id = issued

    try:
        tool_list = rpc_call(
            settings.public_app_mcp_url,
            token,
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            "authenticated ChatGPT App tools/list",
            failures,
        )
        if not tool_list:
            return
        tools = tool_list.get("result", {}).get("tools")
        if not isinstance(tools, list):
            failures.append(f"authenticated ChatGPT App tools/list returned invalid tools: {tool_list}")
            return

        tool_names = {tool.get("name") for tool in tools}
        if tool_names != CHATGPT_APP_TOOLS:
            failures.append(
                "authenticated ChatGPT App tool set is wrong: "
                f"{sorted(str(name) for name in tool_names)}"
            )
        for tool in tools:
            validate_app_tool_descriptor(tool, failures)

        blocked_admin = rpc_call(
            settings.public_app_mcp_url,
            token,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "brain_rebuild_cognee", "arguments": {"confirm": True}},
            },
            "authenticated ChatGPT App admin block",
            failures,
        )
        if blocked_admin and "not available on the chatgpt_app MCP surface" not in json.dumps(blocked_admin):
            failures.append(f"ChatGPT App admin tool did not fail closed: {blocked_admin}")

        unconfirmed_write = rpc_call(
            settings.public_app_mcp_url,
            token,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "brain_profile_context_remember",
                    "arguments": {"statement": "Verifier unconfirmed write should not save."},
                },
            },
            "authenticated ChatGPT App unconfirmed write block",
            failures,
        )
        if unconfirmed_write and "Explicit user confirmation is required" not in json.dumps(unconfirmed_write):
            failures.append(f"ChatGPT App unconfirmed write did not fail closed: {unconfirmed_write}")

        verify_confirmed_write_cleanup(settings, token, failures)
        if len(failures) == failure_count:
            console.print("[green][OK][/green] authenticated ChatGPT App MCP surface verified")
    finally:
        revoke_oauth_token(settings, client_id, token, "verifier access token", failures)
        if refresh_token:
            revoke_oauth_token(settings, client_id, refresh_token, "verifier refresh token", failures)


def verify_confirmed_write_cleanup(settings, token: str, failures: list[str]) -> None:
    statement = f"Brain verifier temporary profile context {secrets.token_urlsafe(8)}."
    confirmed_write = rpc_call(
        settings.public_app_mcp_url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "brain_profile_context_remember",
                "arguments": {
                    "statement": statement,
                    "source": "brain_production_verifier",
                    "confirmed_by_user": True,
                },
            },
        },
        "authenticated ChatGPT App confirmed write",
        failures,
    )
    context_id = (
        (confirmed_write or {})
        .get("result", {})
        .get("structuredContent", {})
        .get("id")
    )
    if not isinstance(context_id, str) or not context_id:
        failures.append(f"ChatGPT App confirmed write did not return context id: {confirmed_write}")
        return

    controls = rpc_call(
        settings.public_app_mcp_url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "brain_app_data_controls", "arguments": {"limit": 25}},
        },
        "authenticated ChatGPT App data controls",
        failures,
    )
    if controls and context_id not in json.dumps(controls):
        failures.append("ChatGPT App data controls did not include verifier test context")

    cleanup = rpc_call(
        settings.public_app_mcp_url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "brain_profile_context_forget",
                "arguments": {"context_id": context_id, "confirmed_by_user": True},
            },
        },
        "authenticated ChatGPT App confirmed cleanup",
        failures,
    )
    if cleanup and "deleted" not in json.dumps(cleanup):
        failures.append(f"ChatGPT App verifier cleanup did not delete test context: {cleanup}")


def validate_app_tool_descriptor(tool: dict, failures: list[str]) -> None:
    name = tool.get("name")
    if not isinstance(name, str):
        failures.append(f"ChatGPT App tool descriptor has no string name: {tool}")
        return
    meta = tool.get("_meta") or {}
    annotations = tool.get("annotations") or {}
    if tool.get("securitySchemes") != meta.get("securitySchemes"):
        failures.append(f"{name} does not mirror securitySchemes in _meta")
    expected_scopes = ["brain.memory.read", "brain.memory.write"] if name in APP_MUTATING_TOOLS else ["brain.memory.read"]
    if tool.get("securitySchemes") != [{"type": "oauth2", "scopes": expected_scopes}]:
        failures.append(f"{name} has wrong securitySchemes: {tool.get('securitySchemes')}")
    if meta.get("ui") != {"visibility": ["model"]}:
        failures.append(f"{name} has wrong UI visibility metadata: {meta}")
    if meta.get("openai/visibility") != "public":
        failures.append(f"{name} is missing public OpenAI visibility metadata")
    if not isinstance(meta.get("openai/toolInvocation/invoking"), str):
        failures.append(f"{name} is missing invoking status metadata")
    if not isinstance(meta.get("openai/toolInvocation/invoked"), str):
        failures.append(f"{name} is missing invoked status metadata")
    if annotations.get("openWorldHint") is not False:
        failures.append(f"{name} must declare openWorldHint=false")
    if annotations.get("readOnlyHint") is not (name in APP_READ_ONLY_TOOLS):
        failures.append(f"{name} has wrong readOnlyHint: {annotations}")
    if annotations.get("destructiveHint") is not (name in APP_DESTRUCTIVE_TOOLS):
        failures.append(f"{name} has wrong destructiveHint: {annotations}")
    if meta.get("brain/requiresUserConfirmation") is not (name in APP_MUTATING_TOOLS):
        failures.append(f"{name} has wrong confirmation metadata: {meta}")


def issue_oauth_token(
    settings,
    hostname: str,
    failures: list[str],
) -> tuple[str, str | None, str] | None:
    verifier_user = verifier_oauth_user(settings, failures)
    if verifier_user is None:
        return None
    user_id, password = verifier_user
    redirect_uri = f"https://{hostname}/app/oauth/callback"
    scope = " ".join(settings.oauth_scopes)
    register_payload = {
        "client_name": "Brain Production Verifier",
        "redirect_uris": [redirect_uri],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "scope": scope,
    }
    registration = post_json(
        f"{settings.brain_public_base_url.rstrip('/')}/register",
        register_payload,
        "OAuth dynamic client registration",
        failures,
    )
    if not registration:
        return None
    client_id = registration.get("client_id")
    if not isinstance(client_id, str):
        failures.append(f"OAuth registration did not return a client_id: {registration}")
        return None

    code_verifier = secrets.token_urlsafe(48)
    code_challenge = pkce_s256(code_verifier)
    auth_url = f"{settings.brain_public_base_url.rstrip('/')}/authorize?{urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': 'brain-production-verifier',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    })}"
    status, _headers, body, _final_url = request_url(auth_url, method="GET")
    if status != 200:
        failures.append(f"OAuth authorize form returned HTTP {status}: {body[:300]}")
        return None
    request_id_match = re.search(r'name="request_id"\s+value="([^"]+)"', body)
    if not request_id_match:
        failures.append("OAuth authorize form did not include request_id")
        return None

    status, headers, body, _final_url = request_url(
        f"{settings.brain_public_base_url.rstrip('/')}/authorize",
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=urllib.parse.urlencode(
            {"request_id": request_id_match.group(1), "user_id": user_id, "password": password}
        ).encode("utf-8"),
        follow_redirects=False,
    )
    if status not in {302, 303}:
        failures.append(f"OAuth authorize completion returned HTTP {status}: {body[:300]}")
        return None
    location = headers.get("location", "")
    code = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query).get("code", [None])[0]
    if not code:
        failures.append(f"OAuth authorize completion did not return a code: {location}")
        return None

    token = post_form(
        f"{settings.brain_public_base_url.rstrip('/')}/token",
        {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
        "OAuth token exchange",
        failures,
    )
    if not token:
        return None
    access_token = token.get("access_token")
    if not isinstance(access_token, str):
        failures.append(f"OAuth token exchange did not return an access token: {token}")
        return None
    refresh_token = token.get("refresh_token")
    return access_token, refresh_token if isinstance(refresh_token, str) else None, client_id


def verifier_oauth_user(settings, failures: list[str]) -> tuple[str, str] | None:
    password_path = settings.auth_password_path
    if not password_path.exists():
        failures.append(f"Brain auth password file does not exist: {password_path}")
        return None
    fallback_password = password_path.read_text(encoding="utf-8").strip()
    users_file = getattr(settings, "brain_auth_users_file", None)
    if not users_file:
        return settings.brain_user_id, fallback_password

    path = Path(users_file).expanduser()
    if not path.exists():
        failures.append(f"Brain auth users file does not exist: {path}")
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.values() if isinstance(payload, dict) else payload
    usable = [
        record
        for record in records
        if isinstance(record, dict) and record.get("id") and record.get("password")
    ]
    regular_users = [record for record in usable if not parse_bool(record.get("superuser"))]
    selected = (regular_users or usable)[0] if usable else None
    if selected is None:
        failures.append(f"Brain auth users file contains no usable verifier user: {path}")
        return None
    return str(selected["id"]), str(selected["password"])


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def revoke_oauth_token(
    settings,
    client_id: str,
    token: str,
    label: str,
    failures: list[str],
) -> None:
    status, _headers, body, _final_url = request_url(
        f"{settings.brain_public_base_url.rstrip('/')}/revoke",
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=urllib.parse.urlencode({"client_id": client_id, "token": token}).encode("utf-8"),
    )
    if status != 200:
        failures.append(f"OAuth revoke failed for {label}: HTTP {status} {body[:300]}")


def pkce_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def rpc_call(url: str, token: str, payload: dict, label: str, failures: list[str]) -> dict | None:
    status, _headers, body, _final_url = request_url(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        body=json.dumps(payload).encode("utf-8"),
    )
    if status != 200:
        failures.append(f"{label} returned HTTP {status}: {body[:300]}")
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        failures.append(f"{label} did not return JSON: {body[:300]}")
        return None


def post_json(url: str, payload: dict, label: str, failures: list[str]) -> dict | None:
    status, _headers, body, _final_url = request_url(
        url,
        method="POST",
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload).encode("utf-8"),
    )
    return parse_expected_json(status, body, label, failures, expected_statuses={200, 201})


def post_form(url: str, payload: dict[str, str], label: str, failures: list[str]) -> dict | None:
    status, _headers, body, _final_url = request_url(
        url,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=urllib.parse.urlencode(payload).encode("utf-8"),
    )
    return parse_expected_json(status, body, label, failures, expected_statuses={200})


def parse_expected_json(
    status: int | None,
    body: str,
    label: str,
    failures: list[str],
    *,
    expected_statuses: set[int],
) -> dict | None:
    if status not in expected_statuses:
        failures.append(f"{label} returned HTTP {status}: {body[:300]}")
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        failures.append(f"{label} did not return JSON: {body[:300]}")
        return None
    return payload


def fetch_json(url: str, label: str, failures: list[str]) -> dict | None:
    status, _headers, body = fetch(url)
    if status is None:
        failures.append(f"{label} failed: {body}")
        return None
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        failures.append(f"{label} did not return JSON: {body[:300]}")
        return None
    if "Brain" not in body and "brain" not in body:
        failures.append(f"{label} does not identify Brain: {payload}")
        return None
    console.print(f"[green][OK][/green] {label}: {url}")
    return payload


def fetch(url: str) -> tuple[int | None, dict[str, str], str]:
    status, headers, body, _final_url = request_url(url, method="GET")
    return status, headers, body


def request_url(
    url: str,
    *,
    method: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    follow_redirects: bool = True,
) -> tuple[int | None, dict[str, str], str, str]:
    request_headers = {"User-Agent": "brain-mcp-verifier/0.1"}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, headers=request_headers, data=body, method=method)
    opener = urllib.request.build_opener()
    if not follow_redirects:
        opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        with opener.open(request, timeout=8) as response:
            return (
                response.status,
                {k.lower(): v for k, v in response.headers.items()},
                response.read().decode("utf-8", errors="replace"),
                response.geturl(),
            )
    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            {k.lower(): v for k, v in exc.headers.items()},
            exc.read().decode("utf-8", errors="replace"),
            exc.geturl(),
        )
    except Exception as exc:
        return None, {}, str(exc), url


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_cloudflared(failures: list[str]) -> None:
    if not command_exists("launchctl"):
        failures.append("launchctl is not available for cloudflared check")
        return
    result = subprocess.run(
        ["launchctl", "print", f"gui/{uid()}/com.cloudflare.cloudflared"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append("cloudflared launchd service is not loaded")
        return
    if "pid =" not in result.stdout:
        failures.append("cloudflared launchd service has no running pid")
        return
    console.print("[green][OK][/green] cloudflared launchd service running")


if __name__ == "__main__":
    raise SystemExit(main())
