from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from memory_stack.evals.model_fixtures import select_fixtures
from memory_stack.evals.model_matrix import load_model_registry, select_model_candidates
from memory_stack.evals.model_runner import build_work_items


def planned_totals(repo: Path) -> Counter[str]:
    registry = load_model_registry(repo / "brain_model_registry.yaml")
    models = select_model_candidates(
        registry,
        model_refs=None,
        roles=set(),
        scope="active",
        include_judge=True,
        mode="fine-grained",
    )
    fixtures = select_fixtures(fixture_set="brain-model-test-v2", roles=set(), mode="fine-grained")
    work_items = build_work_items(models, set(), fixtures, 3)
    totals: Counter[str] = Counter()
    for item in work_items:
        totals[item.candidate.provider] += 1
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


def planned_model_role_counts(repo: Path) -> dict[tuple[str, str], int]:
    registry = load_model_registry(repo / "brain_model_registry.yaml")
    models = select_model_candidates(
        registry,
        model_refs=None,
        roles=set(),
        scope="active",
        include_judge=True,
        mode="fine-grained",
    )
    fixtures = select_fixtures(fixture_set="brain-model-test-v2", roles=set(), mode="fine-grained")
    work_items = build_work_items(models, set(), fixtures, 3)
    counts: Counter[tuple[str, str]] = Counter()
    for item in work_items:
        counts[(item.candidate.ref, item.fixture.role)] += 1
    return dict(counts)


def current_model_role_counts(
    raw_dir: Path,
) -> tuple[Counter[tuple[str, str]], Counter[tuple[str, str]], Counter[tuple[str, str]], Counter[tuple[str, str]]]:
    seen: Counter[tuple[str, str]] = Counter()
    ok: Counter[tuple[str, str]] = Counter()
    schemaish: Counter[tuple[str, str]] = Counter()
    failed: Counter[tuple[str, str]] = Counter()
    for path in raw_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        model = str(data.get("model") or "")
        role = str(data.get("role") or "")
        if not model or not role:
            continue
        key = (model, role)
        seen[key] += 1
        status = data.get("status")
        if status == "ok":
            ok[key] += 1
        elif status in {"schema_fail", "schema_invalid"}:
            schemaish[key] += 1
        else:
            failed[key] += 1
    return seen, ok, schemaish, failed


def estimate_eta(raw_dir: Path, total_seen: int, total_planned: int) -> tuple[str, str]:
    now = datetime.now(UTC).astimezone()
    remaining = max(total_planned - total_seen, 0)
    rate_per_min: float | None = None
    eta_text = "unknown"
    rate_text = "unknown"
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
        rate_text = f"{rate_per_min:.1f} tests/min"
    return eta_text, rate_text


