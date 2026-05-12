from __future__ import annotations

from dataclasses import dataclass


DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_MODEL = "gpt-5.5"
DEFAULT_EMBEDDING_PROVIDER = "openai"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_EMBEDDING_DIMENSIONS = 3072


EMBEDDING_PROVIDERS = {"fastembed", "voyage"}


@dataclass(frozen=True)
class ProviderModel:
    provider: str
    model: str

    @property
    def ref(self) -> str:
        return f"{self.provider}:{self.model}"


def normalize_provider(provider: str | None) -> str:
    normalized = (provider or "").strip().lower()
    if normalized == "gemini":
        return "google"
    if normalized == "bedrock":
        return "aws-bedrock"
    return normalized


def parse_model_ref(ref: str) -> ProviderModel:
    if ":" not in ref:
        raise ValueError(f"model ref must be provider:model, got {ref!r}")
    provider, model = ref.split(":", maxsplit=1)
    if not provider or not model:
        raise ValueError(f"model ref must be provider:model, got {ref!r}")
    return ProviderModel(provider=normalize_provider(provider), model=model)


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


def configured_llm(settings: object) -> ProviderModel:
    provider = normalize_provider(str(getattr(settings, "llm_provider")))
    model = strip_provider_prefix(provider, str(getattr(settings, "llm_model")))
    return ProviderModel(provider=provider, model=model)


def configured_embedding(settings: object) -> ProviderModel:
    provider = normalize_provider(str(getattr(settings, "embedding_provider")))
    model = strip_provider_prefix(provider, str(getattr(settings, "embedding_model")))
    return ProviderModel(provider=provider, model=model)


def is_embedding_ref(ref: str) -> bool:
    parsed = parse_model_ref(ref)
    model = parsed.model.lower()
    if parsed.provider == "openai":
        return "embedding" in model
    return parsed.provider in EMBEDDING_PROVIDERS or "embedding" in model or model.startswith("intfloat/")


def parse_csv_list(value: str | None) -> list[str] | None:
    items = [item.strip() for item in (value or "").split(",") if item.strip()]
    return items or None


def parse_csv_set(value: str | None) -> set[str]:
    return set(parse_csv_list(value) or [])
