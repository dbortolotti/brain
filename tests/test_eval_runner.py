from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from types import SimpleNamespace

from memory_stack import eval_runner
from memory_stack.eval_runner import raw_result_path


def test_raw_result_path_is_collision_resistant_for_same_timestamp_and_query() -> None:
    raw_dir = Path("eval/results/raw")
    timestamp = "2026-05-05T12:34:56.123456"

    first = raw_result_path(raw_dir, timestamp, "duplicate_id", 1)
    second = raw_result_path(raw_dir, timestamp, "duplicate_id", 2)

    assert first != second
    assert first.name == "2026-05-05T123456123456_001_duplicate_id.json"
    assert second.name == "2026-05-05T123456123456_002_duplicate_id.json"


def test_run_eval_writes_csv_and_raw_results_without_live_cognee(
    tmp_path, monkeypatch
) -> None:
    queries_path = tmp_path / "queries.yaml"
    queries_path.write_text(
        """
queries:
  - id: current_pd_position
    dataset: property_trial
    search_type: TEMPORAL
    query: "What is our current Principal Designer position?"
    must_include:
      - "Principal Designer"
      - "Asbestech"
      - "Irwin"
""".lstrip(),
        encoding="utf-8",
    )
    output_path = tmp_path / "results" / "results.csv"
    settings = SimpleNamespace(
        profile="gemini",
        llm_provider="gemini",
        llm_model="gemini/gemini-3.1-flash-lite-preview",
        embedding_provider="gemini",
        embedding_model="gemini/gemini-embedding-001",
    )
    calls: list[dict] = []

    async def fake_recall_text(**kwargs):
        calls.append(kwargs)
        return "Asbestech, Irwin, and Principal Designer context."

    monkeypatch.setattr(eval_runner, "load_settings", lambda: settings)
    monkeypatch.setattr(eval_runner, "recall_text", fake_recall_text)

    rows = asyncio.run(eval_runner.run_eval(str(queries_path), str(output_path), top_k=7))

    assert len(rows) == 1
    assert calls[0]["query"] == "What is our current Principal Designer position?"
    assert calls[0]["dataset"] == "property_trial"
    assert calls[0]["search_type"] == "TEMPORAL"
    assert calls[0]["top_k"] == 7

    raw_path = Path(rows[0]["raw_result_path"])
    assert raw_path.exists()
    raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw_payload["query"]["id"] == "current_pd_position"
    assert raw_payload["result"] == "Asbestech, Irwin, and Principal Designer context."

    with output_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert csv_rows[0]["profile"] == "gemini"
    assert csv_rows[0]["score"] == "1.0"
