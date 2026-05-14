from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def dated_log_path(path_template: str | Path, *, now: datetime | None = None) -> Path:
    active_now = now or datetime.now(UTC)
    template = str(path_template)
    date = active_now.date().isoformat()
    return Path(template.format(date=date, utc_date=date)).expanduser()


def append_jsonl(
    path_template: str | Path,
    record: dict[str, Any],
    *,
    retention_days: int | None = None,
    now: datetime | None = None,
) -> Path:
    path = dated_log_path(path_template, now=now)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)
    if retention_days is not None and retention_days > 0:
        cleanup_dated_logs(path.parent, retention_days=retention_days, now=now)
    return path


def cleanup_dated_logs(
    directory: Path,
    *,
    retention_days: int,
    now: datetime | None = None,
) -> list[Path]:
    if not directory.exists():
        return []
    cutoff = (now or datetime.now(UTC)).date() - timedelta(days=retention_days)
    removed: list[Path] = []
    for path in directory.glob("*.jsonl*"):
        date_text = path.name.split(".", 1)[0]
        try:
            log_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            continue
        if log_date >= cutoff:
            continue
        path.unlink(missing_ok=True)
        removed.append(path)
    return removed
