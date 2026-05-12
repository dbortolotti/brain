from __future__ import annotations

import html
import json
import re
import ssl
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlparse
from urllib.request import Request, urlopen

import certifi

from memory_stack.config import Settings
from memory_stack.taste.media import (
    RESTAURANT_GENRE_ALIASES,
    RESTAURANT_GENRES,
    normalize_restaurant_cuisine,
    normalize_restaurant_metadata,
)


GOOGLE_FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
MICHELIN_SEARCH_URL = "https://guide.michelin.com/en/search"
DUCKDUCKGO_HTML_URL = "https://duckduckgo.com/html/"


def fetch_restaurant_enrichment(
    *,
    canonical_name: str,
    metadata: dict[str, Any],
    settings: Settings,
    allow_broader_web_search: bool = False,
    timeout: float = 10,
) -> dict[str, Any]:
    normalized: dict[str, Any] = normalize_restaurant_metadata(metadata)
    warnings: list[str] = []
    sources: list[dict[str, Any]] = []
    source_payloads: dict[str, Any] = {}

    official_url = official_website_url(metadata)
    if official_url and settings.brain_taste_web_enrichment_enabled:
        result = fetch_official_website_metadata(official_url, timeout=timeout)
        normalized = merge_restaurant_enrichment(normalized, result["metadata"])
        warnings.extend(result["warnings"])
        sources.extend(result["sources"])
        source_payloads["official_website"] = result["source_payload"]

    google_result = fetch_google_places_metadata(
        canonical_name=canonical_name,
        api_key=settings.brain_taste_google_places_api_key,
        timeout=timeout,
    )
    normalized = merge_restaurant_enrichment(normalized, google_result["metadata"])
    warnings.extend(google_result["warnings"])
    sources.extend(google_result["sources"])
    if google_result["source_payload"]:
        source_payloads["google_places"] = google_result["source_payload"]

    if settings.brain_taste_web_enrichment_enabled:
        michelin_result = fetch_michelin_metadata(canonical_name, timeout=timeout)
        normalized = merge_restaurant_enrichment(normalized, michelin_result["metadata"])
        warnings.extend(michelin_result["warnings"])
        sources.extend(michelin_result["sources"])
        if michelin_result["source_payload"]:
            source_payloads["michelin"] = michelin_result["source_payload"]

    if allow_broader_web_search:
        if settings.brain_taste_web_enrichment_enabled:
            broad_result = fetch_controlled_web_restaurant_metadata(
                canonical_name,
                timeout=timeout,
            )
            normalized = merge_restaurant_enrichment(normalized, broad_result["metadata"])
            warnings.extend(broad_result["warnings"])
            sources.extend(broad_result["sources"])
            if broad_result["source_payload"]:
                source_payloads["controlled_web_search"] = broad_result["source_payload"]
        else:
            warnings.append("Broader web search was requested but BRAIN_TASTE_WEB_ENRICHMENT_ENABLED is false.")
    else:
        warnings.append("Broader web search was not approved; only strict restaurant sources were used.")

    return {
        "metadata": normalize_restaurant_metadata(normalized),
        "warnings": warnings,
        "sources": unique_sources(sources),
        "source_payloads": source_payloads,
    }


def fetch_google_places_metadata(
    *,
    canonical_name: str,
    api_key: str | None,
    timeout: float = 10,
) -> dict[str, Any]:
    if not api_key:
        return {
            "metadata": {},
            "warnings": ["BRAIN_TASTE_GOOGLE_PLACES_API_KEY is not set; Google Places was not queried."],
            "sources": [],
            "source_payload": None,
        }
    params = {
        "input": canonical_name,
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address,rating,user_ratings_total,types,website,url,price_level",
        "key": api_key,
    }
    url = f"{GOOGLE_FIND_PLACE_URL}?{urlencode(params)}"
    try:
        payload = fetch_json_url(url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "metadata": {},
            "warnings": [f"Google Places lookup failed: {exc}"],
            "sources": [],
            "source_payload": {"url": redacted_google_key_url(url), "error": str(exc)},
        }

    if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
        return {
            "metadata": {},
            "warnings": [f"Google Places lookup failed: {payload.get('status') or 'unknown status'}"],
            "sources": [],
            "source_payload": payload_without_key(payload, url),
        }
    candidates = payload.get("candidates") or []
    if not candidates:
        return {
            "metadata": {},
            "warnings": ["Google Places returned no restaurant candidate."],
            "sources": [],
            "source_payload": payload_without_key(payload, url),
        }

    candidate = candidates[0]
    source_url = candidate.get("url") or maps_search_url(canonical_name)
    metadata = {
        "google": {
            "rating": candidate.get("rating"),
            "rating_count": candidate.get("user_ratings_total"),
            "source_url": source_url,
            "source": "google_places",
            "checked_at": checked_at(),
        },
        "cuisine": cuisine_from_terms(candidate.get("types") or []),
    }
    return {
        "metadata": metadata,
        "warnings": [],
        "sources": [
            {
                "name": "google_places",
                "url": source_url,
                "source_quality": "strict",
            }
        ],
        "source_payload": {
            "request_url": redacted_google_key_url(url),
            "candidate": candidate,
        },
    }


