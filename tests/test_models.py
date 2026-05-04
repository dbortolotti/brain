from __future__ import annotations

from memory_stack.io import load_memory_items


def test_sample_ingestion_text_contains_temporal_anchor() -> None:
    item = load_memory_items("data/samples/synthetic_property_emails.jsonl")[0]
    text = item.to_ingestion_text()
    assert "Origin-ID: email:melcombe:001" in text
    assert "Source-Sent-At: 2026-04-18T09:13:00+01:00" in text
    assert "Dataset: property_trial" in text

