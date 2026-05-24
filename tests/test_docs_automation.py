from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path("scripts").resolve()))
import docs_check  # noqa: E402
import docs_llm_generate  # noqa: E402


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
    assert "docs/AGENT_TOOL_GUIDE.md" in paths
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


def test_doc_source_markers_do_not_change_source_hash(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "# Source\n\nBody\n\n"
        "<!-- brain-doc-source-hash: "
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef -->\n"
        "<!-- brain-doc-source-commit: ab7f9f07ebbb46922db0079c8daab2903fc84ed3 -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(docs_check, "REPO_ROOT", tmp_path)

    with_markers = docs_check.doc_source_hash({"sources": ["source.md"]}, "{}")
    source.write_text("# Source\n\nBody\n", encoding="utf-8")
    without_markers = docs_check.doc_source_hash({"sources": ["source.md"]}, "{}")

    assert with_markers == without_markers


def test_doc_hash_update_adds_source_commit_marker(monkeypatch) -> None:
    monkeypatch.setattr(
        docs_llm_generate,
        "current_git_commit",
        lambda: "ab7f9f07ebbb46922db0079c8daab2903fc84ed3",
    )

    updated = docs_llm_generate.set_source_markers(
        "# Doc\n\nBody\n",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )

    assert "brain-doc-source-hash" in updated
    assert "brain-doc-source-commit: ab7f9f07ebbb46922db0079c8daab2903fc84ed3" in updated
    assert docs_llm_generate.strip_hash(updated) == "# Doc\n\nBody\n"
