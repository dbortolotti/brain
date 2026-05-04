from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from memory_stack.config import Settings


REDACTED = "[REDACTED]"
SENSITIVE_EXACT_KEYS = {
    "api_key",
    "authorization",
    "code",
    "code_verifier",
    "cookie",
    "id_token",
    "request_id",
    "set-cookie",
}


class RequestResponseLogMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.log_path = Path(settings.brain_request_log_path).expanduser()
        self.max_body_bytes = settings.brain_request_log_max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        request_id = str(uuid.uuid4())
        request_messages, request_body, request_truncated = await drain_request(
            receive,
            self.max_body_bytes,
        )
        response_status = 500
        response_headers: list[tuple[bytes, bytes]] = []
        response_body = bytearray()
        response_truncated = False
        app_error: str | None = None

        async def replay_receive() -> Message:
            if request_messages:
                return request_messages.pop(0)
            return {"type": "http.request", "body": b"", "more_body": False}

        async def capture_send(message: Message) -> None:
            nonlocal response_status, response_headers, response_truncated
            if message["type"] == "http.response.start":
                response_status = int(message["status"])
                response_headers = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_truncated = append_limited(
                        response_body,
                        body,
                        self.max_body_bytes,
                        response_truncated,
                    )
            await send(message)

        try:
            await self.app(scope, replay_receive, capture_send)
        except Exception as exc:
            app_error = f"{exc.__class__.__name__}: {exc}"
            raise
        finally:
            record = build_log_record(
                scope=scope,
                request_id=request_id,
                started=started,
                request_body=bytes(request_body),
                request_body_truncated=request_truncated,
                response_status=response_status,
                response_headers=response_headers,
                response_body=bytes(response_body),
                response_body_truncated=response_truncated,
                app_error=app_error,
            )
            append_jsonl(self.log_path, record)


async def drain_request(receive: Receive, max_body_bytes: int) -> tuple[list[Message], bytearray, bool]:
    messages: list[Message] = []
    body = bytearray()
    truncated = False
    while True:
        message = await receive()
        messages.append(message)
        if message["type"] != "http.request":
            break
        chunk = message.get("body", b"")
        if chunk:
            truncated = append_limited(body, chunk, max_body_bytes, truncated)
        if not message.get("more_body", False):
            break
    return messages, body, truncated


def append_limited(
    target: bytearray,
    chunk: bytes,
    max_body_bytes: int,
    already_truncated: bool,
) -> bool:
    if max_body_bytes == 0:
        target.extend(chunk)
        return already_truncated

    remaining = max_body_bytes - len(target)
    if remaining <= 0:
        return True
    target.extend(chunk[:remaining])
    return already_truncated or len(chunk) > remaining


def build_log_record(
    *,
    scope: Scope,
    request_id: str,
    started: float,
    request_body: bytes,
    request_body_truncated: bool,
    response_status: int,
    response_headers: list[tuple[bytes, bytes]],
    response_body: bytes,
    response_body_truncated: bool,
    app_error: str | None,
) -> dict[str, Any]:
    request_headers = decode_headers(scope.get("headers", []))
    response_header_dict = decode_headers(response_headers)
    method = str(scope.get("method", ""))
    path = str(scope.get("path", ""))
    query_string = bytes(scope.get("query_string", b"")).decode("utf-8", errors="replace")
    client = scope.get("client")

    content_type = request_headers.get("content-type", "")
    response_content_type = response_header_dict.get("content-type", "")
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": request_id,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "client": format_client(client),
        "request": {
            "method": method,
            "path": path,
            "query": redact_query_string(query_string),
            "headers": redact_mapping(request_headers),
            "body": decode_body(request_body, content_type),
            "body_truncated": request_body_truncated,
        },
        "response": {
            "status": response_status,
            "headers": redact_mapping(response_header_dict),
            "body": decode_body(response_body, response_content_type),
            "body_truncated": response_body_truncated,
        },
        "error": app_error,
    }


def decode_headers(raw_headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1", errors="replace")
        for key, value in raw_headers
    }


def format_client(client: Any) -> dict[str, Any] | None:
    if not client:
        return None
    host, port = client
    return {"host": host, "port": port}


def decode_body(body: bytes, content_type: str) -> Any:
    if not body:
        return None
    text = body.decode("utf-8", errors="replace")
    lower_content_type = content_type.lower()
    if "application/json" in lower_content_type:
        try:
            return redact_payload(json.loads(text))
        except json.JSONDecodeError:
            return text
    if "application/x-www-form-urlencoded" in lower_content_type:
        parsed = parse_qs(text, keep_blank_values=True)
        return redact_payload({key: values[-1] if values else "" for key, values in parsed.items()})
    if lower_content_type.startswith("text/") or "html" in lower_content_type:
        return redact_text(text)
    return {"base64_omitted": True, "byte_length": len(body)}


def redact_query_string(query_string: str) -> dict[str, Any]:
    if not query_string:
        return {}
    parsed = parse_qs(query_string, keep_blank_values=True)
    normalized = {
        key: values if len(values) > 1 else values[0]
        for key, values in parsed.items()
    }
    return redact_payload(normalized)


def redact_payload(value: Any, key: str | None = None) -> Any:
    if key and is_sensitive_key(key):
        return REDACTED
    if isinstance(value, dict):
        return {item_key: redact_payload(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact_payload(item, key) for item in value]
    return value


def redact_mapping(headers: dict[str, str]) -> dict[str, str]:
    return {key: redact_header_value(key, value) for key, value in headers.items()}


def redact_header_value(key: str, value: str) -> str:
    if is_sensitive_key(key):
        return REDACTED
    if key.lower() == "location":
        return redact_url(value)
    return value


def redact_text(text: str) -> str:
    text = redact_key_value_pairs(text)
    return redact_hidden_inputs(text)


def redact_key_value_pairs(text: str) -> str:
    sensitive_names = "|".join(sorted(SENSITIVE_EXACT_KEYS))
    return re.sub(
        rf"(?i)([?&]({sensitive_names})=)([^&\"'<>\\s]+)",
        lambda match: f"{match.group(1)}{REDACTED}",
        text,
    )


def redact_hidden_inputs(text: str) -> str:
    sensitive_names = "|".join(sorted(SENSITIVE_EXACT_KEYS))
    return re.sub(
        rf'(?i)(name=["\']({sensitive_names})["\'][^>]*value=["\'])([^"\']+)(["\'])',
        lambda match: f"{match.group(1)}{REDACTED}{match.group(4)}",
        text,
    )


def redact_url(value: str) -> str:
    try:
        parts = urlsplit(value)
    except ValueError:
        return redact_text(value)
    query = parse_qs(parts.query, keep_blank_values=True)
    redacted_items: list[tuple[str, str]] = []
    for key, values in query.items():
        if is_sensitive_key(key):
            redacted_items.append((key, REDACTED))
        else:
            redacted_items.extend((key, item) for item in values)
    encoded_query = urlencode(
        redacted_items,
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, encoded_query, parts.fragment))


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return (
        normalized in SENSITIVE_EXACT_KEYS
        or "password" in normalized
        or "secret" in normalized
        or normalized.endswith("_token")
        or normalized.endswith("_api_key")
    )
def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)
