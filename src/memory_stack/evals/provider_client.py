from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from memory_stack.config import Settings
from memory_stack.evals.model_matrix import ModelCandidate


MAX_OUTPUT_TOKENS = 2000
JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class ModelCallResult:
    status: str
    payload: dict[str, Any] | None
    raw_text: str
    error: str | None
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class ProviderCallError(RuntimeError):
    pass


class LiveProviderClient:
    def __init__(
        self,
        settings: Settings,
        *,
        timeout_seconds: float = 60,
        retry_attempts: int = 2,
        retry_backoff_seconds: float = 1.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings
        self._client = http_client
        self._timeout_seconds = timeout_seconds
        self._retry_attempts = retry_attempts
        self._retry_backoff_seconds = retry_backoff_seconds

    def complete_json(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> ModelCallResult:
        started = time.perf_counter()
        input_text = prompt + "\nSchema:\n" + json.dumps(schema, separators=(",", ":"))
        input_tokens = estimate_tokens(input_text)
        try:
            if missing := self.missing_credential(candidate):
                raise ProviderCallError(missing)
            raw_text = self._retry_call(
                lambda: self._complete_text(candidate, prompt=prompt, schema=schema)
            )
            try:
                payload = parse_json_object(raw_text)
            except Exception as exc:
                payload = None
                status = "schema_fail"
                error = redact(str(exc), self.settings)
            else:
                status = "ok"
                error = None
        except Exception as exc:
            raw_text = ""
            payload = None
            status = "fail"
            error = redact(str(exc), self.settings)
        latency_ms = int((time.perf_counter() - started) * 1000)
        output_tokens = estimate_tokens(raw_text)
        return ModelCallResult(
            status=status,
            payload=payload,
            raw_text=raw_text,
            error=error,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimate_cost(candidate, input_tokens, output_tokens),
        )

    def embed(self, candidate: ModelCandidate, *, text: str) -> ModelCallResult:
        started = time.perf_counter()
        input_tokens = estimate_tokens(text)
        try:
            if missing := self.missing_credential(candidate):
                raise ProviderCallError(missing)
            vector_size = self._retry_call(
                lambda: self._embedding_vector_size(candidate, text=text)
            )
            payload = {"embedding_vector_size": vector_size}
            raw_text = json.dumps(payload)
            status = "ok"
            error = None
        except Exception as exc:
            payload = None
            raw_text = ""
            status = "fail"
            error = redact(str(exc), self.settings)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ModelCallResult(
            status=status,
            payload=payload,
            raw_text=raw_text,
            error=error,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=0,
            estimated_cost_usd=estimate_cost(candidate, input_tokens, 0),
        )

    def missing_credential(self, candidate: ModelCandidate) -> str | None:
        if candidate.provider == "aws-bedrock":
            region = self.settings.aws_region or self.settings.aws_default_region
            has_bearer = bool(self.settings.aws_bearer_token_bedrock)
            has_sigv4 = bool(self.settings.aws_access_key_id and self.settings.aws_secret_access_key)
            if not region:
                return "missing AWS_REGION or AWS_DEFAULT_REGION"
            if not has_bearer and not has_sigv4:
                return "missing AWS_BEARER_TOKEN_BEDROCK or AWS access key credentials"
            return None
        if not self.settings.provider_api_key(candidate.provider):
            return f"missing provider API key for {candidate.provider}"
        return None

    def _complete_text(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        if candidate.provider == "openai":
            return self._openai_response(candidate, prompt=prompt, schema=schema)
        if candidate.provider == "google":
            return self._google_generate_content(candidate, prompt=prompt, schema=schema)
        if candidate.provider == "anthropic":
            return self._anthropic_message(candidate, prompt=prompt, schema=schema)
        if candidate.provider == "groq":
            return self._groq_chat_completion(candidate, prompt=prompt, schema=schema)
        if candidate.provider == "aws-bedrock":
            return self._bedrock_converse(candidate, prompt=prompt, schema=schema)
        raise ProviderCallError(f"unsupported LLM provider: {candidate.provider}")

    def _openai_response(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        response = self.client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.settings.provider_api_key('openai')}"},
            json={
                "model": candidate.api_model or candidate.model,
                "input": prompt_with_schema(prompt, schema),
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "reasoning": {"effort": candidate.reasoning_effort or openai_reasoning_effort(candidate.api_model or candidate.model)},
            },
        )
        payload = checked_json(response)
        text = payload.get("output_text")
        if isinstance(text, str) and text.strip():
            return text
        chunks: list[str] = []
        for item in payload.get("output") or []:
            for content in item.get("content") or []:
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    chunks.append(str(content["text"]))
        if chunks:
            return "\n".join(chunks)
        raise ProviderCallError("OpenAI response did not include text")

    def _google_generate_content(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{quote(candidate.model, safe='')}:generateContent",
            headers={"x-goog-api-key": self.settings.provider_api_key("google") or ""},
            json={
                "contents": [{"parts": [{"text": prompt_with_schema(prompt, schema)}]}],
                "generationConfig": {
                    "maxOutputTokens": MAX_OUTPUT_TOKENS,
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
        )
        payload = checked_json(response)
        parts = (
            (((payload.get("candidates") or [{}])[0].get("content") or {}).get("parts"))
            or []
        )
        chunks = [str(part["text"]) for part in parts if part.get("text")]
        if chunks:
            return "\n".join(chunks)
        raise ProviderCallError("Google response did not include text")

    def _anthropic_message(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        response = self.client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.settings.provider_api_key("anthropic") or "",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": candidate.model,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt_with_schema(prompt, schema)}],
            },
        )
        payload = checked_json(response)
        chunks = [
            str(item["text"])
            for item in payload.get("content") or []
            if item.get("type") == "text" and item.get("text")
        ]
        if chunks:
            return "\n".join(chunks)
        raise ProviderCallError("Anthropic response did not include text")

    def _groq_chat_completion(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        response = self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.provider_api_key('groq')}"},
            json={
                "model": candidate.model,
                "messages": [{"role": "user", "content": prompt_with_schema(prompt, schema)}],
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        payload = checked_json(response)
        message = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content"))
        if isinstance(message, str) and message.strip():
            return message
        raise ProviderCallError("Groq response did not include message content")

    def _bedrock_converse(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        region = self.settings.aws_region or self.settings.aws_default_region
        if not region:
            raise ProviderCallError("missing AWS region")
        model_path = quote(candidate.model, safe="")
        url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_path}/converse"
        body = json.dumps(
            {
                "messages": [
                    {"role": "user", "content": [{"text": prompt_with_schema(prompt, schema)}]},
                ],
                "inferenceConfig": {"maxTokens": MAX_OUTPUT_TOKENS, "temperature": 0},
            },
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.settings.aws_bearer_token_bedrock:
            headers["Authorization"] = f"Bearer {self.settings.aws_bearer_token_bedrock}"
        else:
            headers.update(sigv4_headers(self.settings, url=url, body=body, region=region))
        response = self.client.post(url, headers=headers, content=body)
        payload = checked_json(response)
        content = ((payload.get("output") or {}).get("message") or {}).get("content") or []
        chunks = [str(item["text"]) for item in content if item.get("text")]
        if chunks:
            return "\n".join(chunks)
        raise ProviderCallError("Bedrock response did not include message text")

    def _embedding_vector_size(self, candidate: ModelCandidate, *, text: str) -> int:
        if candidate.provider == "openai":
            response = self.client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.settings.provider_api_key('openai')}"},
                json={"model": candidate.api_model or candidate.model, "input": text},
            )
            payload = checked_json(response)
            vector = ((payload.get("data") or [{}])[0].get("embedding"))
        elif candidate.provider == "voyage":
            response = self.client.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.settings.provider_api_key('voyage')}"},
                json={"model": candidate.model, "input": [text]},
            )
            payload = checked_json(response)
            vector = ((payload.get("data") or [{}])[0].get("embedding"))
        elif candidate.provider == "google":
            response = self.client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{quote(candidate.model, safe='')}:embedContent",
                headers={"x-goog-api-key": self.settings.provider_api_key("google") or ""},
                json={
                    "model": f"models/{candidate.model}",
                    "content": {"parts": [{"text": text}]},
                },
            )
            payload = checked_json(response)
            vector = (payload.get("embedding") or {}).get("values")
        else:
            raise ProviderCallError(f"unsupported embedding provider: {candidate.provider}")
        if not isinstance(vector, list) or not vector:
            raise ProviderCallError("embedding response did not include a vector")
        return len(vector)

    @property
    def client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        self._client = httpx.Client(timeout=self._timeout_seconds)
        return self._client

    def _retry_call(self, fn):
        attempts = self._retry_attempts + 1
        last_error: Exception | None = None
        for attempt_idx in range(attempts):
            try:
                return fn()
            except Exception as exc:
                last_error = exc
                if attempt_idx >= attempts - 1 or not is_retryable_provider_error(exc):
                    raise
                delay_seconds = self._retry_backoff_seconds * (2**attempt_idx)
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
        if last_error is not None:
            raise last_error
        raise ProviderCallError("provider call failed without an error")