def render_markdown(
    *,
    raw_dir: Path,
    totals: Counter[str],
    seen: Counter[str],
    all_fail: Counter[str],
    quota_fail: Counter[str],
    model_role_rows: list[dict[str, str | int]],
) -> str:
    now = datetime.now(UTC).astimezone()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    total_seen = sum(seen.values())
    total_planned = sum(totals.values())
    eta_text, _rate_text = estimate_eta(raw_dir, total_seen, total_planned)
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
    lines.extend(
        [
            "",
            "## Preliminary model/role feasibility",
            "",
            "| Model | Role | Feasibility | Seen / Total | Ok | Schema | Fail |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in model_role_rows[:40]:
        lines.append(
            f"| `{row['model']}` | `{row['role']}` | {row['feasibility']} | "
            f"{row['seen']} / {row['total']} | {row['ok']} | {row['schema']} | {row['fail']} |"
        )
    return "\n".join(lines) + "\n"


def render_html(
    *,
    timestamp_line: str,
    eta_line: str,
    raw_dir_line: str,
    family_rows: list[tuple[str, str]],
    model_role_rows: list[dict[str, str | int]],
) -> str:
    family_html = "\n".join(
        f"<tr><td><code>{family}</code></td><td><code>{metrics}</code></td></tr>" for family, metrics in family_rows
    )
    model_summary: dict[str, dict[str, int]] = {}
    role_tree_rows: dict[str, list[dict[str, str | int]]] = {}
    for row in model_role_rows:
        role_tree_rows.setdefault(str(row["role"]), []).append(row)
        model = str(row["model"])
        bucket = model_summary.setdefault(
            model,
            {"seen": 0, "total": 0, "ok": 0, "schema": 0, "fail": 0, "clean_roles": 0, "issue_roles": 0, "pending_roles": 0},
        )
        bucket["seen"] += int(row["seen"])
        bucket["total"] += int(row["total"])
        bucket["ok"] += int(row["ok"])
        bucket["schema"] += int(row["schema"])
        bucket["fail"] += int(row["fail"])
        feasibility = str(row["feasibility"])
        if feasibility == "clean so far":
            bucket["clean_roles"] += 1
        elif feasibility == "issues seen":
            bucket["issue_roles"] += 1
        else:
            bucket["pending_roles"] += 1
    role_tree_html_parts: list[str] = []
    for role in sorted(role_tree_rows):
        rows = sorted(
            role_tree_rows[role],
            key=lambda item: (-int(item["seen"]), str(item["model"])),
        )
        role_tree_html_parts.append(
            "<details class=\"tree-node\" open>"
            f"<summary><code>{role}</code> <span class=\"muted\">({len(rows)} models)</span></summary>"
            "<div class=\"tree-children\">"
        )
        for row in rows:
            model_class = f"model-name {str(row['feasibility']).replace(' ', '-')}"
            role_tree_html_parts.append(
                "<details class=\"tree-leaf\">"
                f"<summary><code class=\"{model_class}\">{row['model']}</code></summary>"
                "<div class=\"tree-metrics\">"
                f"<div><strong>Status:</strong> {row['feasibility']}</div>"
                f"<div><strong>Seen / Total:</strong> <code>{row['seen']} / {row['total']}</code></div>"
                f"<div><strong>Ok:</strong> {row['ok']}</div>"
                f"<div><strong>Schema:</strong> {row['schema']}</div>"
                f"<div><strong>Fail:</strong> {row['fail']}</div>"
                "</div>"
                "</details>"
            )
        role_tree_html_parts.append("</div></details>")
    role_tree_html = "\n".join(role_tree_html_parts)
    model_summary_rows = sorted(
        model_summary.items(),
        key=lambda item: (-item[1]["seen"], item[0]),
    )
    model_summary_html = "\n".join(
        "<tr>"
        f"<td><code class=\"model-name {'issues-seen' if stats['issue_roles'] else ('clean-so-far' if stats['clean_roles'] else 'pending')}\">{model}</code></td>"
        f"<td><code>{stats['seen']} / {stats['total']}</code></td>"
        f"<td>{stats['ok']}</td>"
        f"<td>{stats['schema']}</td>"
        f"<td>{stats['fail']}</td>"
        f"<td>{stats['clean_roles']}</td>"
        f"<td>{stats['issue_roles']}</td>"
        f"<td>{stats['pending_roles']}</td>"
        "</tr>"
        for model, stats in model_summary_rows
    )
    family_model_role: dict[str, dict[str, list[dict[str, str | int]]]] = {}
    for row in model_role_rows:
        model = str(row["model"])
        family = model.split(":", 1)[0] if ":" in model else "unknown"
        family_model_role.setdefault(family, {}).setdefault(model, []).append(row)
    role_tree_by_family_parts: list[str] = []
    for family in sorted(family_model_role):
        family_models = family_model_role[family]
        family_seen = sum(int(row["seen"]) for rows in family_models.values() for row in rows)
        family_total = sum(int(row["total"]) for rows in family_models.values() for row in rows)
        role_tree_by_family_parts.append(
            "<details class=\"tree-node\" open>"
            f"<summary><code>{family}</code> <span class=\"muted\">({len(family_models)} models, {family_seen} / {family_total})</span></summary>"
            "<div class=\"tree-children\">"
        )
        for model in sorted(
            family_models,
            key=lambda item: (
                -sum(int(row["seen"]) for row in family_models[item]),
                item,
            ),
        ):
            rows = sorted(
                family_models[model],
                key=lambda item: (-int(item["seen"]), str(item["role"])),
            )
            issue_roles = sum(1 for row in rows if str(row["feasibility"]) == "issues seen")
            clean_roles = sum(1 for row in rows if str(row["feasibility"]) == "clean so far")
            model_class = "issues-seen" if issue_roles else ("clean-so-far" if clean_roles else "pending")
            model_seen = sum(int(row["seen"]) for row in rows)
            model_total = sum(int(row["total"]) for row in rows)
            role_tree_by_family_parts.append(
                "<details class=\"tree-leaf\">"
                f"<summary><code class=\"model-name {model_class}\">{model}</code> <span class=\"muted\">({model_seen} / {model_total})</span></summary>"
                "<div class=\"tree-children\">"
            )
            for row in rows:
                role_class = str(row["feasibility"]).replace(" ", "-")
                role_tree_by_family_parts.append(
                    "<details class=\"tree-leaf\">"
                    f"<summary><code class=\"model-name {role_class}\">{row['role']}</code></summary>"
                    "<div class=\"tree-metrics\">"
                    f"<div><strong>Status:</strong> {row['feasibility']}</div>"
                    f"<div><strong>Seen / Total:</strong> <code>{row['seen']} / {row['total']}</code></div>"
                    f"<div><strong>Ok:</strong> {row['ok']}</div>"
                    f"<div><strong>Schema:</strong> {row['schema']}</div>"
                    f"<div><strong>Fail:</strong> {row['fail']}</div>"
                    "</div>"
                    "</details>"
                )
            role_tree_by_family_parts.append("</div></details>")
        role_tree_by_family_parts.append("</div></details>")
    role_tree_by_family_html = "\n".join(role_tree_by_family_parts)
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
      min-height: 100vh;
      font-family: Georgia, "Iowan Old Style", serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #fffdf8, var(--bg) 60%);
      background-attachment: fixed;
    }}
    main {{
      max-width: 1560px;
      margin: 0 auto;
      padding: 32px 20px 48px;
      box-sizing: border-box;
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
    .tabs {{
      display: flex;
      gap: 8px;
      margin-top: 20px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }}
    .tab-button {{
      border: 1px solid var(--line);
      background: #f0e4d3;
      color: var(--ink);
      border-radius: 999px;
      padding: 8px 12px;
      cursor: pointer;
    }}
    .tab-button.active {{
      background: #d7b98c;
    }}
    .tab-panel {{
      display: none;
    }}
    .tab-panel.active {{
      display: block;
    }}
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
    .small {{
      font-size: 0.92rem;
    }}
    .tree-node, .tree-leaf {{
      border-top: 1px solid var(--line);
      padding: 10px 0;
    }}
    .tree-node summary, .tree-leaf summary {{
      cursor: pointer;
      list-style: none;
      white-space: nowrap;
      overflow-x: auto;
      overflow-y: hidden;
      padding-bottom: 2px;
    }}
    .tree-node summary::-webkit-details-marker,
    .tree-leaf summary::-webkit-details-marker {{
      display: none;
    }}
    .tree-node summary::before,
    .tree-leaf summary::before {{
      content: "▸";
      display: inline-block;
      margin-right: 8px;
      color: var(--muted);
    }}
    .tree-node[open] > summary::before,
    .tree-leaf[open] > summary::before {{
      content: "▾";
    }}
    .tree-children {{
      margin-left: 18px;
      margin-top: 8px;
    }}
    .tree-metrics {{
      display: grid;
      grid-template-columns: repeat(2, minmax(160px, 1fr));
      gap: 8px 16px;
      margin-top: 8px;
      margin-left: 24px;
      color: var(--muted);
      white-space: nowrap;
      overflow-x: auto;
    }}
    .muted {{
      color: var(--muted);
    }}
    .model-name.clean-so-far {{
      color: #2f6b3c;
    }}
    .model-name.issues-seen {{
      color: #9c4b21;
    }}
    .model-name.pending {{
      color: var(--muted);
    }}
    td, th {{
      white-space: nowrap;
    }}
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Fine-Grained Eval Live Status</h1>
      <p>{timestamp_line}</p>
      <p>{eta_line}</p>
      <div class="tabs">
        <button class="tab-button active" data-tab="family">Family Summary</button>
        <button class="tab-button" data-tab="tree">Role/Model Tree</button>
        <button class="tab-button" data-tab="model">Model Summary</button>
        <button class="tab-button" data-tab="role">Model/Role Feasibility</button>
      </div>
      <section id="family" class="tab-panel active">
        <p class="small">High-level live provider-family view.</p>
        <table>
          <thead>
            <tr><th>Model family</th><th>Quota / All fail / Seen / Total</th></tr>
          </thead>
          <tbody>
            {family_html}
          </tbody>
        </table>
      </section>
      <section id="tree" class="tab-panel">
        <p class="small">Collapsible live view of preliminary role coverage. Expand a role, then expand a model for current seen/ok/schema/fail counts.</p>
        {role_tree_html}
      </section>
      <section id="model" class="tab-panel">
        <p class="small">Aggregated early summary by model across all currently observed roles.</p>
        <table>
          <thead>
            <tr><th>Model</th><th>Seen / Total</th><th>Ok</th><th>Schema</th><th>Fail</th><th>Clean roles</th><th>Issue roles</th><th>Pending roles</th></tr>
          </thead>
          <tbody>
            {model_summary_html}
          </tbody>
        </table>
      </section>
      <section id="role" class="tab-panel">
        <p class="small">Preliminary feasibility is directional only. This view groups observed rows as family, then model, then role.</p>
        {role_tree_by_family_html}
      </section>
    </section>
  </main>
  <script>
    const buttons = document.querySelectorAll('.tab-button');
    const panels = document.querySelectorAll('.tab-panel');
    buttons.forEach((button) => {{
      button.addEventListener('click', () => {{
        buttons.forEach((item) => item.classList.remove('active'));
        panels.forEach((panel) => panel.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(button.dataset.tab).classList.add('active');
      }});
    }});
  </script>
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
    model_role_totals = planned_model_role_counts(repo)
    model_role_seen, model_role_ok, model_role_schema, model_role_fail = current_model_role_counts(raw_dir)
    model_role_rows: list[dict[str, str | int]] = []
    for model, role in sorted(model_role_totals, key=lambda item: (item[1], item[0])):
        total = model_role_totals[(model, role)]
        seen_count = model_role_seen[(model, role)]
        ok_count = model_role_ok[(model, role)]
        schema_count = model_role_schema[(model, role)]
        fail_count = model_role_fail[(model, role)]
        if seen_count == 0:
            feasibility = "pending"
        elif schema_count or fail_count:
            feasibility = "issues seen"
        else:
            feasibility = "clean so far"
        model_role_rows.append(
            {
                "model": model,
                "role": role,
                "feasibility": feasibility,
                "seen": seen_count,
                "total": total,
                "ok": ok_count,
                "schema": schema_count,
                "fail": fail_count,
            }
        )
    model_role_rows.sort(key=lambda row: (str(row["feasibility"]), -int(row["seen"]), str(row["role"]), str(row["model"])))
    markdown = render_markdown(
        raw_dir=raw_dir,
        totals=totals,
        seen=seen,
        all_fail=all_fail,
        quota_fail=quota_fail,
        model_role_rows=model_role_rows,
    )
    family_rows = [(family, f"{quota_fail[family]} / {all_fail[family]} / {seen[family]} / {totals[family]}") for family in sorted(totals)]
    timestamp_line = next((line for line in markdown.splitlines() if line.startswith("Updated:")), "")
    eta_line = next((line for line in markdown.splitlines() if line.startswith("Expected end:")), "")
    raw_dir_line = next((line for line in markdown.splitlines() if line.startswith("Raw dir:")), "")
    html = render_html(
        timestamp_line=timestamp_line,
        eta_line=eta_line,
        raw_dir_line=raw_dir_line,
        family_rows=family_rows,
        model_role_rows=model_role_rows[:200],
    )
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
