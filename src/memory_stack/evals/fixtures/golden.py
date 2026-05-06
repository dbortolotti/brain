from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GoldenFixture:
    id: str
    input: str
    input_type: str = "auto"
    source_kind: str | None = None
    title: str | None = None
    why_saved: str | None = None
    expected_kinds: set[str] = field(default_factory=set)
    expected_terms: set[str] = field(default_factory=set)


LONG_CHAT_SUMMARY = """
# Brain/Cognee design chat

We concluded Brain DB should remain the source of truth. Cognee should be a
rebuildable projection for semantic search. Open question: how much source text
should be projected into the memory dataset?
""".strip()


ARTICLE_TEXT = """
AI memory systems need durable source evidence. Atomic memory cards should be
small and traceable. A semantic index can improve recall, but the application DB
must own lifecycle and conflict state.
""".strip()


PREFERENCE_TABLE = "\n".join(
    [
        "| Person | Preference |",
        "| --- | --- |",
        "| Sam | Bill Evans |",
        "| Daniele | Knowledge graphs |",
    ]
)


TRANSCRIPT = "\n".join(
    [
        "Daniele: Brain DB remains source of truth.",
        "Sam: Cognee should stay rebuildable.",
        "Daniele: Add source-backed recall next.",
    ]
)


GOLDEN_INGESTION_FIXTURES = [
    GoldenFixture(
        id="family_twins",
        input="Nur and Sara are my twin daughters.",
        expected_kinds={"family_fact"},
        expected_terms={"Nur", "Sara"},
    ),
    GoldenFixture(
        id="sam_goldman_jazz",
        input="Sam from Goldman mentioned that he likes Bill Evans.",
        expected_kinds={"person_interaction"},
        expected_terms={"Sam", "Goldman", "Bill Evans"},
    ),
    GoldenFixture(
        id="knowledge_graph_open_loop",
        input="I want to learn more about knowledge graphs.",
        expected_kinds={"open_question"},
        expected_terms={"knowledge graphs"},
    ),
    GoldenFixture(
        id="long_chat_summary",
        input=LONG_CHAT_SUMMARY,
        source_kind="markdown",
        title="Brain/Cognee design chat",
        expected_kinds={"source_summary"},
        expected_terms={"source of truth", "Cognee"},
    ),
    GoldenFixture(
        id="article_ai_memory",
        input=ARTICLE_TEXT,
        source_kind="article",
        title="AI memory design",
        why_saved="Useful for AI memory design.",
        expected_kinds={"article_note"},
        expected_terms={"AI memory", "source evidence"},
    ),
    GoldenFixture(
        id="preference_table",
        input=PREFERENCE_TABLE,
        source_kind="table",
        title="Preferences",
        expected_kinds={"table_note"},
        expected_terms={"Bill Evans", "Knowledge graphs"},
    ),
    GoldenFixture(
        id="sam_transition",
        input="Sam works at Goldman.",
        expected_kinds={"person_fact"},
        expected_terms={"Goldman"},
    ),
    GoldenFixture(
        id="sam_transition_update",
        input="Sam left Goldman and joined Point72.",
        expected_kinds={"person_fact"},
        expected_terms={"Point72"},
    ),
    GoldenFixture(
        id="brain_transcript",
        input=TRANSCRIPT,
        source_kind="transcript",
        title="Brain sync transcript",
        expected_kinds={"source_summary"},
        expected_terms={"Brain", "Cognee"},
    ),
]
