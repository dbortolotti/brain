from __future__ import annotations

from pathlib import Path

from memory_stack import eval_cases, eval_runner, ingest_cognee, recall_cognee
from memory_stack.evals.fixtures import GOLDEN_INGESTION_FIXTURES


def test_readme_is_brain_first_and_marks_legacy_tools() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert readme.startswith("# Brain\n\nBrain is a local personal memory control plane")
    assert "Legacy Cognee Eval Tools" in readme
    assert "src/memory_stack/evals/" in readme


def test_legacy_modules_are_explicitly_marked_and_still_importable() -> None:
    for module in [eval_cases, eval_runner, ingest_cognee, recall_cognee]:
        assert module.__doc__ is not None
        assert "Legacy" in module.__doc__


def test_useful_legacy_eval_ideas_are_ported_to_brain_fixtures() -> None:
    fixture_ids = {fixture.id for fixture in GOLDEN_INGESTION_FIXTURES}

    assert {
        "family_twins",
        "sam_goldman_jazz",
        "knowledge_graph_open_loop",
        "preference_table",
    } <= fixture_ids
