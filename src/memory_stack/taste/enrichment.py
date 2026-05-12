from __future__ import annotations

from typing import Any

from memory_stack.brain_store import now_utc
from memory_stack.config import Settings
from memory_stack.taste.media import (
    is_empty_metadata_value,
    is_media_type,
    is_music_type,
    is_restaurant_type,
    merge_media_metadata,
    merge_music_metadata,
    merge_restaurant_metadata,
    normalize_media_metadata,
    normalize_music_metadata,
    normalize_restaurant_metadata,
    set_media_field,
    set_music_field,
    set_restaurant_field,
)
from memory_stack.taste.omdb import fetch_omdb_metadata
from memory_stack.taste.restaurants import fetch_restaurant_enrichment
from memory_stack.taste.schema import ENTITY_TYPES, attribute_keys_for_type, invalid_attribute_keys
from memory_stack.taste.store import attribute_value, clamp01, normalize_interval_95


class TasteEnrichmentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def describe_item(
        self,
        *,
        item_text: str,
        entity_type: str,
        canonical_name: str | None = None,
        attributes: dict[str, Any] | None = None,
        attribute_intervals_95: dict[str, dict[str, float]] | None = None,
        metadata: dict[str, Any] | None = None,
        notes: str | None = None,
        fetch_external_ratings: bool = True,
        allow_broader_web_search: bool = False,
    ) -> dict[str, Any]:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"entity_type must be one of: {', '.join(ENTITY_TYPES)}")
        description = item_text.strip()
        if not description:
            raise ValueError("item_text is required and must not be blank.")
        name = (canonical_name or description).strip()
        if not name:
            raise ValueError("canonical_name must not be blank when provided.")

        ignored_attribute_keys = invalid_attribute_keys(entity_type, attributes)
        normalized_attributes = normalize_client_attributes(
            entity_type,
            attributes,
            attribute_intervals_95,
        )
        metadata_payload, metadata_warnings, sources, source_payloads = prepare_metadata(
            settings=self.settings,
            entity_type=entity_type,
            canonical_name=name,
            metadata=metadata or {},
            fetch_external_ratings=fetch_external_ratings,
            allow_broader_web_search=allow_broader_web_search,
        )
        status = "success"
        warnings = list(metadata_warnings)
        if ignored_attribute_keys:
            warnings.append(
                "Ignored attributes not valid for "
                f"{entity_type}: {', '.join(ignored_attribute_keys)}."
            )
        has_normalized_content = metadata_has_content(metadata_payload)
        if not normalized_attributes and not has_normalized_content:
            status = "failed" if fetch_external_ratings else "success"
            if self.settings.brain_taste_auto_enrich_enabled:
                if status == "failed":
                    warnings.append(
                        "No strict-source enrichment was available; confirmation is required "
                        "before storing a minimal user-input-only taste record."
                    )
                    warnings.append(
                        "Broader web search was not run automatically; ask explicitly to broaden search."
                    )
                else:
                    warnings.append(
                        "No strict-source enrichment was requested; using user input only."
                    )
        if allow_broader_web_search:
            warnings.append("Broader web search was explicitly approved for this enrichment request.")

        attribute_values = {
            key: attribute_value(value)
            for key, value in normalized_attributes.items()
        }
        intervals = {
            key: normalize_interval_95(attribute_value(value), value.get("interval_95"))
            for key, value in normalized_attributes.items()
            if isinstance(value, dict)
        }
        for key, value in attribute_values.items():
            intervals.setdefault(key, {"lower": value, "upper": value})

        return {
            "canonical_name": name,
            "entity_type": entity_type,
            "normalized_metadata": metadata_payload,
            "attributes": attribute_values,
            "attribute_intervals_95": intervals,
            "enrichment_metadata": {
                "normalized_fields_source": "strict_source"
                if has_normalized_content
                else "user_input_only",
                "warnings": warnings,
                "ignored_attribute_keys": ignored_attribute_keys,
                "checked_at": now_utc().isoformat(),
                "source_payloads": source_payloads,
            },
            "sources": sources,
            "warnings": warnings,
            "confidence": 1.0 if status == "success" else 0.6,
            "enrichment_status": status,
            "notes": notes or description,
        }


