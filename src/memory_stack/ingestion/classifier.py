from __future__ import annotations

from pydantic import BaseModel

from memory_stack.brain_models import IngestSourceRequest, RememberRequest
from memory_stack.domain_constants import SOURCE_KINDS as SOURCE_KIND_VALUES
from memory_stack.text_utils import string_or_none


SOURCE_KINDS = set(SOURCE_KIND_VALUES)


class SourceClassification(BaseModel):
    source_kind: str
    should_create_source: bool
    should_extract_memories: bool
    reason: str
    confidence: str = "medium"


def classify_source_request(request: IngestSourceRequest | RememberRequest) -> SourceClassification:
    if isinstance(request, IngestSourceRequest):
        source_kind = source_kind_for_input_type(
            input_type_for_source_kind(request.source_kind, request.source),
            request.source_kind,
        )
        return SourceClassification(
            source_kind=source_kind,
            should_create_source=True,
            should_extract_memories=request.extract_memories,
            reason=f"Explicit source ingestion request classified as {source_kind}.",
            confidence="high" if request.source_kind != "auto" else "medium",
        )

    text = request.input.strip()
    input_type = request.input_type if request.input_type != "auto" else infer_input_type(text)
    source_kind = source_kind_for_input_type(
        input_type,
        string_or_none(request.context.get("source_kind")),
    )
    should_create = request.source_policy in {"source_only", "source_and_memory"} or input_type in {
        "article_url",
        "article",
        "transcript",
        "markdown",
        "source_text",
        "table",
    }
    return SourceClassification(
        source_kind=source_kind,
        should_create_source=should_create,
        should_extract_memories=request.source_policy != "source_only",
        reason=f"Remember request classified as {input_type}.",
        confidence="medium",
    )


def infer_input_type(text: str) -> str:
    if text.startswith(("http://", "https://")):
        return "article_url"
    if looks_like_table(text):
        return "table"
    if looks_like_transcript(text):
        return "transcript"
    if len(text) > 1200 or text.startswith("#"):
        return "source_text"
    return "basic_fact"


def input_type_for_source_kind(source_kind: str, source: str) -> str:
    normalized = source_kind.strip().lower()
    if normalized == "auto":
        if source.startswith(("http://", "https://")):
            return "article_url"
        return "source_text"
    mapping = {
        "article": "article_url" if source.startswith(("http://", "https://")) else "article",
        "transcript": "transcript",
        "markdown": "markdown",
        "table": "table",
        "chat_log": "transcript",
        "pdf": "source_text",
        "email": "source_text",
        "other": "source_text",
    }
    return mapping.get(normalized, "source_text")


def looks_like_table(text: str) -> bool:
    return "\n|" in text or (text.count(",") >= 4 and "\n" in text)


def looks_like_transcript(text: str) -> bool:
    speaker_lines = 0
    for line in text.splitlines():
        if ":" not in line:
            continue
        speaker, rest = line.split(":", 1)
        if 0 < len(speaker.strip()) <= 40 and rest.strip():
            speaker_lines += 1
    return speaker_lines >= 2


def source_kind_for_input_type(input_type: str, requested_kind: str | None = None) -> str:
    normalized = (requested_kind or "auto").strip().lower()
    if normalized in SOURCE_KINDS and normalized != "auto":
        return normalized
    if input_type == "article_url":
        return "article"
    if input_type == "source_text":
        return "markdown"
    return "table" if input_type == "table" else input_type
