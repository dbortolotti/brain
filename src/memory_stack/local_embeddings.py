from __future__ import annotations

from typing import Literal


EmbeddingInputType = Literal["query", "passage"]


def fastembed_input_text(
    model: str,
    text: str,
    *,
    input_type: EmbeddingInputType = "passage",
) -> str:
    if is_e5_model(model) and not has_e5_prefix(text):
        return f"{input_type}: {text}"
    return text


def fastembed_vector_size(
    model: str,
    text: str,
    *,
    input_type: EmbeddingInputType = "passage",
) -> int:
    return len(fastembed_vector(model, text, input_type=input_type))


def fastembed_vector(
    model: str,
    text: str,
    *,
    input_type: EmbeddingInputType = "passage",
) -> list[float]:
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:  # pragma: no cover - depends on optional local extra.
        raise RuntimeError("fastembed is required for local FastEmbed embeddings") from exc

    embedding_model = TextEmbedding(model_name=model)
    vectors = list(
        embedding_model.embed(
            [fastembed_input_text(model, text, input_type=input_type)],
            batch_size=1,
            parallel=None,
        )
    )
    if not vectors:
        raise RuntimeError("FastEmbed did not return an embedding vector")
    return [float(value) for value in vectors[0]]


def is_e5_model(model: str) -> bool:
    normalized = model.lower()
    return "/e5-" in normalized or normalized.startswith("e5-") or "multilingual-e5" in normalized


def has_e5_prefix(text: str) -> bool:
    normalized = text.lstrip().lower()
    return normalized.startswith("query:") or normalized.startswith("passage:")
