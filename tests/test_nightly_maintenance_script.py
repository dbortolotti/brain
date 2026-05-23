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


def test_nightly_maintenance_runs_backup(monkeypatch) -> None:
    module = load_nightly_maintenance()
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(command, *, env, check):
        calls.append((command, env))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        module.sys,
        "argv",
        [
            "nightly_maintenance.py",
            "--env-file",
            "/tmp/brain.env",
            "--skip-google-drive",
        ],
    )

    assert module.main() == 0
    assert len(calls) == 1
    command, env = calls[0]
    assert command[1].endswith("backup_stores.py")
    assert command[-1] == "--skip-google-drive"
    assert env["ENV_FILE"] == "/tmp/brain.env"


def test_nightly_maintenance_returns_backup_failure(monkeypatch) -> None:
    module = load_nightly_maintenance()
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(command, *, env, check):
        calls.append((command, env))
        return SimpleNamespace(returncode=42)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.sys, "argv", ["nightly_maintenance.py"])

    assert module.main() == 42
    assert len(calls) == 1
    assert calls[0][0][1].endswith("backup_stores.py")
