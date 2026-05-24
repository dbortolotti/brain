from __future__ import annotations

import json
from typing import Any

from memory_stack.llm.client import LLMClient
from memory_stack.taste.media import MEDIA_GENRES, MICHELIN_STATUSES, MUSIC_GENRES, RESTAURANT_GENRES
from memory_stack.taste.schema import ATTRIBUTE_KEYS_BY_TYPE, ENTITY_TYPES, attribute_keys_for_type


def normalize_enrichment_with_llm(
    *,
    item_text: str,
    entity_type: str,
    llm_client: LLMClient,
    model: str | None = None,
    reasoning_effort: str | None = None,
    use_web_search: bool = False,
) -> dict[str, Any]:
    allowed_attributes = attribute_keys_for_type(entity_type)
    instructions = [
        "Normalize noisy descriptive text into Brain Taste's fixed attribute schema for the given entity type.",
        "Never invent new attribute keys.",
        "Each attribute must include value and interval_iqr.",
        "Each value must be in [0, 1]. Use 0 when not evidenced.",
        "Each interval_iqr is the interquartile range for the true attribute value, using p25 lower and p75 upper bounds.",
        "Each interval_iqr must include the value and stay within [0, 1].",
        "Use a narrow IQR when evidence is explicit and a wide IQR when weak or absent.",
        "For movie or series items, extract only explicitly evidenced media metadata.",
        "For music items, extract only explicitly evidenced music metadata.",
        "For restaurant items, extract explicitly evidenced cuisine as scored metadata cuisine.",
        "Use canonical cuisine values exactly as provided by the schema.",
        "For restaurant cuisine, use 0 when not evidenced and use other only when no listed cuisine category fits at 40% confidence.",
        "For restaurant Michelin metadata, use only explicitly evidenced official Michelin Guide information.",
        "Set Michelin status to unknown when an official Michelin source is not provided.",
        "For restaurant Google metadata, use only directly evidenced Google Maps, Google Business Profile, or Google Places data.",
        "Set Google rating and rating_count to null when no direct Google source is provided.",
        "Do not invent external ratings, external IDs, or watched status.",
    ]
    if use_web_search:
        instructions.extend(
            [
                "Use current web sources to identify the item before scoring attributes.",
                "For wine, use producer, cuvee, region, vintage, grape, and critic or merchant notes when available.",
                "If web evidence is weak, return wide intervals rather than empty attributes.",
            ]
        )
    prompt = json.dumps(
        {
            "instructions": instructions,
            "payload": {
                "item_text": item_text,
                "entity_type": entity_type,
                "allowed_entity_types": ENTITY_TYPES,
                "allowed_attributes": allowed_attributes,
                "allowed_attributes_by_type": ATTRIBUTE_KEYS_BY_TYPE,
                "allowed_media_genres": MEDIA_GENRES,
                "allowed_music_genres": MUSIC_GENRES,
                "allowed_restaurant_genres": RESTAURANT_GENRES,
                "allowed_michelin_statuses": MICHELIN_STATUSES,
            },
        },
        sort_keys=True,
    )
    kwargs: dict[str, Any] = {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "temperature": 0,
    }
    if use_web_search:
        kwargs.update(
            tools=[
                {
                    "type": "web_search",
                    "user_location": {
                        "type": "approximate",
                        "country": "GB",
                        "city": "London",
                        "region": "London",
                        "timezone": "Europe/London",
                    },
                }
            ],
            tool_choice="auto",
            include=["web_search_call.action.sources"],
            schema_name=f"brain_{entity_type}_web_enrichment",
        )
    return llm_client.complete_json(
        prompt,
        enrichment_schema_for_type(entity_type),
        **kwargs,
    )


