from __future__ import annotations

from types import SimpleNamespace

from memory_stack.recall.retriever import raw_memories_from_cognee_result


def test_raw_memories_extracts_text_from_cognee_response_objects() -> None:
    result = [
        SimpleNamespace(text="First remembered fact."),
        SimpleNamespace(text="Second remembered fact."),
    ]

    memories = raw_memories_from_cognee_result(result, limit=5)

    assert [memory["statement"] for memory in memories] == [
        "First remembered fact.",
        "Second remembered fact.",
    ]
