from __future__ import annotations

from memory_stack.cfg import Settings
from memory_stack.model_selection import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    configured_embedding,
    configured_llm,
    is_embedding_ref,
)


def test_settings_default_to_single_prod_llm_and_embedding_models() -> None:
    settings = Settings()

    assert configured_llm(settings).ref == f"{DEFAULT_LLM_PROVIDER}:{DEFAULT_LLM_MODEL}"
    assert configured_embedding(settings).ref == (
        f"{DEFAULT_EMBEDDING_PROVIDER}:{DEFAULT_EMBEDDING_MODEL}"
    )
    assert settings.embedding_dimensions == DEFAULT_EMBEDDING_DIMENSIONS


def test_embedding_ref_classification_is_explicit() -> None:
    assert is_embedding_ref("fastembed:intfloat/multilingual-e5-large") is True
    assert is_embedding_ref("openai:gpt-5.5") is False
