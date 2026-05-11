from __future__ import annotations

import subprocess


DISALLOWED_TRACKED_PATH_PREFIXES = (
    ".data/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "artifacts/",
    "data/",
    "eval_reports/",
    "eval_runs/",
    "local-secrets/",
    "secrets/",
)

DISALLOWED_TRACKED_PATHS = {
    ".DS_Store",
}

DISALLOWED_TRACKED_PATH_PARTS = (
    "/__pycache__/",
)

DISALLOWED_TRACKED_PATH_SUFFIXES = (
    ".pyc",
    ".pyo",
)


def test_generated_runtime_and_secret_paths_are_not_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )

    tracked_paths = result.stdout.splitlines()
    violations = [
        path
        for path in tracked_paths
        if path in DISALLOWED_TRACKED_PATHS
        or path.startswith(DISALLOWED_TRACKED_PATH_PREFIXES)
        or any(part in path for part in DISALLOWED_TRACKED_PATH_PARTS)
        or path.endswith(DISALLOWED_TRACKED_PATH_SUFFIXES)
    ]

    assert violations == []
