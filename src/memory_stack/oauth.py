from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import tempfile
import time
from html import escape
from pathlib import Path
from threading import RLock
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from memory_stack.cfg import Settings


AUTH_REQUEST_SECONDS = 10 * 60
AUTH_CODE_SECONDS = 5 * 60


class BrainOAuthProvider:
    def __init__(self, settings: Settings):
        self.service_name = settings.brain_service_name
        self.issuer_url = settings.brain_public_base_url.rstrip("/")
        self.resource_url = settings.public_mcp_url
        self.scopes = settings.brain_auth_scope_list
        self.require_pkce = settings.brain_auth_require_pkce
        self.password = ensure_auth_password(settings)
        self.state_path = Path(settings.brain_auth_state_path).expanduser()
        self.access_token_seconds = settings.brain_auth_access_token_seconds
        self.refresh_token_seconds = settings.brain_auth_refresh_token_seconds
        self._lock = RLock()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._save_state(self._load_state())

    def protected_resource_metadata(self) -> dict[str, Any]:
        return {
            "resource": self.resource_url,
            "resource_name": self.service_name,
            "authorization_servers": [self.issuer_url],
            "scopes_supported": self.scopes,
            "bearer_methods_supported": ["header"],
        }

    def authorization_server_metadata(self) -> dict[str, Any]:
        return {
            "issuer": self.issuer_url,
            "service": self.service_name,
            "authorization_endpoint": f"{self.issuer_url}/authorize",
            "token_endpoint": f"{self.issuer_url}/token",
            "registration_endpoint": f"{self.issuer_url}/register",
            "scopes_supported": self.scopes,
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
                "none",
            ],
            "code_challenge_methods_supported": ["S256", "plain"],
        }

    async def register_client(self, request: Request) -> Response:
        try:
            payload = await request.json()
        except json.JSONDecodeError as exc:
            raise oauth_http_error("invalid_client_metadata", "Invalid JSON body.") from exc

        redirect_uris = payload.get("redirect_uris")
        if not isinstance(redirect_uris, list) or not all(
            isinstance(uri, str) and uri for uri in redirect_uris
        ):
            raise oauth_http_error(
                "invalid_redirect_uri", "redirect_uris must be a non-empty string list."
            )

        auth_method = str(payload.get("token_endpoint_auth_method") or "client_secret_post")
        if auth_method not in {"client_secret_post", "client_secret_basic", "none"}:
            raise oauth_http_error(
                "invalid_client_metadata",
                "token_endpoint_auth_method must be client_secret_post, "
                "client_secret_basic, or none.",
            )

        requested_scopes = parse_scope(payload.get("scope"), self.scopes)
        validate_scopes(requested_scopes, self.scopes)

        client_id = secrets.token_urlsafe(24)
        client_secret = None if auth_method == "none" else secrets.token_urlsafe(32)
        now = int(time.time())
        client = {
            "client_id": client_id,
            "client_id_issued_at": now,
            "client_name": str(payload.get("client_name") or "MCP client"),
            "client_secret": client_secret,
            "client_secret_expires_at": 0 if client_secret else None,
            "grant_types": payload.get(
                "grant_types", ["authorization_code", "refresh_token"]
            ),
            "redirect_uris": redirect_uris,
            "response_types": payload.get("response_types", ["code"]),
            "scope": " ".join(requested_scopes),
            "token_endpoint_auth_method": auth_method,
        }
        with self._lock:
            state = self._load_state()
            state["clients"][client_id] = without_none(client)
            self._save_state(state)

        return JSONResponse(without_none(client), status_code=201)

    async def authorize(self, request: Request) -> Response:
        if request.method == "POST":
            return await self._complete_authorization(request)

        params = request.query_params
        if params.get("response_type") != "code":
            raise oauth_http_error("unsupported_response_type", "Only response_type=code is supported.")

        client_id = params.get("client_id", "")
        client = self._client(client_id)
        redirect_uri = select_redirect_uri(client, params.get("redirect_uri"))
        requested_scopes = parse_scope(params.get("scope"), self.scopes)
        validate_scopes(requested_scopes, self.scopes)

        resource = params.get("resource")
        if resource and resource != self.resource_url:
            raise oauth_http_error("invalid_target", f"Unsupported resource: {resource}")

        code_challenge = params.get("code_challenge")
        code_challenge_method = params.get("code_challenge_method") or (
            "plain" if code_challenge else None
        )
        if self.require_pkce and not code_challenge:
            raise oauth_http_error("invalid_request", "code_challenge is required.")
        if code_challenge_method and code_challenge_method not in {"S256", "plain"}:
            raise oauth_http_error(
                "invalid_request", "code_challenge_method must be S256 or plain."
            )

        request_id = secrets.token_urlsafe(32)
        pending = {
            "client_id": client_id,
            "state": params.get("state"),
            "scopes": requested_scopes,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "redirect_uri": redirect_uri,
            "resource": resource or self.resource_url,
            "expires_at": int(time.time()) + AUTH_REQUEST_SECONDS,
        }
        with self._lock:
            state = self._load_state()
            state["pending_authorizations"][request_id] = without_none(pending)
            self._save_state(state)

        return auth_form(
            service_name=self.service_name,
            request_id=request_id,
            action="/authorize",
        )

    async def _complete_authorization(self, request: Request) -> Response:
        return await complete_authorization(self, request)

    async def token(self, request: Request) -> Response:
        form = await read_form(request)
        grant_type = form.get("grant_type", "")
        client = self._authenticate_client(request, form)

        if grant_type == "authorization_code":
            token = self._exchange_authorization_code(client, form)
        elif grant_type == "refresh_token":
            token = self._exchange_refresh_token(client, form)
        else:
            raise oauth_http_error("unsupported_grant_type", f"Unsupported grant_type: {grant_type}")

        return JSONResponse(token, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})

    async def revoke(self, request: Request) -> Response:
        form = await read_form(request)
        self._authenticate_client(request, form)
        token = form.get("token", "")
        with self._lock:
            state = self._load_state()
            state["access_tokens"].pop(token, None)
            state["refresh_tokens"].pop(token, None)
            self._save_state(state)
        return Response(status_code=200)

    def validate_access_token(self, token: str, required_scopes: list[str]) -> bool:
        return self.access_token_record(token, required_scopes) is not None

    def access_token_record(
        self,
        token: str,
        required_scopes: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if not token:
            return None
        with self._lock:
            state = self._load_state()
            stored = state["access_tokens"].get(token)
            if stored and is_expired(stored):
                state["access_tokens"].pop(token, None)
                self._save_state(state)
                stored = None
        if not stored:
            return None
        token_scopes = stored.get("scopes") or []
        if any(scope not in token_scopes for scope in required_scopes or []):
            return None
        token_resource = stored.get("resource")
        if token_resource not in {None, self.resource_url}:
            return None
        return {
            "client_id": stored.get("client_id"),
            "scopes": token_scopes,
            "resource": token_resource,
        }

    def _client(self, client_id: str) -> dict[str, Any]:
        with self._lock:
            client = self._load_state()["clients"].get(client_id)
        if not client:
            raise oauth_http_error("invalid_client", "Unknown client_id.", status_code=401)
        return client

    def _authenticate_client(self, request: Request, form: dict[str, str]) -> dict[str, Any]:
        basic_client_id, basic_secret = parse_basic_auth(request.headers.get("authorization"))
        client_id = basic_client_id or form.get("client_id", "")
        client = self._client(client_id)
        auth_method = client.get("token_endpoint_auth_method", "client_secret_post")
        expected_secret = client.get("client_secret")

        if auth_method == "none":
            return client

        provided_secret = basic_secret if basic_client_id else form.get("client_secret", "")
        if not expected_secret or not hmac.compare_digest(provided_secret, expected_secret):
            raise oauth_http_error("invalid_client", "Client authentication failed.", status_code=401)
        return client

    def _exchange_authorization_code(
        self, client: dict[str, Any], form: dict[str, str]
    ) -> dict[str, Any]:
        code_value = form.get("code", "")
        now = int(time.time())
        with self._lock:
            state = self._load_state()
            code = state["authorization_codes"].pop(code_value, None)
            if not code or is_expired(code):
                self._save_state(state)
                raise oauth_http_error("invalid_grant", "Invalid or expired authorization code.")

            if code.get("client_id") != client["client_id"]:
                self._save_state(state)
                raise oauth_http_error("invalid_grant", "Authorization code client mismatch.")

            redirect_uri = form.get("redirect_uri")
            if redirect_uri and redirect_uri != code.get("redirect_uri"):
                self._save_state(state)
                raise oauth_http_error("invalid_grant", "redirect_uri does not match authorization.")

            if (code.get("code_challenge") or self.require_pkce) and not valid_pkce(
                verifier=form.get("code_verifier", ""),
                challenge=code.get("code_challenge", ""),
                method=code.get("code_challenge_method") or "plain",
            ):
                self._save_state(state)
                raise oauth_http_error("invalid_grant", "PKCE verification failed.")

            token = self._issue_tokens(
                state,
                client_id=client["client_id"],
                scopes=code["scopes"],
                resource=code.get("resource") or self.resource_url,
                now=now,
            )
            self._save_state(state)
        return token

    def _exchange_refresh_token(
        self, client: dict[str, Any], form: dict[str, str]
    ) -> dict[str, Any]:
        refresh_value = form.get("refresh_token", "")
        requested_scopes = parse_scope(form.get("scope"), [])
        now = int(time.time())
        with self._lock:
            state = self._load_state()
            refresh = state["refresh_tokens"].pop(refresh_value, None)
            if not refresh or is_expired(refresh):
                self._save_state(state)
                raise oauth_http_error("invalid_grant", "Invalid or expired refresh token.")

            if refresh.get("client_id") != client["client_id"]:
                self._save_state(state)
                raise oauth_http_error("invalid_grant", "Refresh token client mismatch.")

            scopes = requested_scopes or refresh.get("scopes", [])
            if any(scope not in refresh.get("scopes", []) for scope in scopes):
                self._save_state(state)
                raise oauth_http_error("invalid_scope", "Requested scope was not granted.")

            token = self._issue_tokens(
                state,
                client_id=client["client_id"],
                scopes=scopes,
                resource=refresh.get("resource") or self.resource_url,
                now=now,
            )
            self._save_state(state)
        return token

    def _issue_tokens(
        self,
        state: dict[str, Any],
        *,
        client_id: str,
        scopes: list[str],
        resource: str,
        now: int,
    ) -> dict[str, Any]:
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        state["access_tokens"][access_token] = {
            "client_id": client_id,
            "scopes": scopes,
            "resource": resource,
            "expires_at": now + self.access_token_seconds,
        }
        state["refresh_tokens"][refresh_token] = {
            "client_id": client_id,
            "scopes": scopes,
            "resource": resource,
            "expires_at": now + self.refresh_token_seconds,
        }
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_seconds,
            "refresh_token": refresh_token,
            "scope": " ".join(scopes),
        }

    def _load_state(self) -> dict[str, dict[str, Any]]:
        if not self.state_path.exists():
            return empty_state()
        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError:
            payload = empty_state()

        clean = empty_state()
        for key in clean:
            if isinstance(payload.get(key), dict):
                clean[key] = payload[key]
        return clean

    def _save_state(self, state: dict[str, dict[str, Any]]) -> None:
        prune_expired(state)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.state_path.parent,
            delete=False,
        ) as file:
            json.dump(state, file, indent=2, sort_keys=True)
            file.write("\n")
            temp_path = Path(file.name)
        temp_path.replace(self.state_path)
        try:
            self.state_path.chmod(0o600)
        except OSError:
            pass


