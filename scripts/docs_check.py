#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = REPO_ROOT / "docs" / "generated" / "facts.json"
FACTS_HASH_PATH = REPO_ROOT / "docs" / "generated" / "facts.sha256"
MANIFEST_PATH = REPO_ROOT / "docs" / "sources" / "llm_docs.yaml"
HASH_RE = re.compile(r"<!-- brain-doc-source-hash: ([0-9a-f]{64}) -->")
SOURCE_COMMIT_RE = re.compile(r"<!-- brain-doc-source-commit: ([0-9a-f]{40}|unknown) -->\s*")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update-facts",
        action="store_true",
        help="Refresh docs/generated/facts.json and facts.sha256.",
    )
    args = parser.parse_args()

    failures: list[str] = []
    current_facts = collect_facts_text()
    current_facts_hash = sha256(current_facts)

    if args.update_facts:
        FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        FACTS_PATH.write_text(current_facts, encoding="utf-8")
        FACTS_HASH_PATH.write_text(f"{current_facts_hash}\n", encoding="utf-8")
        print(f"updated {relative(FACTS_PATH)}")
        return 0
    else:
        if not FACTS_PATH.exists():
            failures.append(f"missing generated facts file: {relative(FACTS_PATH)}")
        elif FACTS_PATH.read_text(encoding="utf-8") != current_facts:
            failures.append(
                f"stale generated facts: run `make docs-generate` and review {relative(FACTS_PATH)}"
            )
        if not FACTS_HASH_PATH.exists():
            failures.append(f"missing generated facts hash: {relative(FACTS_HASH_PATH)}")
        elif FACTS_HASH_PATH.read_text(encoding="utf-8").strip() != current_facts_hash:
            failures.append("stale generated facts hash: run `make docs-generate`")

    manifest = load_manifest()
    for doc in manifest["docs"]:
        path = REPO_ROOT / doc["path"]
        if not path.exists():
            failures.append(f"missing managed doc: {doc['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        match = HASH_RE.search(text)
        if not match:
            failures.append(f"missing doc source hash in {doc['path']}: run `make docs-hash`")
            continue
        expected = doc_source_hash(doc, current_facts)
        if match.group(1) != expected:
            failures.append(f"stale LLM-managed doc: {doc['path']} (run `make docs-llm`)")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("docs are current")
    return 0


def collect_facts_text() -> str:
    result = subprocess.run(
        [sys.executable, "scripts/docs_collect_facts.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"missing docs manifest: {relative(MANIFEST_PATH)}")
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {"docs": []}


def doc_source_hash(doc: dict[str, Any], facts_text: str) -> str:
    digest = hashlib.sha256()
    digest.update(facts_text.encode("utf-8"))
    digest.update(json.dumps(doc, sort_keys=True).encode("utf-8"))
    for source in sorted(doc.get("sources", [])):
        path = REPO_ROOT / source
        digest.update(source.encode("utf-8"))
        if path.exists():
            source_text = path.read_text(encoding="utf-8", errors="replace")
            digest.update(strip_doc_markers(source_text).encode("utf-8"))
        else:
            digest.update(b"<missing>")
    return digest.hexdigest()


def strip_doc_markers(text: str) -> str:
    return SOURCE_COMMIT_RE.sub("", HASH_RE.sub("", text)).rstrip() + "\n"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
