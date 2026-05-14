from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent


def load_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_organic_recall_fixture_has_100_balanced_cases() -> None:
    payload = load_json("organic_recall_100_cases.json")

    seed_inserts = payload["seed_inserts"]
    recall_cases = payload["recall_cases"]
    seed_ids = {item["id"] for item in seed_inserts}
    case_ids = {case["id"] for case in recall_cases}

    assert len(seed_inserts) >= 40
    assert len(seed_ids) == len(seed_inserts)
    assert len(recall_cases) == 100
    assert len(case_ids) == 100
    assert Counter(case["difficulty"] for case in recall_cases) == {
        1: 20,
        2: 20,
        3: 20,
        4: 20,
        5: 20,
    }

    for seed in seed_inserts:
        assert seed["write_path"] in {"remember", "ingest_source"}
        assert seed["input"].strip()
        assert seed["expected_terms"]
        assert seed["status"] in {
            "current",
            "deleted",
            "superseded",
            "open_loop_open",
            "open_loop_closed",
        }

    for case in recall_cases:
        assert case["query"].strip()
        assert case["mode"] in {"auto", "open_loops"}
        assert case["expected"]["must_include"]
        assert "must_not_include" in case["expected"]
        assert case["expected"]["citations_required"] is True
        assert case["relevant_seed_ids"]
        assert set(case["relevant_seed_ids"]) <= seed_ids


def test_manetti_questions_and_document_are_stored_with_fixture_set() -> None:
    questions_payload = load_json("manetti_100_questions.json")
    questions = questions_payload["questions"]
    question_ids = {question["question_id"] for question in questions}
    document = (FIXTURE_DIR / "manetti_document.md").read_text(encoding="utf-8")

    assert len(questions) == 100
    assert len(question_ids) == 100
    assert questions[0]["question_id"] == "mbq001"
    assert questions[-1]["question_id"] == "mbq100"
    assert Counter(question["difficulty"] for question in questions) == {
        1: 20,
        2: 20,
        3: 20,
        4: 20,
        5: 20,
    }
    assert "CHI SONO IO?" in document
    assert "NARRAZIONE STORICA" in document
    assert "La camicia bruciata" in document
