from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    origin_id: str
    source_type: Literal["email", "note", "manual", "document"]
    source_sent_at: datetime
    source_from: str | None = None
    thread_id: str
    dataset_name: str
    title: str | None = None
    body: str
    tags: list[str] = Field(default_factory=list)

    def to_ingestion_text(self) -> str:
        return f"""
Origin-ID: {self.origin_id}
Source-Type: {self.source_type}
Source-Sent-At: {self.source_sent_at.isoformat()}
Source-From: {self.source_from or ""}
Thread: {self.thread_id}
Dataset: {self.dataset_name}
Tags: {", ".join(self.tags)}

Title:
{self.title or ""}

Body:
{self.body}
""".strip()


class EvalQuery(BaseModel):
    id: str
    dataset: str
    search_type: str
    query: str
    must_include: list[str] = Field(default_factory=list)
    rubric: dict[str, float] = Field(default_factory=dict)

