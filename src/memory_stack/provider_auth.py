from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import fcntl
import httpx

from memory_stack.cfg import Settings


OPENAI_CODEX_PROVIDER = "openai-codex"
OPENAI_CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
OPENAI_CODEX_SCOPE = "openid profile email offline_access"
OPENAI_CODEX_AUTHORIZE_URL = "https://auth.openai.com/oauth/authorize"
OPENAI_CODEX_TOKEN_URL = "https://auth.openai.com/oauth/token"
OPENAI_CODEX_REDIRECT_URI = "http://127.0.0.1:1455/auth/callback"
TOKEN_SAFETY_WINDOW_MS = 5 * 60 * 1000


class ProviderAuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAICodexCredential:
    access: str
    refresh: str
    expires: int
    account_id: str | None = None
    id_token: str | None = None
    email: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "OpenAICodexCredential":
        access = string_value(payload.get("access"))
        refresh = string_value(payload.get("refresh"))
        expires = int_value(payload.get("expires"))
        if not access or not refresh or not expires:
            raise ProviderAuthError("OpenAI Codex OAuth profile is incomplete.")
        return cls(
            access=access,
            refresh=refresh,
            expires=expires,
            account_id=string_value(payload.get("account_id")),
            id_token=string_value(payload.get("id_token")),
            email=string_value(payload.get("email")),
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "oauth",
            "access": self.access,
            "refresh": self.refresh,
            "expires": self.expires,
        }
        if self.account_id:
            payload["account_id"] = self.account_id
        if self.id_token:
            payload["id_token"] = self.id_token
        if self.email:
            payload["email"] = self.email
        return payload

    def usable(self, now_ms: int | None = None) -> bool:
        now = now_ms or int(time.time() * 1000)
        return bool(self.access and self.refresh and self.expires > now + TOKEN_SAFETY_WINDOW_MS)


@dataclass(frozen=True)
class PKCEPair:
    verifier: str
    challenge: str


def generate_pkce_pair() -> PKCEPair:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode("ascii").rstrip("=")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return PKCEPair(verifier=verifier, challenge=challenge)


def build_openai_codex_authorize_url(*, state: str, challenge: str) -> str:
    params = {
        "response_type": "code",
        "client_id": OPENAI_CODEX_CLIENT_ID,
        "redirect_uri": OPENAI_CODEX_REDIRECT_URI,
        "scope": OPENAI_CODEX_SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "originator": "brain",
        "state": state,
    }
    return f"{OPENAI_CODEX_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def parse_authorization_response(value: str, *, expected_state: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ProviderAuthError("Missing authorization code.")
    if "://" not in candidate:
        return candidate
    parsed = urllib.parse.urlparse(candidate)
    values = urllib.parse.parse_qs(parsed.query)
    state = first(values.get("state"))
    if state and state != expected_state:
        raise ProviderAuthError("OAuth state mismatch.")
    code = first(values.get("code"))
    if not code:
        raise ProviderAuthError("Redirect URL did not include an authorization code.")
    return code


def load_auth_store(settings: Settings) -> dict[str, Any]:
    path = auth_profiles_path(settings)
    if not path.exists():
        return empty_auth_store()
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise ProviderAuthError(f"Invalid provider auth store JSON: {path}") from exc
    if not isinstance(payload, dict):
        return empty_auth_store()
    store = empty_auth_store()
    providers = payload.get("providers")
    if isinstance(providers, dict):
        store["providers"] = providers
    return store


def save_auth_store(settings: Settings, store: dict[str, Any]) -> None:
    path = auth_profiles_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    with temp.open("w", encoding="utf-8") as file:
        json.dump(store, file, indent=2, sort_keys=True)
        file.write("\n")
    temp.chmod(0o600)
    temp.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def get_openai_codex_profile(
    settings: Settings,
    profile: str | None = None,
) -> OpenAICodexCredential | None:
    profile_name = profile or settings.openai_codex_auth_profile
    store = load_auth_store(settings)
    payload = (
        store.get("providers", {})
        .get(OPENAI_CODEX_PROVIDER, {})
        .get("profiles", {})
        .get(profile_name)
    )
    if not isinstance(payload, dict):
        return None
    return OpenAICodexCredential.from_payload(payload)


def upsert_openai_codex_profile(
    settings: Settings,
    credential: OpenAICodexCredential,
    profile: str | None = None,
) -> None:
    profile_name = profile or settings.openai_codex_auth_profile
    with provider_auth_store_lock(settings):
        store = load_auth_store(settings)
        provider_store = store.setdefault("providers", {}).setdefault(
            OPENAI_CODEX_PROVIDER,
            {"profiles": {}},
        )
        provider_store.setdefault("profiles", {})[profile_name] = credential.to_payload()
        save_auth_store(settings, store)


