from __future__ import annotations

import argparse
import html
import json
import re
import threading
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any


STATUS_ORDER = {
    "zero_tolerance_fail": 0,
    "quality_fail": 1,
    "schema_fail": 2,
    "parse_fail": 3,
    "provider_fail": 4,
    "ok": 5,
}


def find_results_json(run_dir: Path, explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    candidates = sorted(run_dir.glob("results*.json"), key=lambda path: path.stat().st_mtime)
    return candidates[-1] if candidates else None


def find_raw_dir(run_dir: Path, explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    raw_full = run_dir / "raw_full"
    if raw_full.exists():
        return raw_full
    raw_root = run_dir / "raw"
    if raw_root.exists():
        subdirs = [path for path in raw_root.iterdir() if path.is_dir()]
        if subdirs:
            return max(subdirs, key=lambda path: path.stat().st_mtime)
        return raw_root
    return None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def records_from_raw(raw_dir: Path | None) -> list[dict[str, Any]]:
    if raw_dir is None or not raw_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in raw_dir.rglob("*.json"):
        try:
            data = read_json(path)
        except Exception:
            continue
        if isinstance(data, dict):
            data.setdefault("raw_output_path", str(path))
            records.append(data)
    return records


def records_from_results(results_json: Path | None) -> list[dict[str, Any]]:
    if results_json is None or not results_json.exists():
        return []
    try:
        data = read_json(results_json)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def latest_progress(run_dir: Path, records: list[dict[str, Any]]) -> tuple[int, int | None]:
    run_log = run_dir / "run.log"
    if run_log.exists():
        try:
            tail = run_log.read_text(encoding="utf-8", errors="replace")[-20000:]
        except Exception:
            tail = ""
        matches = re.findall(r"progress\s+(\d+)/(\d+)", tail)
        if matches:
            done, total = matches[-1]
            return int(done), int(total)
    return len(records), None


def estimate_timing(
    *,
    run_dir: Path,
    raw_dir: Path | None,
    done: int,
    total: int | None,
) -> dict[str, Any]:
    if not done or total is None or done >= total:
        return {
            "started_at": None,
            "elapsed_seconds": None,
            "rate_per_second": None,
            "remaining_seconds": None,
            "expected_end_at": None,
        }

    candidates: list[float] = []
    if raw_dir is not None and raw_dir.exists():
        for path in raw_dir.rglob("*.json"):
            try:
                candidates.append(path.stat().st_mtime)
            except OSError:
                continue
    for name in ("run.log", "selected_roles.txt"):
        path = run_dir / name
        if path.exists():
            try:
                candidates.append(path.stat().st_mtime)
            except OSError:
                continue

    if not candidates:
        return {
            "started_at": None,
            "elapsed_seconds": None,
            "rate_per_second": None,
            "remaining_seconds": None,
            "expected_end_at": None,
        }

    now = datetime.now(UTC)
    started_at = datetime.fromtimestamp(min(candidates), UTC)
    elapsed_seconds = max((now - started_at).total_seconds(), 1.0)
    rate_per_second = done / elapsed_seconds
    if rate_per_second <= 0:
        remaining_seconds = None
        expected_end_at = None
    else:
        remaining_seconds = max(total - done, 0) / rate_per_second
        expected_end_at = now + timedelta(seconds=remaining_seconds)

    return {
        "started_at": started_at,
        "elapsed_seconds": elapsed_seconds,
        "rate_per_second": rate_per_second,
        "remaining_seconds": remaining_seconds,
        "expected_end_at": expected_end_at,
    }


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: Counter[str] = Counter()
    by_model_role: dict[tuple[str, str], Counter[str]] = {}
    by_role: dict[str, Counter[str]] = {}
    for record in records:
        status = str(record.get("status") or "unknown")
        model = str(record.get("model") or "unknown")
        role = str(record.get("role") or "unknown")
        by_status[status] += 1
        by_model_role.setdefault((model, role), Counter())[status] += 1
        by_role.setdefault(role, Counter())[status] += 1
    return {
        "by_status": by_status,
        "by_model_role": by_model_role,
        "by_role": by_role,
    }


def failure_rows(records: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    failed = [
        record
        for record in records
        if str(record.get("status") or "") not in {"ok", "skipped"}
        or str(record.get("failure_class") or "none") != "none"
    ]
    failed.sort(
        key=lambda record: (
            STATUS_ORDER.get(str(record.get("status") or ""), 99),
            str(record.get("role") or ""),
            str(record.get("fixture_id") or ""),
        )
    )
    return failed[:limit]


def escape(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def render_html(
    *,
    run_dir: Path,
    results_json: Path | None,
    raw_dir: Path | None,
    records: list[dict[str, Any]],
    record_source: str,
    done: int,
    total: int | None,
) -> str:
    summary = summarize_records(records)
    timing = estimate_timing(run_dir=run_dir, raw_dir=raw_dir, done=done, total=total)
    updated = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    expected_end_at = timing["expected_end_at"]
    expected_end_text = (
        expected_end_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        if expected_end_at is not None
        else "unknown"
    )
    remaining_text = format_duration(timing["remaining_seconds"])
    total_text = str(total) if total is not None else "unknown"
    progress_pct = f"{(done / total * 100):.1f}%" if total else "unknown"
    is_scored = record_source == "scored_results"
    status_label = "Scored" if is_scored else "Raw provider"
    failure_label = "Scored failures" if is_scored else "Provider failures"
    ok_label = "Scored OK" if is_scored else "Provider OK"
    source_note = (
        "Final scored results loaded from results.json."
        if is_scored
        else (
            "Live counts are raw provider-call observations only. "
            "Quality, schema, and zero-tolerance scoring will appear after results.json is written."
        )
    )
    status_rows = "\n".join(
        f"<tr><td><code>{escape(status)}</code></td><td>{count}</td></tr>"
        for status, count in sorted(summary["by_status"].items())
    )
    model_role_rows = "\n".join(
        "<tr>"
        f"<td><code>{escape(model)}</code></td>"
        f"<td><code>{escape(role)}</code></td>"
        f"<td>{sum(counter.values())}</td>"
        f"<td>{counter.get('ok', 0)}</td>"
        f"<td>{sum(value for status, value in counter.items() if status != 'ok')}</td>"
        f"<td><code>{escape(dict(counter))}</code></td>"
        "</tr>"
        for (model, role), counter in sorted(
            summary["by_model_role"].items(),
            key=lambda item: (-sum(item[1].values()), item[0][0], item[0][1]),
        )[:120]
    )
    failed_rows = "\n".join(
        "<tr>"
        f"<td>{escape(record.get('failure_number') or '')}</td>"
        f"<td><code>{escape(record.get('status'))}</code></td>"
        f"<td><code>{escape(record.get('role'))}</code></td>"
        f"<td><code>{escape(record.get('fixture_id'))}</code></td>"
        f"<td><code>{escape(record.get('variant_id'))}</code></td>"
        f"<td>{escape(record.get('quality_score'))}</td>"
        f"<td><code>{escape(record.get('zero_tolerance_failure_types') or record.get('failure_reason_codes') or '')}</code></td>"
        "</tr>"
        for record in failure_rows(records)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="30">
  <title>Brain Eval Monitor</title>
  <style>
    :root {{ color-scheme: light; --bg:#f7f8fb; --panel:#fff; --text:#172033; --muted:#667085; --line:#d8dee8; }}
    body {{ margin:0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--bg); color:var(--text); }}
    main {{ max-width:1200px; margin:0 auto; padding:18px 14px 40px; }}
    section {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px; margin:12px 0; overflow-x:auto; }}
    h1 {{ font-size:22px; margin:0 0 6px; }}
    h2 {{ font-size:17px; margin:0 0 10px; }}
    p {{ color:var(--muted); margin:4px 0; }}
    table {{ width:100%; border-collapse:collapse; min-width:720px; }}
    th, td {{ border-top:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; font-size:13px; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:12px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }}
    .kpi {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fbfcfe; }}
    .kpi strong {{ display:block; font-size:20px; }}
  </style>
</head>
<body><main>
  <h1>Brain Eval Monitor</h1>
  <p>Updated: <code>{escape(updated)}</code></p>
  <p>Run dir: <code>{escape(run_dir)}</code></p>
  <p>Results: <code>{escape(results_json or '')}</code></p>
  <p>Raw: <code>{escape(raw_dir or '')}</code></p>
  <p>Count source: <code>{escape(record_source)}</code>. {escape(source_note)}</p>
  <section class="kpis">
    <div class="kpi"><span>Progress</span><strong>{done} / {escape(total_text)}</strong><p>{escape(progress_pct)}</p></div>
    <div class="kpi"><span>Expected end</span><strong>{escape(expected_end_text)}</strong><p>{escape(remaining_text)} remaining</p></div>
    <div class="kpi"><span>Rows observed</span><strong>{len(records)}</strong></div>
    <div class="kpi"><span>{escape(failure_label)}</span><strong>{sum(count for status, count in summary['by_status'].items() if status != 'ok')}</strong></div>
    <div class="kpi"><span>{escape(ok_label)}</span><strong>{summary['by_status'].get('ok', 0)}</strong></div>
  </section>
  <section><h2>{escape(status_label)} Status Counts</h2><table><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody>{status_rows}</tbody></table></section>
  <section><h2>Model / Role</h2><table><thead><tr><th>Model</th><th>Role</th><th>Total</th><th>OK</th><th>{escape(failure_label)}</th><th>Statuses</th></tr></thead><tbody>{model_role_rows}</tbody></table></section>
  <section><h2>Recent/Important Failures</h2><table><thead><tr><th>#</th><th>Status</th><th>Role</th><th>Fixture</th><th>Variant</th><th>Score</th><th>Reasons</th></tr></thead><tbody>{failed_rows}</tbody></table></section>
</main></body></html>
"""


def write_once(run_dir: Path, results_json: Path | None, raw_dir: Path | None) -> None:
    results_path = find_results_json(run_dir, results_json)
    raw_path = find_raw_dir(run_dir, raw_dir)
    scored_records = records_from_results(results_path)
    if scored_records:
        records = scored_records
        record_source = "scored_results"
    else:
        records = records_from_raw(raw_path)
        record_source = "raw_provider_outputs"
    done, total = latest_progress(run_dir, records)
    if total is None and scored_records:
        total = len(records)
    timing = estimate_timing(run_dir=run_dir, raw_dir=raw_path, done=done, total=total)
    html_text = render_html(
        run_dir=run_dir,
        results_json=results_path,
        raw_dir=raw_path,
        records=records,
        record_source=record_source,
        done=done,
        total=total,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "index.html").write_text(html_text, encoding="utf-8")
    (run_dir / "live_status.json").write_text(
        json.dumps(
            {
                "updated_at": datetime.now(UTC).isoformat(),
                "run_dir": str(run_dir),
                "results_json": str(results_path) if results_path else None,
                "raw_dir": str(raw_path) if raw_path else None,
                "status_counts_source": record_source,
                "status_counts_note": (
                    "final scored eval statuses"
                    if record_source == "scored_results"
                    else "raw provider-call statuses only; final scoring unavailable until results.json is written"
                ),
                "done": done,
                "elapsed_seconds": timing["elapsed_seconds"],
                "expected_end_at": timing["expected_end_at"].isoformat()
                if timing["expected_end_at"] is not None
                else None,
                "rate_per_second": timing["rate_per_second"],
                "remaining_seconds": timing["remaining_seconds"],
                "total": total,
                "status_counts": dict(summarize_records(records)["by_status"]),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def serve(run_dir: Path, bind: str, port: int) -> None:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(run_dir), **kwargs)

    server = ThreadingHTTPServer((bind, port), Handler)
    print(f"serving http://{bind}:{port}/ from {run_dir}", flush=True)
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh and optionally serve a Brain eval monitor page.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--results-json", type=Path)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=18084)
    args = parser.parse_args()

    if args.serve:
        thread = threading.Thread(target=serve, args=(args.run_dir, args.bind, args.port), daemon=True)
        thread.start()
        args.loop = True

    while True:
        write_once(args.run_dir, args.results_json, args.raw_dir)
        if not args.loop:
            return 0
        time.sleep(max(1, args.interval_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
