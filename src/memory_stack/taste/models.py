from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TasteDescribeRequest(BaseModel):
    item_text: str
    entity_type: str
    canonical_name: str | None = None
    attributes: dict[str, Any] | None = None
    attribute_intervals_iqr: dict[str, dict[str, float]] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    fetch_external_ratings: bool = True
    allow_broader_web_search: bool = False


class TasteRememberRequest(BaseModel):
    id: str | None = None
    type: str
    canonical_name: str
    description: str
    attributes: dict[str, Any] | None = None
    attribute_intervals_iqr: dict[str, dict[str, float]] | None = None
    rating: float | None = None
    tried: bool | None = None
    watched: bool | None = None
    listened: bool | None = None
    wanted: bool | None = None
    recommended_by: str | None = None
    disliked: bool | None = None
    avoid: bool | None = None
    not_my_style: bool | None = None
    bad_fit: bool | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = "user"
    dry_run: bool = False
    store_anyway: bool = False
    context: dict[str, Any] = Field(default_factory=dict)
    fetch_external_ratings: bool = True
    allow_broader_web_search: bool = False


class TasteQueryRequest(BaseModel):
    query: str
    context: dict[str, Any] = Field(default_factory=dict)
    options_text: str | None = None
    explain: bool = False
    intent: dict[str, Any] | None = None
    extracted_entities: list[dict[str, Any]] | None = None


class TasteLogDecisionRequest(BaseModel):
    chosen_taste_item_id: str
    decision_id: str | None = None
    query: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class TasteRefreshRequest(BaseModel):
    taste_item_id: str
