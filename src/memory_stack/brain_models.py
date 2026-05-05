from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


MemoryKind = Literal[
    "basic_fact",
    "family_fact",
    "person_fact",
    "person_interaction",
    "preference",
    "decision",
    "idea",
    "open_question",
    "research_question",
    "article_note",
    "key_takeaway",
    "conversation_summary",
    "chat_conclusion",
    "experience",
    "place_note",
    "table_note",
    "source_summary",
    "project_state",
    "commitment",
]


class EntityMention(BaseModel):
    name: str
    type: str
    role: str = "mentioned"
    alias: str | None = None
    confidence: str = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipCandidate(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: str = "medium"
    status: str = "current"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceCandidate(BaseModel):
    kind: str
    title: str | None = None
    uri: str | None = None
    file_path: str | None = None
    raw_text: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = "processed"


class MemoryCandidate(BaseModel):
    kind: MemoryKind | str
    statement: str
    summary: str | None = None
    confidence: str = "medium"
    status: str = "current"
    observed_at: datetime | None = None
    source_quote: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    entities: list[EntityMention] = Field(default_factory=list)
    relationships: list[RelationshipCandidate] = Field(default_factory=list)
    open_loop: dict[str, Any] | None = None


class RememberRequest(BaseModel):
    input: str
    input_type: str = "auto"
    observed_at: datetime | None = None
    source_policy: str = "auto"
    dry_run: bool = False
    context: dict[str, Any] = Field(default_factory=dict)


class SourceReceipt(BaseModel):
    created: bool
    source_id: str | None = None


class MemoryReceipt(BaseModel):
    id: str
    kind: str
    statement: str
    status: str
    created: bool = True


class EntityReceipt(BaseModel):
    id: str
    canonical_name: str
    type: str
    created: bool = True


class IngestionReceipt(BaseModel):
    ingestion_run_id: str
    classification: str
    source: SourceReceipt = Field(default_factory=lambda: SourceReceipt(created=False))
    memory_cards: list[MemoryReceipt] = Field(default_factory=list)
    entities: list[EntityReceipt] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    open_loops: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    cognee_sync_status: str = "pending"
    dry_run: bool = False


class RecallRequest(BaseModel):
    query: str
    mode: str = "auto"
    include_sources: bool = True
    include_superseded: bool = False
    limit: int = 20


class RecallResponse(BaseModel):
    answer: str
    facts: list[dict[str, Any]] = Field(default_factory=list)
    inferences: list[dict[str, Any]] = Field(default_factory=list)
    open_loops: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
