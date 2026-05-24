#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from memory_stack.cfg import Settings  # noqa: E402
from memory_stack.llm.client import ConfiguredLLMClient  # noqa: E402

from docs_check import doc_source_hash  # noqa: E402

FACTS_PATH = REPO_ROOT / "docs" / "generated" / "facts.json"
MANIFEST_PATH = REPO_ROOT / "docs" / "sources" / "llm_docs.yaml"

MARKER_RE = re.compile(r"<!-- brain-doc-source-hash: [0-9a-f]{64} -->\s*")
SOURCE_COMMIT_RE = re.compile(r"<!-- brain-doc-source-commit: ([0-9a-f]{40}|unknown) -->\s*$")
MAX_DIFF_CHARS = 30_000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Only refresh embedded doc hashes after manual review.",
    )
    parser.add_argument(
        "--full-regenerate",
        action="store_true",
        help="Regenerate full documents from source excerpts instead of using source diffs.",
    )
    parser.add_argument(
        "--doc",
        action="append",
        default=[],
        help="Limit generation to a doc path from docs/sources/llm_docs.yaml.",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--reasoning-effort", default="medium")
    args = parser.parse_args()

    facts_text = regenerate_facts()
    facts = json.loads(facts_text)
    manifest = load_manifest()
    docs = manifest.get("docs", [])
    if args.doc:
        selected = set(args.doc)
        docs = [doc for doc in docs if doc["path"] in selected]
    if not docs:
        print("no docs selected", file=sys.stderr)
        return 1

    client = None if args.hash_only else ConfiguredLLMClient(Settings(brain_llm_enabled=True))
    for doc in docs:
        path = REPO_ROOT / doc["path"]
        current = path.read_text(encoding="utf-8")
        if args.hash_only:
            updated = set_source_markers(current, doc_source_hash(doc, facts_text))
        else:
            print(f"generating {doc['path']}...", flush=True)
            updated = generate_doc(client, doc, current, facts, full_regenerate=args.full_regenerate)
            validate_generated_doc(doc, current, updated)
            updated = set_source_markers(updated, doc_source_hash(doc, facts_text))
        path.write_text(updated, encoding="utf-8")
        print(f"updated {doc['path']}", flush=True)
    return 0


def regenerate_facts() -> str:
    subprocess.run(
        [
            sys.executable,
            "scripts/docs_check.py",
            "--update-facts",
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    return FACTS_PATH.read_text(encoding="utf-8")


def load_manifest() -> dict[str, Any]:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {"docs": []}


def generate_doc(
    client: ConfiguredLLMClient,
    doc: dict[str, Any],
    current: str,
    facts: dict[str, Any],
    *,
    full_regenerate: bool,
) -> str:
    if not full_regenerate:
        baseline_commit = source_commit(current)
        if baseline_commit and baseline_commit_exists(baseline_commit):
            updated = generate_doc_from_diffs(client, doc, current, facts, baseline_commit)
            if updated is not None:
                return updated
        print(
            f"falling back to full regeneration for {doc['path']} "
            "because no usable source commit marker was found",
            flush=True,
        )
    schema = {
        "type": "object",
        "properties": {
            "markdown": {
                "type": "string",
                "description": "Complete replacement Markdown document.",
            }
        },
        "required": ["markdown"],
        "additionalProperties": False,
    }
    prompt = "\n\n".join(
        [
            "You are maintaining Brain documentation.",
            "Revise the target Markdown document using only the supplied facts and source excerpts.",
            "Do not invent endpoints, UI controls, workflows, secrets, or operational behavior.",
            "Preserve the current document's useful technical detail, examples, commands, tables, and warnings unless the supplied facts show they are stale.",
            "Prefer targeted updates over broad summarization. Do not shorten the document materially.",
            "Preserve warnings about secrets, auth, deletion, backups, and production promotion.",
            f"Target document: {doc['path']}",
            f"Audience: {doc.get('audience', 'Brain users and operators')}",
            f"Purpose: {doc.get('purpose', 'Keep Brain documentation accurate and readable.')}",
            "Current Markdown:",
            strip_hash(current),
            "Deterministic facts JSON summary:",
            json.dumps(facts_summary(facts), indent=2, sort_keys=True),
            "Source excerpts:",
            source_excerpts(doc),
        ]
    )
    result = client.complete_json(
        prompt,
        schema,
        schema_name="brain_docs_markdown",
        model=doc.get("model"),
        reasoning_effort=doc.get("reasoning_effort", "medium"),
        max_output_tokens=doc.get("max_output_tokens", 12_000),
    )
    markdown = str(result["markdown"]).strip() + "\n"
    return markdown


def generate_doc_from_diffs(
    client: ConfiguredLLMClient,
    doc: dict[str, Any],
    current: str,
    facts: dict[str, Any],
    baseline_commit: str,
) -> str | None:
    source_diff = source_diffs(doc, baseline_commit)
    facts_diff = facts_summary_diff(baseline_commit, facts)
    if not source_diff.strip() and not facts_diff.strip():
        return strip_hash(current)
    schema = {
        "type": "object",
        "properties": {
            "changed": {
                "type": "boolean",
                "description": "Whether the document needed content edits for the supplied diffs.",
            },
            "markdown": {
                "type": "string",
                "description": "Complete Markdown document. If changed is false, return the current Markdown unchanged.",
            },
        },
        "required": ["changed", "markdown"],
        "additionalProperties": False,
    }
    prompt = "\n\n".join(
        [
            "You are maintaining Brain documentation with a diff-based workflow.",
            "Read the full current Markdown, then inspect only the supplied source and facts diffs.",
            "Update the document only where the diffs introduce behavior, endpoints, config, commands, or operational details that are missing, stale, or incorrectly described.",
            "If the current Markdown already represents the diffs correctly, set changed=false and return the current Markdown unchanged.",
            "Do not reformat, summarize, reorder, or rephrase unrelated sections.",
            "Do not invent endpoints, UI controls, workflows, secrets, or operational behavior.",
            "Preserve warnings about secrets, auth, deletion, backups, and production promotion.",
            f"Target document: {doc['path']}",
            f"Audience: {doc.get('audience', 'Brain users and operators')}",
            f"Purpose: {doc.get('purpose', 'Keep Brain documentation accurate and readable.')}",
            f"Baseline source commit: {baseline_commit}",
            "Current Markdown:",
            strip_hash(current),
            "Current deterministic facts JSON summary:",
            json.dumps(facts_summary(facts), indent=2, sort_keys=True),
            "Facts summary diff from baseline to current:",
            facts_diff or "<no facts summary diff>",
            "Managed source diffs from baseline to current:",
            source_diff or "<no managed source diff>",
        ]
    )
    result = client.complete_json(
        prompt,
        schema,
        schema_name="brain_docs_diff_markdown",
        model=doc.get("model"),
        reasoning_effort=doc.get("reasoning_effort", "medium"),
        max_output_tokens=doc.get("max_output_tokens", 12_000),
    )
    markdown = str(result["markdown"]).strip() + "\n"
    return markdown


def validate_generated_doc(doc: dict[str, Any], current: str, updated: str) -> None:
    current_lines = len(strip_hash(current).splitlines())
    updated_lines = len(strip_hash(updated).splitlines())
    if current_lines >= 80 and updated_lines < int(current_lines * 0.75):
        raise RuntimeError(
            f"LLM output for {doc['path']} is too short: {updated_lines} lines vs {current_lines}"
        )
    if not updated.lstrip().startswith("#"):
        raise RuntimeError(f"LLM output for {doc['path']} does not look like Markdown")


def facts_summary(facts: dict[str, Any]) -> dict[str, Any]:
    routes = facts.get("http_routes", {})
    tools = facts.get("mcp_tools", {})
    return {
        "schema_version": facts.get("schema_version"),
        "config": facts.get("config", {}),
        "http_routes": {
            surface: [
                {"path": route["path"], "methods": route["methods"], "name": route["name"]}
                for route in route_list
            ]
            for surface, route_list in routes.items()
        },
        "mcp_tools": {
            surface: [tool["name"] for tool in tool_list]
            for surface, tool_list in tools.items()
        },
        "workflows": facts.get("workflows", {}),
        "ui": facts.get("ui", {}),
    }


def source_excerpts(doc: dict[str, Any]) -> str:
    chunks: list[str] = []
    for source in doc.get("sources", []):
        path = REPO_ROOT / source
        if not path.exists():
            chunks.append(f"## {source}\n<missing>")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > 8_000:
            text = text[:8_000] + "\n\n[truncated]"
        chunks.append(f"## {source}\n{text}")
    return "\n\n".join(chunks)


def source_diffs(doc: dict[str, Any], baseline_commit: str) -> str:
    sources = [source for source in doc.get("sources", []) if source]
    if not sources:
        return ""
    result = subprocess.run(
        ["git", "diff", "--unified=80", "--no-ext-diff", baseline_commit, "--", *sources],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return truncate_diff(result.stdout)


def facts_summary_diff(baseline_commit: str, current_facts: dict[str, Any]) -> str:
    result = subprocess.run(
        ["git", "show", f"{baseline_commit}:docs/generated/facts.json"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    try:
        baseline_facts = json.loads(result.stdout)
    except json.JSONDecodeError:
        return ""
    baseline = json.dumps(facts_summary(baseline_facts), indent=2, sort_keys=True).splitlines()
    current = json.dumps(facts_summary(current_facts), indent=2, sort_keys=True).splitlines()
    diff = "\n".join(
        difflib.unified_diff(
            baseline,
            current,
            fromfile=f"{baseline_commit}:facts_summary",
            tofile="current:facts_summary",
            lineterm="",
        )
    )
    return truncate_diff(diff)


def truncate_diff(value: str) -> str:
    if len(value) <= MAX_DIFF_CHARS:
        return value
    return value[:MAX_DIFF_CHARS] + "\n\n[diff truncated]"


def set_source_markers(text: str, value: str) -> str:
    body = strip_hash(text).rstrip()
    return (
        f"{body}\n\n"
        f"<!-- brain-doc-source-hash: {value} -->\n"
        f"<!-- brain-doc-source-commit: {current_git_commit()} -->\n"
    )


def strip_hash(text: str) -> str:
    return SOURCE_COMMIT_RE.sub("", MARKER_RE.sub("", text)).rstrip() + "\n"


def source_commit(text: str) -> str | None:
    match = SOURCE_COMMIT_RE.search(text)
    if not match or match.group(1) == "unknown":
        return None
    return match.group(1)


def current_git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def baseline_commit_exists(commit: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
