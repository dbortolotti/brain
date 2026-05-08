from __future__ import annotations

from memory_stack.local_embeddings import fastembed_input_text


def test_fastembed_input_text_adds_e5_passage_prefix() -> None:
    assert (
        fastembed_input_text("intfloat/multilingual-e5-large", "brain memory")
        == "passage: brain memory"
    )


def test_fastembed_input_text_preserves_existing_e5_prefix() -> None:
    assert (
        fastembed_input_text("intfloat/multilingual-e5-large", "query: brain memory")
        == "query: brain memory"
    )


def test_fastembed_input_text_leaves_non_e5_models_unchanged() -> None:
    assert fastembed_input_text("BAAI/bge-small-en-v1.5", "brain memory") == "brain memory"
