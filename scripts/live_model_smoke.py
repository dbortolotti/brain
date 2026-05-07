#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import httpx
import yaml
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.config import Settings, load_settings, normalize_provider_name


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "brain_model_registry.yaml"
LLM_PROVIDERS = {"openai", "openrouter", "google", "gemini", "anthropic", "aws-bedrock", "bedrock", "groq"}
EMBEDDING_PROVIDERS = {"openai", "google", "gemini", "voyage"}
LOCAL_PROVIDERS = {"ollama", "fastembed"}
SECRET_FIELDS = (
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
SMOKE_MAX_TOKENS = 16

console = Console()


@dataclass(frozen=True)
class Probe:
    provider: str
    model: str
    kind: str
    label: str
    api_model: str | None = None
    reasoning_effort: str | None = None
    quantizations: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    judge_only: bool = False
    skip_reason: str | None = None


@dataclass(frozen=True)
class ProbeResult:
    probe: Probe
    status: str
    detail: str


class SmokeFailure(RuntimeError):
    """A live provider call failed in a way that should fail the smoke run."""


def main() -> int:
    parser = build_parser()
    args = normalize_args(parser.parse_args())

    if args.scope == "none":
        console.print("[yellow][SKIP][/yellow] live model smoke disabled")
        return 0

    settings = load_settings()
    registry = load_registry(Path(args.registry))
    probes = select_probes(
        settings,
        registry,
        scope=args.scope,
        roles=set(args.role or []),
        include_judge=args.include_judge,
    )
    if not probes:
        console.print("[red][FAIL][/red] no live model probes selected")
        return 1

    with httpx.Client(timeout=args.timeout) as client:
        results = run_probes(
            settings,
            probes,
            client=client,
            skip_missing_keys=args.skip_missing_keys,
        )

    print_results(results)
    if args.json_output:
        write_json_results(Path(args.json_output), results)

    failed = [result for result in results if result.status == "fail"]
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run low-token live model smoke checks.")
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument(
        "--scope",
        choices=("none", "active", "core", "enabled", "all"),
        default=os.getenv("BRAIN_MODEL_SMOKE_SCOPE", "active"),
        help="Model set to test. Use core/enabled/all for registry-wide checks.",
    )
    parser.add_argument(
        "--all-registry",
        action="store_true",
        help=(
            "Shortcut for --scope all --include-judge. Runs one tiny live probe for "
            "every unique model declared in the registry."
        ),
    )
    parser.add_argument("--role", action="append", default=None, help="Limit registry scopes to a role.")
    parser.add_argument(
        "--skip-missing-keys",
        action="store_true",
        default=env_bool("BRAIN_MODEL_SMOKE_SKIP_MISSING_KEYS", False),
        help="Skip probes whose provider credentials are not configured.",
    )
    parser.add_argument(
        "--no-skip-missing-keys",
        dest="skip_missing_keys",
        action="store_false",
    )
    parser.add_argument(
        "--include-judge",
        action="store_true",
        default=env_bool("BRAIN_MODEL_SMOKE_INCLUDE_JUDGE", False),
        help="Include judge_only models in registry scopes.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("BRAIN_MODEL_SMOKE_TIMEOUT_SECONDS", "30")),
    )
    parser.add_argument("--json-output", default=None)
    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    if args.all_registry:
        args.scope = "all"
        args.include_judge = True
    return args


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_registry(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def select_probes(
    settings: Settings,
    registry: dict[str, Any],
    *,
    scope: str,
    roles: set[str],
    include_judge: bool,
) -> list[Probe]:
    if scope == "active":
        return active_probes(settings)
    if scope == "core":
        return core_registry_probes(registry, roles=roles, include_judge=include_judge)
    if scope in {"enabled", "all"}:
        return provider_registry_probes(
            registry,
            enabled_only=scope == "enabled",
            roles=roles,
            include_judge=include_judge,
        )
    raise ValueError(f"unsupported smoke scope: {scope}")


def active_probes(settings: Settings) -> list[Probe]:
    probes = [
        Probe(
            provider=normalize_provider(settings.llm_provider),
            model=strip_provider_prefix(settings.llm_provider, settings.llm_model),
            kind="llm",
            label="active:llm",
        ),
        Probe(
            provider=normalize_provider(settings.embedding_provider),
            model=strip_provider_prefix(settings.embedding_provider, settings.embedding_model),
            kind="embedding",
            label="active:embedding",
        ),
    ]
    if settings.brain_llm_enabled and settings.brain_llm_provider and settings.brain_llm_model:
        probes.append(
            Probe(
                provider=normalize_provider(settings.brain_llm_provider),
                model=strip_provider_prefix(settings.brain_llm_provider, settings.brain_llm_model),
                kind="llm",
                label="active:brain_llm",
            )
        )
    return dedupe_probes(probes)


def core_registry_probes(
    registry: dict[str, Any],
    *,
    roles: set[str],
    include_judge: bool,
) -> list[Probe]:
    index = registry_model_index(registry)
    probes: list[Probe] = []
    for role, refs in (registry.get("core_eval_matrix") or {}).items():
        if roles and role not in roles:
            continue
        for ref in refs or []:
            probe = probe_from_ref(str(ref), index, role=role)
            if probe.skip_reason:
                continue
            if probe.judge_only and not include_judge:
                continue
            probes.append(probe)
    return dedupe_probes(probes)


def provider_registry_probes(
    registry: dict[str, Any],
    *,
    enabled_only: bool,
    roles: set[str],
    include_judge: bool,
) -> list[Probe]:
    probes: list[Probe] = []
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = config.get("type", "llm")
        for model in config.get("models") or []:
            if model_skip_reason(model):
                continue
            if enabled_only and not model.get("enabled_by_default", False):
                continue
            if model.get("judge_only", False) and not include_judge:
                continue
            model_roles = tuple(str(role) for role in model.get("roles", ()))
            if roles and not roles.intersection(model_roles):
                continue
            if provider == "embeddings":
                probe_provider = normalize_provider(str(model["provider"]))
                probe_kind = "embedding"
            else:
                probe_provider = normalize_provider(provider)
                probe_kind = str(provider_type)
            probes.append(
                Probe(
                    provider=probe_provider,
                    model=str(model["id"]),
                    kind=probe_kind,
                    label=f"{probe_provider}:{model['id']}",
                    api_model=str(model.get("api_model") or model["id"]),
                    reasoning_effort=str(model.get("reasoning_effort")) if model.get("reasoning_effort") is not None else None,
                    quantizations=tuple(str(value) for value in model.get("quantizations", ())),
                    roles=model_roles,
                    judge_only=bool(model.get("judge_only", False)),
                )
            )
    return dedupe_probes(probes)


def registry_model_index(registry: dict[str, Any]) -> dict[str, Probe]:
    index: dict[str, Probe] = {}
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = config.get("type", "llm")
        for model in config.get("models") or []:
            if provider == "embeddings":
                probe_provider = normalize_provider(str(model["provider"]))
                kind = "embedding"
            else:
                probe_provider = normalize_provider(provider)
                kind = str(provider_type)
            probe = Probe(
                provider=probe_provider,
                model=str(model["id"]),
                kind=kind,
                label=f"{probe_provider}:{model['id']}",
                api_model=str(model.get("api_model") or model["id"]),
                reasoning_effort=str(model.get("reasoning_effort")) if model.get("reasoning_effort") is not None else None,
                quantizations=tuple(str(value) for value in model.get("quantizations", ())),
                roles=tuple(str(role) for role in model.get("roles", ())),
                judge_only=bool(model.get("judge_only", False)),
                skip_reason=model_skip_reason(model),
            )
            index[f"{probe_provider}:{probe.model}"] = probe
            if alias := model.get("alias"):
                index[f"{probe_provider}:{alias}"] = replace(
                    probe,
                    label=f"{probe_provider}:{alias}",
                )
    return index


def probe_from_ref(ref: str, index: dict[str, Probe], *, role: str) -> Probe:
    if ref in index:
        probe = index[ref]
        return replace(probe, roles=tuple(dict.fromkeys((*probe.roles, role))))
    provider, model = ref.split(":", maxsplit=1)
    kind = "embedding" if role == "embeddings" else "llm"
    return Probe(
        provider=normalize_provider(provider),
        model=model,
        kind=kind,
        label=ref,
        api_model=model,
        roles=(role,),
    )


def normalize_provider(provider: str | None) -> str:
    normalized = normalize_provider_name(provider)
    if normalized == "gemini":
        return "google"
    if normalized == "bedrock":
        return "aws-bedrock"
    return normalized or ""


def strip_provider_prefix(provider: str, model: str) -> str:
    normalized = normalize_provider(provider)
    for prefix in (f"{normalized}/", f"{normalized}:"):
        if model.startswith(prefix):
            return model.removeprefix(prefix)
    if normalized == "google":
        for prefix in ("gemini/", "gemini:"):
            if model.startswith(prefix):
                return model.removeprefix(prefix)
    return model


def dedupe_probes(probes: list[Probe]) -> list[Probe]:
    deduped: dict[tuple[str, str, str], Probe] = {}
    for probe in probes:
        key = (probe.kind, probe.provider, probe.model, probe.quantizations)
        if key not in deduped:
            deduped[key] = probe
            continue
        existing = deduped[key]
        deduped[key] = replace(
            existing,
            roles=tuple(dict.fromkeys((*existing.roles, *probe.roles))),
            judge_only=existing.judge_only or probe.judge_only,
            skip_reason=existing.skip_reason or probe.skip_reason,
        )
    return list(deduped.values())


def run_probes(
    settings: Settings,
    probes: list[Probe],
    *,
    client: httpx.Client,
    skip_missing_keys: bool,
) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for probe in probes:
        missing = missing_credential(settings, probe)
        if missing:
            status = "skip" if skip_missing_keys or probe.provider in LOCAL_PROVIDERS else "fail"
            results.append(ProbeResult(probe, status, missing))
            continue
        try:
            run_probe(settings, probe, client=client)
        except Exception as exc:
            results.append(ProbeResult(probe, "fail", redact(str(exc), settings)))
        else:
            results.append(ProbeResult(probe, "ok", "live call succeeded"))
    return results


def model_skip_reason(model: dict[str, Any]) -> str | None:
    reason = model.get("skip_reason")
    return str(reason) if reason else None


def missing_credential(settings: Settings, probe: Probe) -> str | None:
    if probe.provider in LOCAL_PROVIDERS:
        return f"provider {probe.provider} is local; no cloud smoke call"
    if probe.provider == "aws-bedrock":
        region = settings.aws_region or settings.aws_default_region
        has_bearer = bool(settings.aws_bearer_token_bedrock)
        has_sigv4 = bool(settings.aws_access_key_id and settings.aws_secret_access_key)
        if not region:
            return "missing AWS_REGION or AWS_DEFAULT_REGION"
        if not has_bearer and not has_sigv4:
            return "missing AWS_BEARER_TOKEN_BEDROCK or AWS access key credentials"
        return None
    if probe.kind == "llm" and probe.provider not in LLM_PROVIDERS:
        return f"unsupported LLM provider for live smoke: {probe.provider}"
    if probe.kind == "embedding" and probe.provider not in EMBEDDING_PROVIDERS:
        return f"unsupported embedding provider for live smoke: {probe.provider}"
    if not settings.provider_api_key(probe.provider):
        env_names = {
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "google": "GEMINI_API_KEY or GOOGLE_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY",
            "voyage": "VOYAGE_API_KEY",
        }.get(probe.provider, f"{probe.provider.upper()}_API_KEY")
        return f"missing {env_names}"
    return None


def run_probe(settings: Settings, probe: Probe, *, client: httpx.Client) -> None:
    if probe.kind == "embedding":
        run_embedding_probe(settings, probe, client=client)
        return
    run_llm_probe(settings, probe, client=client)


def run_llm_probe(settings: Settings, probe: Probe, *, client: httpx.Client) -> None:
    if probe.provider == "openai":
        post_openai_response(settings, probe.api_model or probe.model, client=client)
    elif probe.provider == "openrouter":
        post_openrouter_chat_completion(settings, probe.api_model or probe.model, probe.quantizations, client=client)
    elif probe.provider == "google":
        post_google_generate_content(
            settings,
            probe.api_model or probe.model,
            reasoning_effort=probe.reasoning_effort,
            client=client,
        )
    elif probe.provider == "anthropic":
        post_anthropic_message(settings, probe.api_model or probe.model, client=client)
    elif probe.provider == "groq":
        post_groq_chat_completion(settings, probe.api_model or probe.model, client=client)
    elif probe.provider == "aws-bedrock":
        post_bedrock_converse(settings, probe.api_model or probe.model, client=client)
    else:
        raise SmokeFailure(f"unsupported LLM provider for live smoke: {probe.provider}")


def run_embedding_probe(settings: Settings, probe: Probe, *, client: httpx.Client) -> None:
    if probe.provider == "openai":
        post_openai_embedding(settings, probe.model, client=client)
    elif probe.provider == "google":
        post_google_embedding(settings, probe.model, client=client)
    elif probe.provider == "voyage":
        post_voyage_embedding(settings, probe.model, client=client)
    else:
        raise SmokeFailure(f"unsupported embedding provider for live smoke: {probe.provider}")


def post_openai_response(settings: Settings, model: str, *, client: httpx.Client) -> None:
    response = client.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {settings.provider_api_key('openai')}"},
        json={
            "model": model,
            "input": "Reply with exactly: ok",
            "max_output_tokens": SMOKE_MAX_TOKENS,
        },
    )
    payload = checked_json(response, settings)
    if not payload.get("id"):
        raise SmokeFailure("OpenAI response did not include an id")


def post_openai_embedding(settings: Settings, model: str, *, client: httpx.Client) -> None:
    response = client.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {settings.provider_api_key('openai')}"},
        json={"model": model, "input": "brain smoke test"},
    )
    payload = checked_json(response, settings)
    if not vector_present(payload):
        raise SmokeFailure("OpenAI embedding response did not include an embedding vector")