def list_openai_codex_profiles(settings: Settings) -> list[dict[str, Any]]:
    store = load_auth_store(settings)
    profiles = (
        store.get("providers", {})
        .get(OPENAI_CODEX_PROVIDER, {})
        .get("profiles", {})
    )
    if not isinstance(profiles, dict):
        return []
    rows: list[dict[str, Any]] = []
    now_ms = int(time.time() * 1000)
    for name, payload in sorted(profiles.items()):
        if not isinstance(payload, dict):
            continue
        try:
            credential = OpenAICodexCredential.from_payload(payload)
        except ProviderAuthError:
            rows.append({"profile": name, "status": "invalid"})
            continue
        rows.append(
            {
                "profile": name,
                "status": "usable" if credential.usable(now_ms) else "expired",
                "expires": credential.expires,
                "account_id": credential.account_id,
                "email": credential.email,
            }
        )
    return rows


def resolve_openai_text_bearer(settings: Settings) -> str:
    if settings.openai_auth_mode == "api_key":
        key = settings.configured_provider_api_key("openai")
        if not key:
            raise ProviderAuthError("OPENAI_AUTH_MODE=api_key but OPENAI_API_KEY is missing.")
        return key
    sink_token = get_token_sink_client_token(settings)
    if sink_token:
        return sink_token
    return resolve_openai_codex_access_token(settings)


def openai_responses_base_url(settings: Settings) -> str:
    return settings.openai_codex_base_url.rstrip("/")


def openai_embeddings_base_url(settings: Settings) -> str:
    if openai_uses_token_sink(settings):
        return openai_responses_base_url(settings)
    return "https://api.openai.com/v1"


def openai_uses_token_sink(settings: Settings) -> bool:
    return bool(string_value(getattr(settings, "openai_token_sink_client_token_file", None)))


def get_token_sink_client_token(settings: Settings) -> str | None:
    path_value = string_value(getattr(settings, "openai_token_sink_client_token_file", None))
    if not path_value:
        return None
    path = Path(path_value).expanduser()
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ProviderAuthError(f"OpenAI token sink client token is unreadable: {path}") from exc
    if not token:
        raise ProviderAuthError(f"OpenAI token sink client token is empty: {path}")
    return token


def resolve_openai_codex_access_token(settings: Settings) -> str:
    cli_access = get_codex_cli_access_token()
    if cli_access:
        return cli_access

    credential = get_openai_codex_profile(settings)
    if credential:
        if credential.usable():
            return credential.access
        refreshed = refresh_openai_codex_profile(settings)
        return refreshed.access

    refresh_openai_codex_profile(settings)
    raise ProviderAuthError("OpenAI OAuth credentials are missing. Run `brain models auth login --provider openai-codex`.")


def refresh_openai_codex_profile(settings: Settings) -> OpenAICodexCredential:
    profile = settings.openai_codex_auth_profile
    with openai_codex_refresh_lock(settings, profile):
        current = get_openai_codex_profile(settings, profile)
        if current and current.usable():
            return current
        if not current:
            raise ProviderAuthError(
                "OpenAI OAuth credentials are missing. Run `brain models auth login --provider openai-codex`."
            )
        refreshed = exchange_refresh_token(current.refresh)
        upsert_openai_codex_profile(settings, refreshed, profile)
        return refreshed


def get_codex_cli_access_token(now_ms: int | None = None) -> str | None:
    path = codex_cli_auth_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    tokens = payload.get("tokens")
    if not isinstance(tokens, dict):
        return None
    access = string_value(tokens.get("access_token"))
    if not access:
        return None
    exp = int_value(jwt_claim(access, "exp"))
    if exp is None:
        return None
    now = now_ms or int(time.time() * 1000)
    if exp * 1000 <= now + TOKEN_SAFETY_WINDOW_MS:
        return None
    return access


def codex_cli_auth_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "auth.json"
    return Path.home() / ".codex" / "auth.json"


def login_openai_codex(
    settings: Settings,
    *,
    manual: bool = False,
    timeout_seconds: int = 120,
) -> OpenAICodexCredential:
    pkce = generate_pkce_pair()
    state = secrets.token_urlsafe(32)
    auth_url = build_openai_codex_authorize_url(state=state, challenge=pkce.challenge)
    code: str | None = None

    if not manual:
        code = try_local_browser_callback(auth_url, expected_state=state, timeout_seconds=timeout_seconds)

    if not code:
        print(f"Open this URL to sign in:\n{auth_url}\n")
        pasted = input("Paste the authorization code or full redirect URL: ")
        code = parse_authorization_response(pasted, expected_state=state)

    credential = exchange_authorization_code(code, pkce.verifier)
    upsert_openai_codex_profile(settings, credential)
    return credential