def fetch_michelin_metadata(canonical_name: str, *, timeout: float = 10) -> dict[str, Any]:
    url = f"{MICHELIN_SEARCH_URL}?{urlencode({'q': canonical_name})}"
    try:
        text = fetch_text_url(url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "metadata": {},
            "warnings": [f"Michelin Guide lookup failed: {exc}"],
            "sources": [],
            "source_payload": {"url": url, "error": str(exc)},
        }
    metadata = michelin_html_to_metadata(text, canonical_name, url)
    if not metadata:
        return {
            "metadata": {},
            "warnings": ["Michelin Guide returned no strict match."],
            "sources": [],
            "source_payload": {"url": url, "matched": False},
        }
    return {
        "metadata": {"michelin": metadata},
        "warnings": [],
        "sources": [
            {
                "name": "michelin_guide",
                "url": metadata["source_url"],
                "source_quality": "strict",
            }
        ],
        "source_payload": {"url": url, "matched": True},
    }


def fetch_official_website_metadata(url: str, *, timeout: float = 10) -> dict[str, Any]:
    if not is_http_url(url):
        return {
            "metadata": {},
            "warnings": [f"Official website URL is not fetchable: {url}"],
            "sources": [],
            "source_payload": None,
        }
    try:
        text = fetch_text_url(url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "metadata": {},
            "warnings": [f"Official website lookup failed: {exc}"],
            "sources": [],
            "source_payload": {"url": url, "error": str(exc)},
        }
    cuisine = cuisine_from_terms(extract_visible_terms(text))
    return {
        "metadata": {"cuisine": cuisine} if cuisine else {},
        "warnings": [] if cuisine else ["Official website did not expose recognizable cuisine metadata."],
        "sources": [{"name": "official_website", "url": url, "source_quality": "strict"}],
        "source_payload": {"url": url, "matched_cuisine": sorted(cuisine)},
    }


def fetch_controlled_web_restaurant_metadata(
    canonical_name: str,
    *,
    timeout: float = 10,
) -> dict[str, Any]:
    query = f"{canonical_name} restaurant cuisine menu"
    url = f"{DUCKDUCKGO_HTML_URL}?{urlencode({'q': query})}"
    try:
        text = fetch_text_url(url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "metadata": {},
            "warnings": [f"Controlled web search failed: {exc}"],
            "sources": [],
            "source_payload": {"url": url, "error": str(exc)},
        }
    results = duckduckgo_results(text, limit=5)
    source_urls = [result["url"] for result in results if result.get("url")]
    cuisine = cuisine_from_terms(
        " ".join(
            [
                result.get("title", "")
                + " "
                + result.get("snippet", "")
                for result in results
            ]
        )
    )
    warnings = [
        "Broader web search was user-approved; promoted fields are limited to validated cuisine terms."
    ]
    if not results:
        warnings.append("Controlled web search returned no usable source URLs.")
    return {
        "metadata": {"cuisine": cuisine} if cuisine and source_urls else {},
        "warnings": warnings,
        "sources": [
            {"name": "controlled_web_search", "url": source_url, "source_quality": "broad_web"}
            for source_url in source_urls
        ],
        "source_payload": {"query_url": url, "results": results},
    }


def michelin_html_to_metadata(
    text: str,
    canonical_name: str,
    source_url: str,
) -> dict[str, Any]:
    plain = html_to_text(text)
    if normalize_for_match(canonical_name) not in normalize_for_match(plain):
        return {}
    lower = plain.casefold()
    stars = None
    status = "selected"
    if "three michelin stars" in lower or "3 michelin stars" in lower:
        stars = 3
    elif "two michelin stars" in lower or "2 michelin stars" in lower:
        stars = 2
    elif "one michelin star" in lower or "1 michelin star" in lower:
        stars = 1
    if stars is not None:
        status = {1: "one_star", 2: "two_stars", 3: "three_stars"}[stars]
    elif "bib gourmand" in lower:
        status = "bib_gourmand"
        stars = 0
    elif "selected restaurant" in lower or "michelin selected" in lower:
        status = "selected"
        stars = 0
    return {
        "status": status,
        "stars": stars,
        "green_star": "green star" in lower,
        "source_url": source_url,
        "source": "guide.michelin.com",
        "checked_at": checked_at(),
    }


