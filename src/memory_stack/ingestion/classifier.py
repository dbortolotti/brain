from __future__ import annotations


SOURCE_KINDS = {
    "auto",
    "article",
    "transcript",
    "markdown",
    "pdf",
    "email",
    "table",
    "chat_log",
    "other",
}


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


def source_kind_for_input_type(input_type: str, requested_kind: str | None = None) -> str:
    normalized = (requested_kind or "auto").strip().lower()
    if normalized in SOURCE_KINDS and normalized != "auto":
        return normalized
    if input_type == "article_url":
        return "article"
    if input_type == "source_text":
        return "markdown"
    return "table" if input_type == "table" else input_type