def exchange_authorization_code(code: str, verifier: str) -> OpenAICodexCredential:
    response = httpx.post(
        OPENAI_CODEX_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": OPENAI_CODEX_CLIENT_ID,
            "code": code,
            "redirect_uri": OPENAI_CODEX_REDIRECT_URI,
            "code_verifier": verifier,
        },
        timeout=60,
    )
    return credential_from_token_response(response)


def exchange_refresh_token(refresh_token: str) -> OpenAICodexCredential:
    response = httpx.post(
        OPENAI_CODEX_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": OPENAI_CODEX_CLIENT_ID,
            "refresh_token": refresh_token,
        },
        timeout=60,
    )
    return credential_from_token_response(response)


def credential_from_token_response(response: httpx.Response) -> OpenAICodexCredential:
    if response.status_code >= 400:
        raise ProviderAuthError(redact_token_error(f"OpenAI OAuth token exchange failed: HTTP {response.status_code}: {response.text}"))
    payload = response.json()
    if not isinstance(payload, dict):
        raise ProviderAuthError("OpenAI OAuth token exchange returned invalid JSON.")
    access = string_value(payload.get("access_token"))
    refresh = string_value(payload.get("refresh_token"))
    if not access or not refresh:
        raise ProviderAuthError("OpenAI OAuth token exchange did not return access and refresh tokens.")
    expires_in = int_value(payload.get("expires_in")) or 3600
    id_token = string_value(payload.get("id_token"))
    account_id = string_value(payload.get("account_id")) or jwt_claim(access, "https://api.openai.com/auth", "account_id")
    email = jwt_claim(id_token or access, "email")
    return OpenAICodexCredential(
        access=access,
        refresh=refresh,
        expires=int(time.time() * 1000) + (expires_in * 1000),
        account_id=account_id,
        id_token=id_token,
        email=email,
    )


def try_local_browser_callback(
    auth_url: str,
    *,
    expected_state: str,
    timeout_seconds: int,
) -> str | None:
    event = threading.Event()
    result: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                result["code"] = parse_authorization_response(
                    f"http://127.0.0.1:1455{self.path}",
                    expected_state=expected_state,
                )
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authentication successful. Return to your terminal.")
            except Exception as exc:
                result["error"] = str(exc)
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authentication failed. Return to your terminal.")
            finally:
                event.set()

        def log_message(self, *_args: Any) -> None:
            return

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 1455), Handler)
    except OSError:
        return None

    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    webbrowser.open(auth_url)
    event.wait(timeout_seconds)
    server.server_close()
    if result.get("error"):
        raise ProviderAuthError(result["error"])
    return result.get("code")


@contextmanager
def provider_auth_store_lock(settings: Settings) -> Iterator[None]:
    with file_lock(auth_profiles_path(settings).with_suffix(".lock")):
        yield


@contextmanager
def openai_codex_refresh_lock(settings: Settings, profile: str) -> Iterator[None]:
    lock_id = hashlib.sha256(f"{OPENAI_CODEX_PROVIDER}\0{profile}".encode("utf-8")).hexdigest()
    lock_path = Path(settings.brain_provider_auth_state_dir).expanduser() / "locks" / f"{lock_id}.lock"
    with file_lock(lock_path):
        yield


@contextmanager
def file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as file:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)


def auth_profiles_path(settings: Settings) -> Path:
    return Path(settings.brain_provider_auth_profiles_path).expanduser()


def empty_auth_store() -> dict[str, Any]:
    return {"version": 1, "providers": {}}


def jwt_claim(token: str | None, *path: str) -> Any:
    if not token:
        return None
    parts = token.split(".")
    if len(parts) < 2:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(pad_base64(parts[1])).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def pad_base64(value: str) -> str:
    return value + ("=" * (-len(value) % 4))


def first(values: list[str] | None) -> str | None:
    return values[0] if values else None


def string_value(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def int_value(value: Any) -> int | None:
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, float) and value > 0:
        return int(value)
    return None


def redact_token_error(value: str) -> str:
    # Token-looking JWTs and opaque OAuth secrets should never be echoed back.
    words = value.split()
    return " ".join("[redacted]" if looks_secret(word) else word for word in words)


def looks_secret(value: str) -> bool:
    return len(value) > 32 and (
        value.count(".") >= 2
        or value.startswith(("eyJ", "sk-", "sess-", "rt_"))
        or all(ch.isalnum() or ch in "-_." for ch in value)
    )
