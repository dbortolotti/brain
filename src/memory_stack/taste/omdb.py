from __future__ import annotations

import json
import os
import re
import ssl
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi

from .media import (
    empty_media_metadata,
    is_media_type,
    normalize_float,
    normalize_int,
    normalize_media_metadata,
)


OMDB_URL = "https://www.omdbapi.com/"


def fetch_omdb_metadata(
    *,
    title: str,
    entity_type: str,
    imdb_id: str | None = None,
    api_key: str | None = None,
    timeout: float = 10,
) -> dict[str, Any]:
    if not is_media_type(entity_type):
        return {"metadata": {}, "warnings": []}

    resolved_key = api_key if api_key is not None else (
        os.getenv("BRAIN_TASTE_OMDB_API_KEY") or os.getenv("OMDB_API_KEY")
    )
    if not resolved_key:
        return {
            "metadata": {},
            "warnings": [
                "BRAIN_TASTE_OMDB_API_KEY is not set; external ratings were not fetched."
            ],
        }

    params = {"apikey": resolved_key}
    if imdb_id:
        params["i"] = imdb_id
    else:
        params["t"] = title
        params["type"] = "movie" if entity_type == "movie" else "series"

    try:
        request = Request(
            f"{OMDB_URL}?{urlencode(params)}",
            headers={"Accept": "application/json", "User-Agent": "brain-taste/0.1"},
        )
        with urlopen(request, timeout=timeout, context=ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "metadata": {},
            "warnings": [f"OMDb lookup failed: {exc}"],
        }

    if str(payload.get("Response", "")).lower() == "false":
        return {
            "metadata": {},
            "warnings": [f"OMDb lookup failed: {payload.get('Error') or 'not found'}"],
        }

    metadata = omdb_payload_to_metadata(payload)
    warnings = []
    if not has_external_rating(metadata):
        warnings.append("OMDb returned no IMDb or Rotten Tomatoes rating.")
    return {"metadata": metadata, "warnings": warnings}


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def omdb_payload_to_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    fetched_at = datetime.now(UTC).isoformat()
    metadata = empty_media_metadata()

    metadata["synopsis"] = omdb_string(payload.get("Plot"))
    metadata["main_actors"] = omdb_list(payload.get("Actors"))
    metadata["director"] = omdb_string(payload.get("Director"))
    metadata["country"] = omdb_list(payload.get("Country"))
    metadata["language"] = omdb_list(payload.get("Language"))
    metadata["genre"] = omdb_list(payload.get("Genre"))
    metadata["runtime"] = payload.get("Runtime")
    metadata["seasons"] = payload.get("totalSeasons")
    metadata["external_ids"]["imdb_id"] = omdb_string(payload.get("imdbID"))
    metadata["external_ratings"]["imdb"]["rating"] = normalize_float(
        omdb_string(payload.get("imdbRating"))
    )
    metadata["external_ratings"]["imdb"]["votes"] = normalize_int(
        omdb_string(payload.get("imdbVotes"))
    )
    metadata["external_ratings"]["rotten_tomatoes"]["critic_score"] = (
        rotten_tomatoes_score(payload.get("Ratings"))
    )
    metadata["ratings_source"] = {"provider": "omdb", "fetched_at": fetched_at}
    return normalize_media_metadata(metadata)


def has_external_rating(metadata: dict[str, Any]) -> bool:
    return (
        metadata["external_ratings"]["imdb"]["rating"] is not None
        or metadata["external_ratings"]["rotten_tomatoes"]["critic_score"] is not None
    )


def rotten_tomatoes_score(ratings: Any) -> int | None:
    if not isinstance(ratings, list):
        return None

    for rating in ratings:
        if not isinstance(rating, dict):
            continue
        if rating.get("Source") != "Rotten Tomatoes":
            continue
        match = re.search(r"(\d{1,3})\s*%", str(rating.get("Value") or ""))
        if not match:
            return None
        return max(0, min(100, int(match.group(1))))

    return None


def omdb_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return None
    return text


def omdb_list(value: Any) -> list[str]:
    text = omdb_string(value)
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]