def normalize_restaurant_enrichment_with_llm(
    *,
    item_text: str,
    llm_client: LLMClient,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    allowed_attributes = attribute_keys_for_type("restaurant")
    prompt = json.dumps(
        {
            "instructions": [
                "Research the restaurant using current web sources, then normalize it into Brain Taste's fixed restaurant attribute schema.",
                "Use the web for venue facts such as cuisine, menu, neighborhood, price tier, ambiance, and setting.",
                "Use official guide.michelin.com pages for Michelin status.",
                "Use Google Maps, Google Business Profile, or Google Places data for Google rating and rating_count.",
                "Never invent new attribute keys.",
                "Each attribute must include value and interval_iqr.",
                "Each value must be in [0, 1]. Use 0 when not evidenced.",
                "Each interval_iqr is the interquartile range for the true attribute value, using p25 lower and p75 upper bounds.",
                "Each interval_iqr must include the value and stay within [0, 1].",
                "Use a narrow IQR when web evidence is explicit and a wide IQR when weak or absent.",
                "Extract explicitly evidenced cuisine as scored metadata cuisine.",
                "Use canonical cuisine values exactly as provided by the schema.",
                "For restaurant cuisine, use 0 when not evidenced and use other only when no listed cuisine category fits at 40% confidence.",
                "Extract Michelin status only from official guide.michelin.com sources.",
                "Set Michelin status to unknown when no official Michelin source is found; do not infer not_listed from generic web absence.",
                "Extract Google rating and rating_count only from direct Google sources; do not copy third-party review-site ratings.",
                "Set Google rating and rating_count to null when no direct Google source is found.",
                "Mention the web facts that drove the scores in notes, without copying long source text.",
            ],
            "payload": {
                "item_text": item_text,
                "entity_type": "restaurant",
                "allowed_attributes": allowed_attributes,
                "allowed_restaurant_genres": RESTAURANT_GENRES,
                "allowed_michelin_statuses": MICHELIN_STATUSES,
            },
        },
        sort_keys=True,
    )
    return llm_client.complete_json(
        prompt,
        restaurant_web_enrichment_schema(),
        model=model,
        reasoning_effort=reasoning_effort,
        temperature=0,
        tools=[
            {
                "type": "web_search",
                "user_location": {
                    "type": "approximate",
                    "country": "GB",
                    "city": "London",
                    "region": "London",
                    "timezone": "Europe/London",
                },
            }
        ],
        tool_choice="auto",
        include=["web_search_call.action.sources"],
        schema_name="brain_restaurant_web_enrichment",
    )


def enrichment_schema_for_type(entity_type: str) -> dict[str, Any]:
    allowed_attributes = attribute_keys_for_type(entity_type)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["attributes", "notes", "metadata"],
        "properties": {
            "attributes": {
                "type": "object",
                "additionalProperties": False,
                "required": allowed_attributes,
                "properties": {
                    key: attribute_value_schema()
                    for key in allowed_attributes
                },
            },
            "notes": {"type": "string"},
            "metadata": metadata_schema_for_type(entity_type),
        },
    }


def attribute_value_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["value", "interval_iqr"],
        "properties": {
            "value": {"type": "number", "minimum": 0, "maximum": 1},
            "interval_iqr": confidence_interval_schema(),
        },
    }


def sigma_attribute_value_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["value", "interval_iqr"],
        "properties": {
            "value": {"type": "number", "minimum": 0, "maximum": 1},
            "interval_iqr": confidence_interval_schema(),
        },
    }


def confidence_interval_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["lower", "upper"],
        "properties": {
            "lower": {"type": "number", "minimum": 0, "maximum": 1},
            "upper": {"type": "number", "minimum": 0, "maximum": 1},
        },
    }


def metadata_schema_for_type(entity_type: str) -> dict[str, Any]:
    if entity_type in {"movie", "series"}:
        return media_metadata_schema()
    if entity_type == "music":
        return music_metadata_schema()
    if entity_type == "restaurant":
        return restaurant_metadata_schema()
    return empty_metadata_schema()


def empty_metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [],
        "properties": {},
    }


