from __future__ import annotations

import math
from dataclasses import dataclass

PRICES = {
    "gpt-5.5": {
        "input": 1.25,
        "output": 10.00,
        "embedding": 0.0,
    },
}


@dataclass(frozen=True)
class TokenEstimate:
    source_tokens: int
    chunks: int
    llm_calls: int
    input_tokens_low: int
    input_tokens_high: int
    output_tokens_low: int
    output_tokens_high: int
    embedding_tokens_low: int
    embedding_tokens_high: int
    standard_ingest_paid_estimate_low: float
    standard_ingest_paid_estimate_high: float
    temporal_ingest_paid_estimate_low: float
    temporal_ingest_paid_estimate_high: float
    reported_cost_with_free_tier: float | None


def estimate_tokens(text: str) -> int:
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, math.ceil(len(text) / 4))


def estimate_ingest_cost(
    *,
    source_text: str,
    model: str,
    chunk_size: int = 1024,
    google_free_tier: bool = False,
) -> TokenEstimate:
    source_tokens = estimate_tokens(source_text)
    chunks = max(1, math.ceil(source_tokens / chunk_size))
    llm_calls = chunks * 2

    input_tokens_low = math.ceil(source_tokens * 3.5)
    input_tokens_high = math.ceil(source_tokens * 5.5)
    output_tokens_low = math.ceil(source_tokens * 0.4)
    output_tokens_high = math.ceil(source_tokens * 1.4)
    embedding_tokens_low = math.ceil(source_tokens * 1.2)
    embedding_tokens_high = math.ceil(source_tokens * 2.0)

    prices = PRICES.get(model.split("/")[-1], PRICES.get(model, {}))
    standard_low = paid_cost(
        prices,
        input_tokens_low,
        output_tokens_low,
        embedding_tokens_low,
    )
    standard_high = paid_cost(
        prices,
        input_tokens_high,
        output_tokens_high,
        embedding_tokens_high,
    )
    temporal_low = standard_low * 1.25
    temporal_high = standard_high * 1.75
    reported = 0.0 if google_free_tier and model.startswith("gemini") else None

    return TokenEstimate(
        source_tokens=source_tokens,
        chunks=chunks,
        llm_calls=llm_calls,
        input_tokens_low=input_tokens_low,
        input_tokens_high=input_tokens_high,
        output_tokens_low=output_tokens_low,
        output_tokens_high=output_tokens_high,
        embedding_tokens_low=embedding_tokens_low,
        embedding_tokens_high=embedding_tokens_high,
        standard_ingest_paid_estimate_low=standard_low,
        standard_ingest_paid_estimate_high=standard_high,
        temporal_ingest_paid_estimate_low=temporal_low,
        temporal_ingest_paid_estimate_high=temporal_high,
        reported_cost_with_free_tier=reported,
    )


def paid_cost(
    prices: dict[str, float],
    input_tokens: int,
    output_tokens: int,
    embedding_tokens: int,
) -> float:
    if not prices:
        return 0.0
    return (
        (input_tokens / 1_000_000) * prices["input"]
        + (output_tokens / 1_000_000) * prices["output"]
        + (embedding_tokens / 1_000_000) * prices["embedding"]
    )