def normalize_client_attributes(
    entity_type: str,
    attributes: dict[str, Any] | None,
    attribute_intervals_95: dict[str, dict[str, float]] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(attributes, dict):
        return {}
    allowed = set(attribute_keys_for_type(entity_type))
    intervals = attribute_intervals_95 if isinstance(attribute_intervals_95, dict) else {}
    normalized = {}
    for key, value in attributes.items():
        if key not in allowed:
            continue
        try:
            point = clamp01(attribute_value(value))
        except (TypeError, ValueError):
            continue
        interval = intervals.get(key) if isinstance(intervals.get(key), dict) else None
        if isinstance(value, dict) and interval is None:
            interval = value.get("interval_95") or value
        normalized[key] = {
            "value": point,
            "interval_95": normalize_interval_95(point, interval),
        }
    return normalized


def prepare_metadata(
    *,
    settings: Settings,
    entity_type: str,
    canonical_name: str,
    metadata: dict[str, Any],
    fetch_external_ratings: bool,
    allow_broader_web_search: bool = False,
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]], dict[str, Any]]:
    if is_music_type(entity_type):
        return merge_music_metadata(normalize_music_metadata(metadata), {}), [], [], {}
    if is_restaurant_type(entity_type):
        normalized = normalize_restaurant_metadata(metadata)
        if fetch_external_ratings:
            lookup = fetch_restaurant_enrichment(
                canonical_name=canonical_name,
                metadata=metadata,
                settings=settings,
                allow_broader_web_search=allow_broader_web_search,
            )
            normalized = merge_restaurant_metadata(normalized, lookup["metadata"])
            return (
                normalized,
                lookup["warnings"],
                lookup["sources"],
                lookup["source_payloads"],
            )
        return merge_restaurant_metadata(normalized, {}), [], [], {}
    if is_media_type(entity_type):
        normalized = normalize_media_metadata(metadata)
        warnings = []
        sources: list[dict[str, Any]] = []
        source_payloads: dict[str, Any] = {}
        if fetch_external_ratings:
            lookup = fetch_omdb_metadata(
                title=canonical_name,
                entity_type=entity_type,
                imdb_id=(normalized.get("external_ids") or {}).get("imdb_id"),
                api_key=settings.brain_taste_omdb_api_key,
            )
            warnings.extend(lookup["warnings"])
            normalized = merge_media_metadata(normalized, lookup["metadata"])
            if lookup["metadata"]:
                sources.append({"name": "omdb", "url": "https://www.omdbapi.com/", "source_quality": "strict"})
                source_payloads["omdb"] = {"looked_up": True}
        return normalized, warnings, sources, source_payloads
    return metadata or {}, [], [], {}


def metadata_has_content(metadata: dict[str, Any] | None) -> bool:
    if not isinstance(metadata, dict) or not metadata:
        return False
    for value in metadata.values():
        if isinstance(value, dict):
            if metadata_has_content(value):
                return True
            continue
        if isinstance(value, list):
            if any(not is_empty_metadata_value(item) for item in value):
                return True
            continue
        if not is_empty_metadata_value(value):
            return True
    return False


def merge_manual_metadata(entity_type: str, base: dict[str, Any], manual: dict[str, Any]) -> dict[str, Any]:
    if is_media_type(entity_type):
        merged = normalize_media_metadata(base)
        for key, value in manual.items():
            if value is not None:
                merged = set_media_field(merged, tuple(str(key).split(".")), value)
        return merged
    if is_music_type(entity_type):
        merged = normalize_music_metadata(base)
        for key, value in manual.items():
            if value is not None:
                merged = set_music_field(merged, tuple(str(key).split(".")), value)
        return merged
    if is_restaurant_type(entity_type):
        merged = normalize_restaurant_metadata(base)
        for key, value in manual.items():
            if value is not None:
                merged = set_restaurant_field(merged, tuple(str(key).split(".")), value)
        return merged
    return {**base, **{key: value for key, value in manual.items() if value is not None}}
