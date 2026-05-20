from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def test_docs_automation_files_are_wired() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    pre_commit = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")

    for target in ("docs-generate", "docs-check", "docs-hash", "docs-llm", "llm-docs"):
        assert f"{target}:" in makefile

    assert "make docs-check" in pre_commit
    assert "make llm-docs" in pre_commit
    assert "stages: [manual]" not in pre_commit


def test_docs_check_is_part_of_validation_and_deploy_workflows() -> None:
    for path in [
        Path(".github/workflows/validate.yml"),
        Path(".github/workflows/deploy-local-staging.yml"),
        Path(".github/workflows/release.yml"),
    ]:
        assert "make docs-check" in path.read_text(encoding="utf-8")


def test_docs_manifest_tracks_user_and_operator_docs() -> None:
    manifest = yaml.safe_load(Path("docs/sources/llm_docs.yaml").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest["docs"]}

    assert "docs/USER_GUIDE.md" in paths
    assert "USER_MANUAL.md" in paths
    assert "docs/API_SETUP_GUIDE.md" in paths
    assert "docs/production-secrets.md" in paths


def test_docs_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/docs_check.py"],
        check=False,
        capture_output=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
