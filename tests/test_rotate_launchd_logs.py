from __future__ import annotations

import gzip
import subprocess
import sys


def test_rotate_launchd_logs_copy_truncates_and_cleans_old_archives(tmp_path) -> None:
    log_dir = tmp_path / "logs"
    archive_dir = tmp_path / "archive"
    log_dir.mkdir()
    source = log_dir / "brain-prod.err.log"
    source.write_text("line one\nline two\n", encoding="utf-8")
    old = archive_dir / "2026-03-01"
    old.mkdir(parents=True)
    (old / "old.log.gz").write_text("old", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/rotate_launchd_logs.py",
            "--log-dir",
            str(log_dir),
            "--archive-dir",
            str(archive_dir),
            "--retention-days",
            "30",
            "--date",
            "2026-05-14",
        ],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )

    rotated = archive_dir / "2026-05-14" / "brain-prod.err.log.gz"
    assert "rotated 1 launchd logs" in result.stdout
    assert source.read_text(encoding="utf-8") == ""
    assert gzip.decompress(rotated.read_bytes()).decode("utf-8") == "line one\nline two\n"
    assert not old.exists()
