from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GoldenRecallQuery:
    id: str
    query: str
    expected_terms: set[str] = field(default_factory=set)
    mode: str = "auto"


GOLDEN_RECALL_QUERIES = [
    GoldenRecallQuery(
        id="sam_profile",
        query="Tell me everything about Sam from Goldman.",
        expected_terms={"Bill Evans", "Goldman"},
    ),
    GoldenRecallQuery(
        id="daughters",
        query="Who are my daughters?",
        expected_terms={"Nur", "Sara"},
    ),
    GoldenRecallQuery(
        id="knowledge_graph_open_questions",
        query="What open questions do I have about knowledge graphs?",
        expected_terms={"knowledge graphs"},
    ),
    GoldenRecallQuery(
        id="brain_cognee_conclusions",
        query="What did I conclude about Brain/Cognee?",
        expected_terms={"source of truth", "rebuildable"},
    ),
    GoldenRecallQuery(
        id="ai_memory_articles",
        query="What articles have I saved about AI memory?",
        expected_terms={"AI memory"},
    ),
    GoldenRecallQuery(
        id="sam_uncertain_or_stale",
        query="What facts about Sam are uncertain or stale?",
        expected_terms={"Goldman", "Point72"},
        mode="debug",
    ),
]
