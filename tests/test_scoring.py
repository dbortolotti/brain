from __future__ import annotations

from memory_stack.scoring import score_result


def test_must_include_scoring() -> None:
    score = score_result("Asbestech and Irwin discussed the Principal Designer role.", [
        "Asbestech",
        "Irwin",
        "Principal Designer",
    ])
    assert score["score"] == 1.0
    assert score["missing"] == []

