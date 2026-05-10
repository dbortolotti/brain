from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "brain_eval_monitor.py"
SPEC = importlib.util.spec_from_file_location("brain_eval_monitor", SCRIPT_PATH)
assert SPEC is not None
brain_eval_monitor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(brain_eval_monitor)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_live_monitor_labels_raw_provider_counts_before_scored_results(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    raw_dir = run_dir / "raw"
    write_json(
        raw_dir / "ok.json",
        {
            "status": "ok",
            "model": "openai:test",
            "role": "intent_router",
            "fixture_id": "fixture_ok",
        },
    )
    write_json(
        raw_dir / "fail.json",
        {
            "status": "fail",
            "model": "openai:test",
            "role": "intent_router",
            "fixture_id": "fixture_fail",
        },
    )
    (run_dir / "run.log").write_text("progress 2/10 openai:test intent_router fixture_fail status=fail\n")

    brain_eval_monitor.write_once(run_dir, run_dir / "results.json", raw_dir)

    live_status = json.loads((run_dir / "live_status.json").read_text(encoding="utf-8"))
    html = (run_dir / "index.html").read_text(encoding="utf-8")

    assert live_status["status_counts_source"] == "raw_provider_outputs"
    assert live_status["status_counts"] == {"fail": 1, "ok": 1}
    assert "Provider failures" in html
    assert "Raw provider Status Counts" in html
    assert "Quality, schema, and zero-tolerance scoring will appear after results.json is written." in html
    assert "Scored failures" not in html


def test_live_monitor_uses_scored_results_when_available(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    raw_dir = run_dir / "raw"
    write_json(
        raw_dir / "raw_ok.json",
        {
            "status": "ok",
            "model": "openai:test",
            "role": "intent_router",
            "fixture_id": "fixture_raw",
        },
    )
    write_json(
        run_dir / "results.json",
        [
            {
                "status": "ok",
                "failure_class": "none",
                "model": "openai:test",
                "role": "intent_router",
                "fixture_id": "fixture_ok",
            },
            {
                "status": "quality_fail",
                "failure_class": "quality_failure",
                "model": "openai:test",
                "role": "intent_router",
                "fixture_id": "fixture_quality",
            },
        ],
    )

    brain_eval_monitor.write_once(run_dir, run_dir / "results.json", raw_dir)

    live_status = json.loads((run_dir / "live_status.json").read_text(encoding="utf-8"))
    html = (run_dir / "index.html").read_text(encoding="utf-8")

    assert live_status["status_counts_source"] == "scored_results"
    assert live_status["status_counts"] == {"ok": 1, "quality_fail": 1}
    assert "Scored failures" in html
    assert "Scored Status Counts" in html
    assert "Final scored results loaded from results.json." in html
    assert "Provider failures" not in html
