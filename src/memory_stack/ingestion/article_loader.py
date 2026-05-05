from __future__ import annotations

import re
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field


class ArticleLoadResult(BaseModel):
    title: str | None = None
    text: str
    summary: str | None = None
    status: str = "processed"
    metadata: dict[str, Any] = Field(default_factory=dict)


class FetchResponse(Protocol):
    text: str

    def raise_for_status(self) -> None: ...


def load_article(
    url: str,
    *,
    title: str | None = None,
    why_saved: str | None = None,
    timeout: float = 5.0,
) -> ArticleLoadResult:
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "BrainMemory/0.1"},
        )
        response.raise_for_status()
    except Exception as exc:
        return ArticleLoadResult(
            title=title or url,
            text=url,
            summary=why_saved or f"Saved article URL: {url}",
            status="processed_with_warning",
            metadata={
                "fetch_error": str(exc),
                "capture_note": "URL captured; article fetching failed.",
            },
        )

    extracted_title = title or extract_title(response.text) or url
    text = readable_text(response.text)
    summary = why_saved or summarize(text)
    return ArticleLoadResult(
        title=extracted_title,
        text=text or url,
        summary=summary,
        status="processed",
        metadata={
            "fetched": True,
            "source_url": url,
            "text_length": len(text),
        },
    )


def extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if match is None:
        return None
    return normalize_space(strip_tags(match.group(1))) or None


def readable_text(html: str) -> str:
    cleaned = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    cleaned = re.sub(r"(?is)<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?is)</(p|div|h[1-6]|li|section|article)>", "\n", cleaned)
    return normalize_space(strip_tags(cleaned))


def strip_tags(value: str) -> str:
    return re.sub(r"(?s)<[^>]+>", " ", value)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def summarize(text: str, *, max_chars: int = 500) -> str:
    return text[:max_chars].strip()
