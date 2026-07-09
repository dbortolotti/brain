from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from memory_stack.cfg import Settings
from memory_stack.evals.model_matrix import ModelCandidate
from memory_stack.local_embeddings import fastembed_vector
from memory_stack.provider_auth import (
    ProviderAuthError,
    openai_embeddings_base_url,
    openai_responses_base_url,
    resolve_openai_text_bearer,
)


MAX_OUTPUT_TOKENS = 2000
SMOKE_PROMPT = 'Return exactly this JSON object: {"ok": true}'
SMOKE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
    "additionalProperties": False,
}
JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class ModelCallResult:
    status: str
    payload: dict[str, Any] | None
    raw_text: str
    error: str | None
    latency_ms: float | None
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    attempt_count: int = 1
    retry_count: int = 0


@dataclass(frozen=True)
class RetryCallResult:
    value: Any
    attempt_count: int


class ProviderCallError(RuntimeError):
    pass


class MissingJsonObjectError(ProviderCallError):
    def __init__(self, message: str, *, raw_text: str = "") -> None:
        super().__init__(message)
        self.raw_text = raw_text


class ModelOutputSchemaError(ValueError):
    def __init__(self, message: str, *, raw_text: str) -> None:
        super().__init__(message)
        self.raw_text = raw_text


class ProviderRetryError(ProviderCallError):
    def __init__(self, exc: Exception, *, attempt_count: int) -> None:
        super().__init__(str(exc))
        self.attempt_count = attempt_count
        self.original_error = exc


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
        attempt_count = 0
        try:
            if missing := self.missing_credential(candidate):
                raise ProviderCallError(missing)
            retry_result = self._retry_call(
                lambda: self._complete_json_payload(candidate, prompt=prompt, schema=schema)
            )
            raw_text, payload = retry_result.value
            attempt_count = retry_result.attempt_count
            status = "ok"
            error = None
        except ModelOutputSchemaError as exc:
            attempt_count = int(getattr(exc, "attempt_count", attempt_count))
            raw_text = exc.raw_text
            payload = None
            status = "schema_fail"
            error = redact(str(exc), self.settings)
        except Exception as exc:
            attempt_count = int(getattr(exc, "attempt_count", attempt_count))
            raw_text = str(getattr(getattr(exc, "original_error", exc), "raw_text", ""))
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
            attempt_count=attempt_count,
            retry_count=max(0, attempt_count - 1),
        )

    def _complete_json_payload(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        raw_text = self._complete_text(candidate, prompt=prompt, schema=schema)
        try:
            return raw_text, parse_json_object(raw_text)
        except MissingJsonObjectError:
            raise
        except Exception as exc:
            raise ModelOutputSchemaError(str(exc), raw_text=raw_text) from exc

    def embed(self, candidate: ModelCandidate, *, text: str) -> ModelCallResult:
        started = time.perf_counter()
        input_tokens = estimate_tokens(text)
        attempt_count = 0
        try:
            if missing := self.missing_credential(candidate):
                raise ProviderCallError(missing)
            retry_result = self._retry_call(
                lambda: self._embedding_vector(candidate, text=text)
            )
            vector = retry_result.value
            attempt_count = retry_result.attempt_count
            payload = {
                "embedding_vector_size": len(vector),
                "embedding_vector": vector,
            }
            raw_text = json.dumps(payload)
            status = "ok"
            error = None
        except Exception as exc:
            attempt_count = int(getattr(exc, "attempt_count", attempt_count))
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
            attempt_count=attempt_count,
            retry_count=max(0, attempt_count - 1),
        )

    def smoke(self, candidate: ModelCandidate) -> None:
        if candidate.kind == "embedding":
            result = self.embed(candidate, text="brain smoke test")
            if result.status != "ok":
                raise ProviderCallError(result.error or "embedding smoke failed")
            return

        result = self.complete_json(
            candidate,
            prompt=SMOKE_PROMPT,
            schema=SMOKE_SCHEMA,
        )
        if result.status != "ok":
            raise ProviderCallError(result.error or "LLM smoke failed")
        if not result.payload or result.payload.get("ok") is not True:
            raise ProviderCallError("LLM smoke response did not include ok=true")

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
        if candidate.provider == "openai" and self.settings.openai_auth_mode == "oauth":
            try:
                resolve_openai_text_bearer(self.settings)
            except ProviderAuthError as exc:
                return str(exc)
            return None
        if candidate.provider == "openai" and getattr(candidate, "kind", "llm") == "embedding":
            if not self.settings.configured_provider_api_key("openai"):
                return "missing OPENAI_API_KEY for OpenAI embeddings"
            return None
        if candidate.provider == "fastembed" and getattr(candidate, "kind", "llm") == "embedding":
            return None
        if not self.settings.provider_api_key(candidate.provider):
            return missing_provider_api_key_message(candidate.provider)
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
        if candidate.provider == "openrouter":
            return self._openrouter_chat_completion(candidate, prompt=prompt, schema=schema)
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
        bearer = resolve_openai_text_bearer(self.settings)
        base_url = (
            openai_responses_base_url(self.settings)
            if self.settings.openai_auth_mode == "oauth"
            else "https://api.openai.com/v1"
        )
        request_payload: dict[str, Any] = {
            "model": candidate.api_model or candidate.model,
            "instructions": "Return only one JSON object matching the requested schema. Do not wrap it in Markdown.",
            "input": [{"role": "user", "content": prompt_with_schema(prompt, schema)}],
            "store": False,
            "stream": self.settings.openai_auth_mode == "oauth",
            "reasoning": {"effort": candidate.reasoning_effort or openai_reasoning_effort(candidate.api_model or candidate.model)},
        }
        if self.settings.openai_auth_mode != "oauth":
            request_payload["max_output_tokens"] = MAX_OUTPUT_TOKENS
        response = self.client.post(
            f"{base_url.rstrip('/')}/responses",
            headers={"Authorization": f"Bearer {bearer}"},
            json=request_payload,
        )
        if self.settings.openai_auth_mode == "oauth":
            text = openai_stream_response_text(response)
            if text:
                return text
        else:
            text = openai_response_text(checked_json(response))
            if text:
                return text
        raise ProviderCallError("OpenAI response did not include text")

    def _google_generate_content(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        generation_config: dict[str, Any] = {
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "temperature": 0,
            "responseMimeType": "application/json",
        }
        if thinking_level := google_thinking_level(candidate.reasoning_effort):
            generation_config["thinkingConfig"] = {"thinkingLevel": thinking_level}
        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{quote(candidate.api_model or candidate.model, safe='')}:generateContent",
            headers={"x-goog-api-key": self.settings.provider_api_key("google") or ""},
            json={
                "contents": [{"parts": [{"text": prompt_with_schema(prompt, schema)}]}],
                "generationConfig": generation_config,
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

    def _openrouter_chat_completion(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> str:
        request_json: dict[str, Any] = {
            "model": candidate.api_model or candidate.model,
            "messages": [{"role": "user", "content": prompt_with_schema(prompt, schema)}],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        if candidate.quantizations:
            request_json["provider"] = {"quantizations": list(candidate.quantizations)}
        response = self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.provider_api_key('openrouter')}"},
            json=request_json,
        )
        payload = checked_json(response)
        message = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content"))
        if isinstance(message, str) and message.strip():
            return message
        raise ProviderCallError("OpenRouter response did not include message content")

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

    def _embedding_vector(self, candidate: ModelCandidate, *, text: str) -> list[float]:
        if candidate.provider == "openai":
            base_url = (
                openai_embeddings_base_url(self.settings)
                if self.settings.openai_auth_mode == "oauth"
                else "https://api.openai.com/v1"
            )
            response = self.client.post(
                f"{base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {resolve_openai_text_bearer(self.settings)}"
                    if self.settings.openai_auth_mode == "oauth"
                    else f"Bearer {self.settings.configured_provider_api_key('openai')}"
                },
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
                f"https://generativelanguage.googleapis.com/v1beta/models/{quote(candidate.api_model or candidate.model, safe='')}:embedContent",
                headers={"x-goog-api-key": self.settings.provider_api_key("google") or ""},
                json={
                    "model": f"models/{candidate.api_model or candidate.model}",
                    "content": {"parts": [{"text": text}]},
                },
            )
            payload = checked_json(response)
            vector = (payload.get("embedding") or {}).get("values")
        elif candidate.provider == "fastembed":
            return fastembed_vector(candidate.api_model or candidate.model, text)
        else:
            raise ProviderCallError(f"unsupported embedding provider: {candidate.provider}")
        if not isinstance(vector, list) or not vector:
            raise ProviderCallError("embedding response did not include a vector")
        return [float(value) for value in vector]

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
                return RetryCallResult(value=fn(), attempt_count=attempt_idx + 1)
            except Exception as exc:
                last_error = exc
                if isinstance(exc, ModelOutputSchemaError):
                    exc.attempt_count = attempt_idx + 1
                    raise
                if attempt_idx >= attempts - 1 or not is_retryable_provider_error(exc):
                    raise ProviderRetryError(exc, attempt_count=attempt_idx + 1) from exc
                delay_seconds = self._retry_backoff_seconds * (2**attempt_idx)
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
        if last_error is not None:
            raise ProviderRetryError(last_error, attempt_count=attempts) from last_error
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
            raise MissingJsonObjectError("model output did not contain a JSON object", raw_text=raw_text)
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ProviderCallError("model output JSON was not an object")
    return payload


def openai_reasoning_effort(model: str) -> str:
    if model.startswith(("gpt-5.4", "gpt-5.5")):
        return "low"
    return "minimal"


def google_thinking_level(reasoning_effort: str | None) -> str | None:
    if reasoning_effort in {"low", "medium", "high"}:
        return reasoning_effort
    return None


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


def openai_response_text(payload: dict[str, Any]) -> str | None:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text
    chunks: list[str] = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(str(content["text"]))
    return "\n".join(chunks) if chunks else None


def openai_stream_response_text(response: httpx.Response) -> str | None:
    if response.status_code >= 400:
        raise ProviderCallError(f"HTTP {response.status_code}: {response_error_message(response)}")
    chunks: list[str] = []
    final_text: str | None = None
    for line in response.text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "")
        if event_type in {"response.output_text.delta", "response.refusal.delta"} and isinstance(event.get("delta"), str):
            chunks.append(event["delta"])
        elif event_type == "response.completed" and isinstance(event.get("response"), dict):
            final_text = openai_response_text(event["response"])
        elif isinstance(event.get("output_text"), str):
            final_text = event["output_text"]
    if chunks:
        return "".join(chunks)
    return final_text


def is_retryable_provider_error(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if not isinstance(exc, ProviderCallError):
        return False
    if isinstance(exc, MissingJsonObjectError):
        return True
    message = str(exc).lower()
    if "response did not include text" in message or "response did not include message content" in message:
        return True
    if "model output did not contain a json object" in message:
        return True
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


def missing_provider_api_key_message(provider: str) -> str:
    env_names = {
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "google": "GEMINI_API_KEY or GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "voyage": "VOYAGE_API_KEY",
    }.get(provider, f"{provider.upper()}_API_KEY")
    return f"missing {env_names}"


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
        "openrouter_api_key",
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
    values = {
        str(getattr(settings, field))
        for field in fields
        if getattr(settings, field, None)
    }
    for env_name in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_BEARER_TOKEN_BEDROCK",
        "GROQ_API_KEY",
        "VOYAGE_API_KEY",
    ):
        if value := os.getenv(env_name):
            values.add(value)
    return values