def duckduckgo_results(text: str, *, limit: int) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    result_blocks = re.findall(
        r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not result_blocks:
        result_blocks = re.findall(
            r'<a[^>]+href="(?P<url>https?://[^"]+)"[^>]*>(?P<title>.*?)</a>',
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        result_blocks = [(url, title, "") for url, title in result_blocks]
    for raw_url, raw_title, raw_snippet in result_blocks:
        url = clean_result_url(html.unescape(raw_url))
        if not is_http_url(url):
            continue
        results.append(
            {
                "url": url,
                "title": html_to_text(raw_title),
                "snippet": html_to_text(raw_snippet),
            }
        )
        if len(results) >= limit:
            break
    return results


def cuisine_from_terms(value: Any) -> dict[str, dict[str, Any]]:
    if isinstance(value, str):
        lower = value.casefold().replace("-", " ").replace("_", " ")
        terms: list[str] = []
        for cuisine in RESTAURANT_GENRES:
            if re.search(rf"\b{re.escape(cuisine.replace('_', ' '))}\b", lower):
                terms.append(cuisine)
        for alias, cuisine in RESTAURANT_GENRE_ALIASES.items():
            if re.search(rf"\b{re.escape(alias.replace('_', ' '))}\b", lower):
                terms.append(cuisine)
        if terms:
            return normalize_restaurant_cuisine(terms)
    if isinstance(value, list):
        joined = " ".join(str(item) for item in value)
        from_joined = cuisine_from_terms(joined)
        if from_joined:
            return from_joined
    return normalize_restaurant_cuisine(value)


def extract_visible_terms(text: str) -> str:
    return html_to_text(text)


def html_to_text(text: str) -> str:
    no_scripts = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    stripped = re.sub(r"<[^>]+>", " ", no_scripts)
    return re.sub(r"\s+", " ", html.unescape(stripped)).strip()


def merge_restaurant_enrichment(
    base: dict[str, Any],
    incoming: dict[str, Any],
) -> dict[str, Any]:
    merged = normalize_restaurant_metadata(base)
    source = normalize_restaurant_metadata(incoming)
    for key, value in source.items():
        if key == "cuisine" and value:
            existing = dict(merged.get("cuisine") or {})
            for cuisine, detail in value.items():
                if cuisine not in existing or detail.get("value", 0) > existing[cuisine].get("value", 0):
                    existing[cuisine] = detail
            merged["cuisine"] = existing
        elif key not in merged or not merged.get(key):
            merged[key] = value
        elif key in {"michelin", "google"} and value:
            merged[key] = {**merged.get(key, {}), **{k: v for k, v in value.items() if v not in (None, "", [])}}
    return normalize_restaurant_metadata(merged)


def official_website_url(metadata: dict[str, Any]) -> str | None:
    for key in ("official_website_url", "official_url", "website", "url"):
        value = metadata.get(key)
        if isinstance(value, str) and is_http_url(value):
            return value
    return None


def fetch_json_url(url: str, *, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "brain-taste/0.1"})
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text_url(url: str, *, timeout: float) -> str:
    request = Request(url, headers={"Accept": "text/html", "User-Agent": "brain-taste/0.1"})
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return response.read().decode("utf-8", errors="replace")


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def checked_at() -> str:
    return datetime.now(UTC).isoformat()


def maps_search_url(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def redacted_google_key_url(url: str) -> str:
    return re.sub(r"([?&]key=)[^&]+", r"\1REDACTED", url)


def payload_without_key(payload: dict[str, Any], url: str) -> dict[str, Any]:
    return {"request_url": redacted_google_key_url(url), "payload": payload}


def clean_result_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
        match = re.search(r"(?:^|&)uddg=([^&]+)", parsed.query)
        if match:
            from urllib.parse import unquote

            return unquote(match.group(1))
    return url


def is_http_url(url: str | None) -> bool:
    parsed = urlparse(str(url or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_for_match(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def unique_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    result = []
    for source in sources:
        key = (str(source.get("name") or ""), str(source.get("url") or ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result
