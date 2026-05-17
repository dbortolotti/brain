from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def load_nightly_maintenance():
    path = Path("scripts/nightly_maintenance.py")
    spec = importlib.util.spec_from_file_location("nightly_maintenance", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nightly_maintenance_runs_backup_only_after_agent_memory_success(monkeypatch) -> None:
    module = load_nightly_maintenance()
    calls: list[list[str]] = []

    def fake_run(command, *, env, check):
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        module.sys,
        "argv",
        [
            "nightly_maintenance.py",
            "--env",
            "staging",
            "--env-file",
            "/tmp/brain.env",
            "--skip-google-drive",
        ],
    )

    assert module.main() == 0
    assert calls[0][1].endswith("brain_agent_memory.py")
    assert calls[0][-2:] == ["--env-file", "/tmp/brain.env"]
    assert calls[1][1].endswith("backup_stores.py")
    assert calls[1][-1] == "--skip-google-drive"


def test_nightly_maintenance_skips_backup_after_agent_memory_failure(monkeypatch) -> None:
    module = load_nightly_maintenance()
    calls: list[list[str]] = []

    def fake_run(command, *, env, check):
        calls.append(command)
        return SimpleNamespace(returncode=42)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.sys, "argv", ["nightly_maintenance.py", "--env", "prod"])

    assert module.main() == 42
    assert len(calls) == 1
    assert calls[0][1].endswith("brain_agent_memory.py")