def post_groq_chat_completion(settings: Settings, model: str, *, client: httpx.Client) -> None:
    response = client.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.provider_api_key('groq')}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
            "max_tokens": SMOKE_MAX_TOKENS,
        },
    )
    payload = checked_json(response, settings)
    if not payload.get("choices"):
        raise SmokeFailure("Groq response did not include choices")


def post_openrouter_chat_completion(
    settings: Settings,
    model: str,
    quantizations: tuple[str, ...],
    *,
    client: httpx.Client,
) -> None:
    request_json: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
        "max_tokens": SMOKE_MAX_TOKENS,
    }
    if quantizations:
        request_json["provider"] = {"quantizations": list(quantizations)}
    response = client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.provider_api_key('openrouter')}"},
        json=request_json,
    )
    payload = checked_json(response, settings)
    if not payload.get("choices"):
        raise SmokeFailure("OpenRouter response did not include choices")


def post_google_generate_content(
    settings: Settings,
    model: str,
    *,
    reasoning_effort: str | None = None,
    client: httpx.Client,
) -> None:
    generation_config: dict[str, Any] = {"maxOutputTokens": SMOKE_MAX_TOKENS, "temperature": 0}
    if thinking_level := google_thinking_level(reasoning_effort):
        generation_config["thinkingConfig"] = {"thinkingLevel": thinking_level}
    response = client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent",
        headers={"x-goog-api-key": settings.provider_api_key("google") or ""},
        json={
            "contents": [{"parts": [{"text": "Reply with exactly: ok"}]}],
            "generationConfig": generation_config,
        },
    )
    payload = checked_json(response, settings)
    if not payload.get("candidates"):
        raise SmokeFailure("Google response did not include candidates")


