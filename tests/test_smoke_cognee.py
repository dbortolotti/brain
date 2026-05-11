from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import smoke_cognee


def test_smoke_orchestrates_ingest_and_recall_without_live_cognee(monkeypatch) -> None:
    settings = SimpleNamespace(profile="openai")
    remembered: list[dict] = []
    recalls: list[dict] = []

    async def fake_remember_text(
        text,
        *,
        dataset_name,
        temporal,
        node_set,
        settings,
    ):
        remembered.append(
            {
                "text": text,
                "dataset_name": dataset_name,
                "temporal": temporal,
                "node_set": node_set,
                "settings": settings,
            }
        )

    async def fake_recall_text(**kwargs):
        recalls.append(kwargs)
        if kwargs["search_type"] == "TEMPORAL":
            return (
                "Jason confirmed Asbestech as Principal Designer. "
                "Irwin disagrees. The current position is to seek written confirmation."
            )
        return "Asbestech is involved in the Melcombe Court asbestos works."

    monkeypatch.setattr(smoke_cognee, "load_settings", lambda: settings)
    monkeypatch.setattr(smoke_cognee, "remember_text", fake_remember_text)
    monkeypatch.setattr(smoke_cognee, "recall_text", fake_recall_text)

    result = asyncio.run(smoke_cognee.run_smoke())

    expected_items = smoke_cognee.load_memory_items(smoke_cognee.SAMPLE)
    assert result == 0
    assert len(remembered) == len(expected_items)
    assert {item["dataset_name"] for item in remembered} == {"property_trial"}
    assert all(item["temporal"] is True for item in remembered)
    assert [call["search_type"] for call in recalls] == ["TEMPORAL", "GRAPH_COMPLETION"]
    assert all(call["settings"] is settings for call in recalls)


def test_smoke_returns_failure_when_ingest_fails(monkeypatch) -> None:
    settings = SimpleNamespace(profile="openai")

    async def fake_remember_text(*args, **kwargs):
        raise RuntimeError("ingest failed")

    monkeypatch.setattr(smoke_cognee, "load_settings", lambda: settings)
    monkeypatch.setattr(smoke_cognee, "remember_text", fake_remember_text)

    result = asyncio.run(smoke_cognee.run_smoke())

    assert result == 1
