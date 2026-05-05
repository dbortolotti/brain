from __future__ import annotations

import pytest
import typer

from memory_stack.recall_cognee import parse_search_type


def test_parse_search_type_normalizes_known_values() -> None:
    assert parse_search_type("temporal") == "TEMPORAL"
    assert parse_search_type(" graph_completion ") == "GRAPH_COMPLETION"


def test_parse_search_type_rejects_unknown_values() -> None:
    with pytest.raises(typer.BadParameter, match="Unknown search type"):
        parse_search_type("not-a-search-mode")