def post_google_embedding(settings: Settings, model: str, *, client: httpx.Client) -> None:
    response = client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:embedContent",
        headers={"x-goog-api-key": settings.provider_api_key("google") or ""},
        json={
            "model": f"models/{model}",
            "content": {"parts": [{"text": "brain smoke test"}]},
        },
    )
    payload = checked_json(response, settings)
    values = (payload.get("embedding") or {}).get("values")
    if not isinstance(values, list) or not values:
        raise SmokeFailure("Google embedding response did not include an embedding vector")


def post_anthropic_message(settings: Settings, model: str, *, client: httpx.Client) -> None:
    response = client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.provider_api_key("anthropic") or "",
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": model,
            "max_tokens": SMOKE_MAX_TOKENS,
            "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
        },
    )
    payload = checked_json(response, settings)
    if not payload.get("content"):
        raise SmokeFailure("Anthropic response did not include content")


def post_voyage_embedding(settings: Settings, model: str, *, client: httpx.Client) -> None:
    response = client.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {settings.provider_api_key('voyage')}"},
        json={"model": model, "input": ["brain smoke test"]},
    )
    payload = checked_json(response, settings)
    if not vector_present(payload):
        raise SmokeFailure("Voyage embedding response did not include an embedding vector")


def post_bedrock_converse(settings: Settings, model: str, *, client: httpx.Client) -> None:
    region = settings.aws_region or settings.aws_default_region
    if not region:
        raise SmokeFailure("missing AWS region")
    model_path = quote(model, safe="")
    url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_path}/converse"
    body = json.dumps(
        {
            "messages": [
                {"role": "user", "content": [{"text": "Reply with exactly: ok"}]},
            ],
            "inferenceConfig": {"maxTokens": SMOKE_MAX_TOKENS, "temperature": 0},
        },
        separators=(",", ":"),
    ).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if settings.aws_bearer_token_bedrock:
        headers["Authorization"] = f"Bearer {settings.aws_bearer_token_bedrock}"
    else:
        headers.update(sigv4_headers(settings, url=url, body=body, region=region))
    response = client.post(url, headers=headers, content=body)
    payload = checked_json(response, settings)
    content = ((payload.get("output") or {}).get("message") or {}).get("content")
    if not content:
        raise SmokeFailure("Bedrock response did not include message content")


