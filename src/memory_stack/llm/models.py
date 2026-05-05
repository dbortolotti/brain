from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Confidence = Literal["low", "medium", "high"]


class LLMCompilerEntity(BaseModel):
    name: str
    type: str
    role: str = "mentioned"
    alias: str | None = None
    confidence: Confidence = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCompilerRelationship(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: Confidence = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCompilerSource(BaseModel):
    should_create: bool = False
    kind: str = "other"
    title: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCompilerMemoryCard(BaseModel):
    kind: str
    statement: str
    summary: str | None = None
    entities: list[LLMCompilerEntity] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    relationships: list[LLMCompilerRelationship] = Field(default_factory=list)
    confidence: Confidence = "medium"
    observed_at: str | None = None
    source_quote: str | None = None
    open_loop: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCompilerOutput(BaseModel):
    classification: str
    source: LLMCompilerSource = Field(default_factory=LLMCompilerSource)
    memory_cards: list[LLMCompilerMemoryCard] = Field(default_factory=list)
    possible_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    questions_for_user: list[str] = Field(default_factory=list)


def compiler_output_schema() -> dict[str, Any]:
    return LLMCompilerOutput.model_json_schema()
