from __future__ import annotations

import base64
import hashlib
import hmac
import time
from html import escape
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from memory_stack.config import load_settings
from memory_stack.oauth import ensure_auth_password, read_form

settings = load_settings()
auth_password = ensure_auth_password(settings)

app = FastAPI(title="Brain Cognee UI Proxy", version="0.1.0")

COOKIE_NAME = "brain_ui_session"
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


@app.get("/healthz")
async def healthz() -> dict[str, str | int | bool]:
    return {
        "status": "ok",
        "service": "Brain UI",
        "auth_enabled": settings.brain_auth_enabled,
        "frontend_port": settings.brain_ui_frontend_port,
        "backend_port": settings.brain_ui_backend_port,
        "public_ui_url": settings.public_ui_url,
    }


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(settings.brain_public_ui_path, status_code=302)


@app.api_route("/ui-login", methods=["GET", "POST"])
async def ui_login(request: Request) -> Response:
    next_path = safe_next_path(request.query_params.get("next"), settings.brain_public_ui_path)
    if request.method == "GET":
        return login_form(next_path=next_path)

    form = await read_form(request)
    password = str(form.get("password") or "")
    next_path = safe_next_path(str(form.get("next") or ""), settings.brain_public_ui_path)
    if not hmac.compare_digest(password, auth_password):
        return login_form(next_path=next_path, error="Invalid password.")

    response = RedirectResponse(next_path, status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        signed_session_value(),
        max_age=settings.brain_ui_session_seconds,
        httponly=True,
        secure=settings.brain_public_base_url.startswith("https://"),
        samesite="lax",
        path="/",
    )
    return response


@app.post("/ui-logout")
async def ui_logout() -> Response:
    response = RedirectResponse("/ui-login", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@app.api_route("/ui", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/ui/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_ui(request: Request, path: str = "") -> Response:
    require_session(request)
    upstream_path = "/" + path
    return await proxy_request(request, frontend_base_url(), upstream_path)


@app.api_route(
    "/ui-api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy_ui_api(path: str, request: Request) -> Response:
    require_session(request)
    return await proxy_request(request, backend_base_url(), "/" + path)


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy_frontend_root_paths(path: str, request: Request) -> Response:
    if path in {"mcp", "healthz", "authorize", "token", "register", "revoke"}:
        raise HTTPException(status_code=404, detail="Not found")
    if path.startswith(".well-known/"):
        raise HTTPException(status_code=404, detail="Not found")

    require_session(request)
    return await proxy_request(request, frontend_base_url(), "/" + path)


def require_session(request: Request) -> None:
    if valid_session(request.cookies.get(COOKIE_NAME)):
        return
    next_path = request.url.path
    if request.url.query:
        next_path += f"?{request.url.query}"
    query = urlencode({"next": next_path})
    raise HTTPException(
        status_code=303,
        headers={"Location": f"/ui-login?{query}"},
        detail="Authentication required",
    )


def signed_session_value() -> str:
    issued_at = str(int(time.time()))
    signature = session_signature(issued_at)
    payload = f"{issued_at}.{signature}"
    return base64.urlsafe_b64encode(payload.encode("ascii")).decode("ascii")


def valid_session(cookie_value: str | None) -> bool:
    if not cookie_value:
        return False
    try:
        payload = base64.urlsafe_b64decode(cookie_value.encode("ascii")).decode("ascii")
        issued_at, signature = payload.split(".", 1)
        issued_at_int = int(issued_at)
    except Exception:
        return False
    if time.time() - issued_at_int > settings.brain_ui_session_seconds:
        return False
    return hmac.compare_digest(signature, session_signature(issued_at))


def session_signature(issued_at: str) -> str:
    return hmac.new(
        auth_password.encode("utf-8"),
        f"brain-ui:{issued_at}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def login_form(*, next_path: str, error: str | None = None) -> HTMLResponse:
    safe_next = escape(next_path, quote=True)
    error_html = f'<p class="error">{escape(error)}</p>' if error else ""
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Brain UI Login</title>
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
      <h1>Brain UI</h1>
      <p>Enter the Brain auth password to open the Cognee web UI.</p>
      {error_html}
      <form method="post" action="/ui-login">
        <input type="hidden" name="next" value="{safe_next}">
        <label for="password">Password</label>
        <input id="password" name="password" type="password" autocomplete="current-password" autofocus>
        <button type="submit">Open UI</button>
      </form>
    </main>
  </body>
</html>"""
    return HTMLResponse(html, status_code=401 if error else 200)


def safe_next_path(value: str | None, default: str) -> str:
    if not value or not value.startswith("/") or value.startswith("//"):
        return default
    return value


def frontend_base_url() -> str:
    return f"http://127.0.0.1:{settings.brain_ui_frontend_port}"


def backend_base_url() -> str:
    return f"http://127.0.0.1:{settings.brain_ui_backend_port}"


async def proxy_request(request: Request, upstream_base_url: str, upstream_path: str) -> Response:
    url = f"{upstream_base_url}{upstream_path}"
    if request.url.query:
        url += f"?{request.url.query}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }
    headers["x-forwarded-host"] = request.headers.get("host", "")
    headers["x-forwarded-proto"] = (
        "https" if settings.brain_public_base_url.startswith("https") else "http"
    )

    async with httpx.AsyncClient(follow_redirects=False, timeout=60.0) as client:
        upstream = await client.request(
            request.method,
            url,
            content=await request.body(),
            headers=headers,
        )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )
