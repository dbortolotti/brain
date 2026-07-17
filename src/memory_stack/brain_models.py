from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from memory_stack.domain_constants import SOURCE_KINDS


class EntityMention(BaseModel):
    name: str
    type: str
    role: str = "mentioned"
    alias: str | None = None
    confidence: str = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)

class RememberRequest(BaseModel):
    input: str
    input_type: str = "auto"
    dry_run: bool = False
    run_in_background: bool = False
    idempotency_key: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


SourceKind = Literal[*SOURCE_KINDS]


class IngestSourceRequest(BaseModel):
    source: str
    source_kind: SourceKind = "auto"
    title: str | None = None
    why_saved: str | None = None
    dry_run: bool = False
    run_in_background: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class EntityReceipt(BaseModel):
    id: str
    canonical_name: str
    type: str
    created: bool = True


class IngestionReceipt(BaseModel):
    ingestion_run_id: str
    classification: str
    entities: list[EntityReceipt] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    taste: dict[str, Any] = Field(default_factory=dict)
    cognee_sync_status: str = "not_applicable"
    dry_run: bool = False


class RecallRequest(BaseModel):
    query: str
    mode: str = "auto"
    include_superseded: bool = False
    include_conflicts: bool = True
    limit: int = 20


class RecallResponse(BaseModel):
    answer: str
    facts: list[dict[str, Any]] = Field(default_factory=list)
    inferences: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    taste: dict[str, Any] = Field(default_factory=dict)