def music_metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["artist", "album", "personnel", "genre"],
        "properties": {
            "artist": {"type": ["string", "null"]},
            "album": {"type": ["string", "null"]},
            "personnel": {"type": "array", "items": {"type": "string"}},
            "genre": {
                "type": "array",
                "items": {"type": "string", "enum": MUSIC_GENRES},
            },
        },
    }


def restaurant_metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["cuisine", "michelin", "google"],
        "properties": {
            "cuisine": {
                "type": "object",
                "additionalProperties": False,
                "required": RESTAURANT_GENRES,
                "properties": {
                    key: attribute_value_schema()
                    for key in RESTAURANT_GENRES
                },
            },
            "michelin": michelin_metadata_schema(),
            "google": google_rating_metadata_schema(),
        },
    }


def restaurant_web_enrichment_schema() -> dict[str, Any]:
    allowed_attributes = attribute_keys_for_type("restaurant")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["attributes", "notes", "metadata"],
        "properties": {
            "attributes": {
                "type": "object",
                "additionalProperties": False,
                "required": allowed_attributes,
                "properties": {
                    key: sigma_attribute_value_schema()
                    for key in allowed_attributes
                },
            },
            "notes": {"type": "string"},
            "metadata": restaurant_metadata_schema(),
        },
    }


def michelin_metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "status",
            "stars",
            "green_star",
            "source_url",
            "source",
            "checked_at",
        ],
        "properties": {
            "status": {"type": "string", "enum": MICHELIN_STATUSES},
            "stars": {"type": ["integer", "null"], "minimum": 0, "maximum": 3},
            "green_star": {"type": "boolean"},
            "source_url": {"type": ["string", "null"]},
            "source": {"type": ["string", "null"]},
            "checked_at": {"type": ["string", "null"]},
        },
    }


def google_rating_metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "rating",
            "rating_count",
            "source_url",
            "source",
            "checked_at",
        ],
        "properties": {
            "rating": {"type": ["number", "null"], "minimum": 0, "maximum": 5},
            "rating_count": {"type": ["integer", "null"], "minimum": 0},
            "source_url": {"type": ["string", "null"]},
            "source": {"type": ["string", "null"]},
            "checked_at": {"type": ["string", "null"]},
        },
    }


def media_metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "synopsis",
            "main_actors",
            "director",
            "country",
            "language",
            "genre",
            "runtime",
            "seasons",
            "watched",
            "watched_at",
            "external_ids",
            "external_ratings",
            "ratings_source",
        ],
        "properties": {
            "synopsis": {"type": ["string", "null"]},
            "main_actors": {"type": "array", "items": {"type": "string"}},
            "director": {"type": ["string", "null"]},
            "country": {"type": "array", "items": {"type": "string"}},
            "language": {"type": "array", "items": {"type": "string"}},
            "genre": {
                "type": "array",
                "items": {"type": "string", "enum": MEDIA_GENRES},
            },
            "runtime": {"type": ["integer", "null"], "minimum": 0},
            "seasons": {"type": ["integer", "null"], "minimum": 0},
            "watched": {"type": "boolean"},
            "watched_at": {"type": ["string", "null"]},
            "external_ids": {
                "type": "object",
                "additionalProperties": False,
                "required": ["imdb_id"],
                "properties": {"imdb_id": {"type": ["string", "null"]}},
            },
            "external_ratings": {
                "type": "object",
                "additionalProperties": False,
                "required": ["imdb", "rotten_tomatoes"],
                "properties": {
                    "imdb": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["rating", "votes"],
                        "properties": {
                            "rating": {"type": ["number", "null"]},
                            "votes": {"type": ["integer", "null"]},
                        },
                    },
                    "rotten_tomatoes": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["critic_score"],
                        "properties": {
                            "critic_score": {"type": ["integer", "null"]},
                        },
                    },
                },
            },
            "ratings_source": {
                "type": "object",
                "additionalProperties": False,
                "required": ["provider", "fetched_at"],
                "properties": {
                    "provider": {"type": ["string", "null"]},
                    "fetched_at": {"type": ["string", "null"]},
                },
            },
        },
    }
