from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from memory_stack.evals.model_fixtures import select_fixtures
from memory_stack.evals.model_matrix import load_model_registry, select_model_candidates


def planned_totals(repo: Path) -> Counter[str]:
    registry = load_model_registry(repo / "brain_model_registry.yaml")
    fixtures = select_fixtures(fixture_set="brain-model-test-v2", roles=set(), mode="fine-grained")
    role_counts = Counter(f.role for f in fixtures)
    models = select_model_candidates(
        registry,
        model_refs=None,
        roles=set(),
        scope="active",
        include_judge=True,
        mode="fine-grained",
    )
    totals: Counter[str] = Counter()
    for model in models:
        totals[model.provider] += sum(role_counts[role] for role in model.roles if role in role_counts) * 3
    return totals


def current_counts(raw_dir: Path) -> tuple[Counter[str], Counter[str], Counter[str]]:
    seen: Counter[str] = Counter()
    all_fail: Counter[str] = Counter()
    quota_fail: Counter[str] = Counter()
    quota_patterns = (
        "quota",
        "insufficient_quota",
        "credit",
        "billing",
        "resource exhausted",
        "resource_exhausted",
    )
    for path in raw_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        model = data.get("model") or ""
        provider = model.split(":", 1)[0] if ":" in model else "unknown"
        seen[provider] += 1
        if data.get("status") != "ok":
            all_fail[provider] += 1
            blob = f"{data.get('error') or ''} {json.dumps(data, sort_keys=True)}".lower()
            if any(pattern in blob for pattern in quota_patterns):
                quota_fail[provider] += 1
    return seen, all_fail, quota_fail


def render_markdown(
    *,
    raw_dir: Path,
    totals: Counter[str],
    seen: Counter[str],
    all_fail: Counter[str],
    quota_fail: Counter[str],
) -> str:
    now = datetime.now(UTC).astimezone()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    total_seen = sum(seen.values())
    total_planned = sum(totals.values())
    remaining = max(total_planned - total_seen, 0)
    rate_per_min: float | None = None
    eta_text = "unknown"
    files = sorted(raw_dir.rglob("*.json"), key=lambda path: path.stat().st_mtime)
    if len(files) >= 2:
        first = files[0].stat().st_mtime
        last = files[-1].stat().st_mtime
        span_seconds = last - first
        if span_seconds > 0:
            rate_per_min = total_seen / (span_seconds / 60.0)
    if rate_per_min and rate_per_min > 0:
        eta_minutes = remaining / rate_per_min
        eta_dt = now.timestamp() + eta_minutes * 60.0
        eta_local = datetime.fromtimestamp(eta_dt, tz=now.tzinfo)
        eta_text = f"{eta_local.strftime('%Y-%m-%d %H:%M:%S %Z')} ({eta_minutes:.0f} min remaining at {rate_per_min:.1f} tests/min)"
    lines = [
        "# Fine-Grained Eval Live Status",
        "",
        f"Updated: `{timestamp}`",
        f"Expected end: `{eta_text}`",
        "",
        f"Raw dir: `{raw_dir}`",
        "",
        "| Model family | Quota / All fail / Seen / Total |",
        "|---|---:|",
    ]
    for family in sorted(totals):
        lines.append(
            f"| `{family}` | `{quota_fail[family]} / {all_fail[family]} / {seen[family]} / {totals[family]}` |"
        )
    return "\n".join(lines) + "\n"


def render_html(markdown: str) -> str:
    rows = []
    for line in markdown.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        family = parts[0].strip("`")
        metrics = parts[1].strip("`")
        rows.append((family, metrics))
    timestamp_line = next((line for line in markdown.splitlines() if line.startswith("Updated:")), "")
    eta_line = next((line for line in markdown.splitlines() if line.startswith("Expected end:")), "")
    raw_dir_line = next((line for line in markdown.splitlines() if line.startswith("Raw dir:")), "")
    body_rows = "\n".join(
        f"<tr><td><code>{family}</code></td><td><code>{metrics}</code></td></tr>" for family, metrics in rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fine-Grained Eval Live Status</title>
  <style>
    :root {{
      --bg: #f6f1e8;
      --card: #fffaf2;
      --ink: #1e1d1a;
      --muted: #5f5a50;
      --line: #d7ccba;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Iowan Old Style", serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #fffdf8, var(--bg) 60%);
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 12px 30px rgba(0,0,0,0.05);
    }}
    h1 {{ margin-top: 0; }}
    p {{ color: var(--muted); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }}
    th, td {{
      border-top: 1px solid var(--line);
      padding: 12px 10px;
      text-align: left;
    }}
    th {{ font-size: 0.95rem; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.92rem;
    }}
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Fine-Grained Eval Live Status</h1>
      <p>{timestamp_line}</p>
      <p>{eta_line}</p>
      <p>{raw_dir_line}</p>
      <table>
        <thead>
          <tr><th>Model family</th><th>Quota / All fail / Seen / Total</th></tr>
        </thead>
        <tbody>
          {body_rows}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def write_once(repo: Path, run_dir: Path, publish_dir: Path | None = None) -> None:
    raw_root = run_dir / "raw"
    raw_subdirs = [path for path in raw_root.iterdir() if path.is_dir()] if raw_root.exists() else []
    if not raw_subdirs:
        raise FileNotFoundError(f"no raw run directories found under {raw_root}")
    raw_dir = max(raw_subdirs, key=lambda path: path.stat().st_mtime)
    totals = planned_totals(repo)
    seen, all_fail, quota_fail = current_counts(raw_dir)
    markdown = render_markdown(
        raw_dir=raw_dir,
        totals=totals,
        seen=seen,
        all_fail=all_fail,
        quota_fail=quota_fail,
    )
    html = render_html(markdown)
    (run_dir / "live_status.md").write_text(markdown, encoding="utf-8")
    (run_dir / "live_status.html").write_text(html, encoding="utf-8")
    if publish_dir is not None:
        publish_dir.mkdir(parents=True, exist_ok=True)
        (publish_dir / "fine_grained_live_status.md").write_text(markdown, encoding="utf-8")
        (publish_dir / "fine_grained_live_status.html").write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--publish-dir", type=Path)
    parser.add_argument("--interval-seconds", type=int, default=600)
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    while True:
        write_once(args.repo, args.run_dir, args.publish_dir)
        if not args.loop:
            return 0
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