def sigv4_headers(settings: Settings, *, url: str, body: bytes, region: str) -> dict[str, str]:
    access_key = settings.aws_access_key_id
    secret_key = settings.aws_secret_access_key
    if not access_key or not secret_key:
        raise SmokeFailure("missing AWS access key credentials")

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
    signing_key = aws_signing_key(secret_key, date_stamp, region, "bedrock")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
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


def checked_json(response: httpx.Response, settings: Settings) -> dict[str, Any]:
    if response.status_code >= 400:
        raise SmokeFailure(
            f"HTTP {response.status_code}: {redact(response_error_message(response), settings)}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise SmokeFailure("provider returned non-JSON response") from exc
    if not isinstance(payload, dict):
        raise SmokeFailure("provider returned unexpected JSON response")
    return payload


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
        message = payload.get("message")
        if message:
            return str(message)
    return json.dumps(payload)[:500]


def vector_present(payload: dict[str, Any]) -> bool:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return False
    embedding = data[0].get("embedding") if isinstance(data[0], dict) else None
    return isinstance(embedding, list) and bool(embedding)


def google_thinking_level(reasoning_effort: str | None) -> str | None:
    if reasoning_effort in {"low", "medium", "high"}:
        return reasoning_effort
    return None


def redact(value: str, settings: Settings) -> str:
    redacted = value
    for secret in secret_values(settings):
        if len(secret) >= 6:
            redacted = redacted.replace(secret, "[redacted]")
    return redacted


def secret_values(settings: Settings) -> set[str]:
    values = {
        str(getattr(settings, field))
        for field in SECRET_FIELDS
        if getattr(settings, field, None)
    }
    for env_name in (
        "OPENAI_API_KEY",
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


def print_results(results: list[ProbeResult]) -> None:
    table = Table(title="Live Model Smoke")
    table.add_column("Status")
    table.add_column("Kind")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Roles")
    table.add_column("Detail")
    for result in results:
        style = {"ok": "green", "skip": "yellow", "fail": "red"}[result.status]
        table.add_row(
            f"[{style}]{result.status.upper()}[/{style}]",
            result.probe.kind,
            result.probe.provider,
            result.probe.model,
            ",".join(result.probe.roles),
            result.detail,
        )
    console.print(table)


def write_json_results(path: Path, results: list[ProbeResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            [
                {
                    "status": result.status,
                    "detail": result.detail,
                    "kind": result.probe.kind,
                    "provider": result.probe.provider,
                    "model": result.probe.model,
                    "label": result.probe.label,
                    "roles": list(result.probe.roles),
                    "judge_only": result.probe.judge_only,
                }
                for result in results
            ],
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