async def read_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8", errors="replace")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def ensure_auth_password(settings: Settings) -> str:
    if settings.brain_auth_password:
        return settings.brain_auth_password

    path = Path(settings.brain_auth_password_file).expanduser()
    if path.exists():
        return path.read_text(encoding="utf-8").strip()

    path.parent.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(24)
    path.write_text(password + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return password


def auth_form(
    *,
    service_name: str,
    request_id: str,
    action: str,
    error: str | None = None,
) -> HTMLResponse:
    safe_service = escape(service_name)
    safe_request_id = escape(request_id, quote=True)
    safe_action = escape(action, quote=True)
    error_html = f'<p class="error">{escape(error)}</p>' if error else ""
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Authorize {safe_service}</title>
    <style>
      body {{
        background: #101114;
        color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
      }}
      main {{
        width: min(420px, calc(100vw - 40px));
      }}
      h1 {{
        font-size: 24px;
        margin: 0 0 8px;
      }}
      p {{
        color: #c9ccd2;
        line-height: 1.45;
      }}
      label {{
        display: block;
        font-size: 14px;
        margin: 24px 0 8px;
      }}
      input, button {{
        box-sizing: border-box;
        width: 100%;
        border-radius: 8px;
        border: 1px solid #3a3d45;
        font: inherit;
        padding: 12px 14px;
      }}
      input {{
        background: #191b20;
        color: #f3f4f6;
      }}
      button {{
        margin-top: 14px;
        background: #f3f4f6;
        color: #101114;
        cursor: pointer;
      }}
      .error {{
        color: #ffb4ab;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>Authorize {safe_service}</h1>
      <p>Enter the {safe_service} auth password to connect this MCP client.</p>
      {error_html}
      <form method="post" action="{safe_action}">
        <input type="hidden" name="request_id" value="{safe_request_id}">
        <label for="password">Password</label>
        <input id="password" name="password" type="password" autocomplete="current-password" autofocus>
        <button type="submit">Authorize</button>
      </form>
    </main>
  </body>
</html>"""
    return HTMLResponse(html, status_code=401 if error else 200)


async def completion_form(request: Request) -> dict[str, str]:
    return await read_form(request)


def parse_bearer(header_value: str | None) -> str | None:
    if not header_value:
        return None
    scheme, _, token = header_value.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def parse_basic_auth(header_value: str | None) -> tuple[str | None, str | None]:
    if not header_value:
        return None, None
    scheme, _, encoded = header_value.partition(" ")
    if scheme.lower() != "basic" or not encoded:
        return None, None
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return None, None
    client_id, separator, client_secret = decoded.partition(":")
    if not separator:
        return None, None
    return client_id, client_secret


def select_redirect_uri(client: dict[str, Any], requested: str | None) -> str:
    redirect_uris = client.get("redirect_uris", [])
    if requested:
        if requested not in redirect_uris:
            raise oauth_http_error("invalid_redirect_uri", "redirect_uri is not registered.")
        return requested
    if len(redirect_uris) == 1:
        return redirect_uris[0]
    raise oauth_http_error("invalid_request", "redirect_uri is required.")


def parse_scope(value: Any, default: list[str]) -> list[str]:
    if value is None or value == "":
        return list(default)
    if isinstance(value, list):
        return [str(scope) for scope in value if str(scope)]
    return [scope for scope in str(value).split() if scope]


def validate_scopes(requested: list[str], allowed: list[str]) -> None:
    if any(scope not in allowed for scope in requested):
        raise oauth_http_error("invalid_scope", "Requested scope is not supported.")


def valid_pkce(*, verifier: str, challenge: str, method: str) -> bool:
    if not verifier:
        return False
    if method == "plain":
        return hmac.compare_digest(verifier, challenge)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    derived = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(derived, challenge)


def oauth_http_error(
    error: str, description: str, *, status_code: int = 400
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": error, "error_description": description},
    )


def empty_state() -> dict[str, dict[str, Any]]:
    return {
        "clients": {},
        "pending_authorizations": {},
        "authorization_codes": {},
        "access_tokens": {},
        "refresh_tokens": {},
    }


def prune_expired(state: dict[str, dict[str, Any]]) -> None:
    for bucket_name in [
        "pending_authorizations",
        "authorization_codes",
        "access_tokens",
        "refresh_tokens",
    ]:
        bucket = state[bucket_name]
        for key, value in list(bucket.items()):
            if is_expired(value):
                bucket.pop(key, None)


def is_expired(value: dict[str, Any]) -> bool:
    expires_at = value.get("expires_at")
    return expires_at is not None and float(expires_at) < time.time()


def without_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def add_query_params(url: str, params: dict[str, str]) -> str:
    parts = urlsplit(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    for key, value in params.items():
        query[key] = [value]
    encoded_query = urlencode(
        [(key, item) for key, values in query.items() for item in values]
    )
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            encoded_query,
            parts.fragment,
        )
    )


async def complete_authorization(provider: BrainOAuthProvider, request: Request) -> Response:
    form = await completion_form(request)
    request_id = form.get("request_id", "")
    password = form.get("password", "")
    if not hmac.compare_digest(password, provider.password):
        return auth_form(
            service_name=provider.service_name,
            request_id=request_id,
            action="/authorize",
            error="Invalid or expired authorization.",
        )

    with provider._lock:
        state = provider._load_state()
        pending = state["pending_authorizations"].pop(request_id, None)
        if not pending or is_expired(pending):
            provider._save_state(state)
            return auth_form(
                service_name=provider.service_name,
                request_id=request_id,
                action="/authorize",
                error="Invalid or expired authorization.",
            )

        code_value = secrets.token_urlsafe(32)
        code = {
            "code": code_value,
            "client_id": pending["client_id"],
            "scopes": pending["scopes"],
            "code_challenge": pending.get("code_challenge"),
            "code_challenge_method": pending.get("code_challenge_method"),
            "redirect_uri": pending["redirect_uri"],
            "resource": pending.get("resource") or provider.resource_url,
            "expires_at": int(time.time()) + AUTH_CODE_SECONDS,
        }
        state["authorization_codes"][code_value] = without_none(code)
        provider._save_state(state)

    redirect_params = {"code": code_value}
    if pending.get("state"):
        redirect_params["state"] = pending["state"]
    return RedirectResponse(add_query_params(pending["redirect_uri"], redirect_params), status_code=302)
