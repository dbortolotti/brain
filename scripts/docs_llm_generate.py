#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

MARKER_RE = re.compile(r"<!-- brain-doc-source-hash: [0-9a-f]{64} -->\s*$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Only refresh embedded doc hashes after manual review.",
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
            updated = set_hash(current, doc_source_hash(doc, facts_text))
        else:
            print(f"generating {doc['path']}...", flush=True)
            updated = generate_doc(client, doc, current, facts)
            validate_generated_doc(doc, current, updated)
            updated = set_hash(updated, doc_source_hash(doc, facts_text))
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
) -> str:
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


def set_hash(text: str, value: str) -> str:
    body = strip_hash(text).rstrip()
    return f"{body}\n\n<!-- brain-doc-source-hash: {value} -->\n"


def strip_hash(text: str) -> str:
    return MARKER_RE.sub("", text).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
