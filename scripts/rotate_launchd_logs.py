#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path


LOG_NAMES = [
    "brain-prod.out.log",
    "brain-prod.err.log",
    "brain-ui.out.log",
    "brain-ui.err.log",
    "brain-slack-agent.out.log",
    "brain-slack-agent.err.log",
    "brain-agent-memory.out.log",
    "brain-agent-memory.err.log",
    "com.cloudflare.cloudflared.err.log",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily copy-truncate rotation for Brain launchd logs.")
    parser.add_argument("--log-dir", default=str(Path.home() / "Library" / "Logs"))
    parser.add_argument(
        "--archive-dir",
        default="/Volumes/xpg_usb4/prod/brain/shared/logs/launchd",
    )
    parser.add_argument("--retention-days", type=int, default=30)
    parser.add_argument("--date", default=None, help="Archive date, YYYY-MM-DD. Defaults to yesterday UTC.")
    args = parser.parse_args()

    now = datetime.now(UTC)
    archive_date = args.date or (now.date() - timedelta(days=1)).isoformat()
    log_dir = Path(args.log_dir).expanduser()
    archive_root = Path(args.archive_dir).expanduser()
    archive_day = archive_root / archive_date
    archive_day.mkdir(parents=True, exist_ok=True)

    rotated = []
    for name in LOG_NAMES:
        source = log_dir / name
        if not source.exists() or source.stat().st_size == 0:
            continue
        destination = archive_day / f"{name}.gz"
        copy_truncate_gzip(source, destination)
        rotated.append(str(destination))

    cleanup_archives(archive_root, retention_days=args.retention_days, now=now)
    print(f"rotated {len(rotated)} launchd logs into {archive_day}")
    return 0


def copy_truncate_gzip(source: Path, destination: Path) -> None:
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    with source.open("rb") as input_file, gzip.open(tmp, "wb", compresslevel=6) as output_file:
        shutil.copyfileobj(input_file, output_file)
    with source.open("r+b") as input_file:
        input_file.truncate(0)
    tmp.replace(destination)


def cleanup_archives(archive_root: Path, *, retention_days: int, now: datetime) -> None:
    cutoff = now.date() - timedelta(days=retention_days)
    if not archive_root.exists():
        return
    for path in archive_root.iterdir():
        if not path.is_dir():
            continue
        try:
            archive_date = datetime.strptime(path.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if archive_date >= cutoff:
            continue
        shutil.rmtree(path)


if __name__ == "__main__":
    raise SystemExit(main())