def prompt_with_schema(prompt: str, schema: dict[str, Any]) -> str:
    return "\n".join(
        [
            prompt,
            "Return only one JSON object. Do not wrap it in Markdown.",
            "JSON schema:",
            json.dumps(schema, separators=(",", ":")),
        ]
    )


def parse_json_object(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except ValueError:
        match = JSON_RE.search(raw_text)
        if not match:
            raise ProviderCallError("model output did not contain a JSON object")
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ProviderCallError("model output JSON was not an object")
    return payload


def openai_reasoning_effort(model: str) -> str:
    if model.startswith(("gpt-5.4", "gpt-5.5")):
        return "low"
    return "minimal"


def checked_json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        raise ProviderCallError(f"HTTP {response.status_code}: {response_error_message(response)}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderCallError("provider returned non-JSON response") from exc
    if not isinstance(payload, dict):
        raise ProviderCallError("provider returned unexpected JSON response")
    return payload


def is_retryable_provider_error(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if not isinstance(exc, ProviderCallError):
        return False
    message = str(exc).lower()
    if "http 429" in message:
        return True
    if any(code in message for code in ("http 500", "http 502", "http 503", "http 504")):
        return True
    if "rate limit" in message or "high demand" in message or "temporarily unavailable" in message:
        return True
    if "timeout" in message or "timed out" in message:
        return True
    if "connection" in message or "network" in message or "transport" in message:
        return True
    return False


def response_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("type") or error.get("code")
            if message:
                return str(message)
        if isinstance(error, str):
            return error
        if message := payload.get("message"):
            return str(message)
    return json.dumps(payload)[:500]


def sigv4_headers(settings: Settings, *, url: str, body: bytes, region: str) -> dict[str, str]:
    access_key = settings.aws_access_key_id
    secret_key = settings.aws_secret_access_key
    if not access_key or not secret_key:
        raise ProviderCallError("missing AWS access key credentials")

    parsed = urlparse(url)
    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "host": parsed.netloc,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    if settings.aws_session_token:
        headers["x-amz-security-token"] = settings.aws_session_token

    signed_headers = ";".join(sorted(headers))
    canonical_headers = "".join(f"{key}:{headers[key]}\n" for key in sorted(headers))
    canonical_request = "\n".join(
        [
            "POST",
            parsed.path,
            parsed.query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )
    credential_scope = f"{date_stamp}/{region}/bedrock/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    signature = hmac.new(
        aws_signing_key(secret_key, date_stamp, region, "bedrock"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers["authorization"] = (
        "AWS4-HMAC-SHA256 "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    return headers


def aws_signing_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    key = ("AWS4" + secret_key).encode("utf-8")
    for value in (date_stamp, region, service, "aws4_request"):
        key = hmac.new(key, value.encode("utf-8"), hashlib.sha256).digest()
    return key


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost(candidate: ModelCandidate, input_tokens: int, output_tokens: int) -> float:
    input_price = candidate.price_per_1m.get("input") or candidate.price_per_1m.get("input_under_200k") or 0
    output_price = candidate.price_per_1m.get("output") or candidate.price_per_1m.get("output_under_200k") or 0
    return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)


def redact(value: str, settings: Settings) -> str:
    redacted = value
    for secret in secret_values(settings):
        if len(secret) >= 6:
            redacted = redacted.replace(secret, "[redacted]")
    return redacted


def secret_values(settings: Settings) -> set[str]:
    fields = (
        "llm_api_key",
        "embedding_api_key",
        "openai_api_key",
        "gemini_api_key",
        "google_api_key",
        "anthropic_api_key",
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "aws_bearer_token_bedrock",
        "groq_api_key",
        "voyage_api_key",
    )
    return {
        str(getattr(settings, field))
        for field in fields
        if getattr(settings, field, None)
    }
