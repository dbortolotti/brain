#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from memory_stack import cfg  # noqa: E402
from memory_stack import mcp_server, slack_agent_server, ui_proxy  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None, help="Write facts JSON to this path.")
    parser.add_argument("--hash-output", default=None, help="Write SHA-256 of facts JSON.")
    args = parser.parse_args()

    facts = collect_facts()
    text = facts_json(facts)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if args.hash_output:
        Path(args.hash_output).write_text(f"{hash_text(text)}\n", encoding="utf-8")
    return 0


def collect_facts() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "config": collect_config_facts(),
        "http_routes": {
            "brain": app_routes(mcp_server.app),
            "cognee_ui_proxy": app_routes(ui_proxy.app),
            "slack_agent": app_routes(slack_agent_server.app),
        },
        "mcp_tools": collect_mcp_tools(),
        "workflows": collect_workflows(),
        "ui": collect_ui_facts(),
    }


def collect_config_facts() -> dict[str, Any]:
    environments = {
        name: cfg.load(name)
        for name in ("dev", "qa", "staging", "prod")
    }
    return {
        "common_keys": sorted(cfg.read_yaml(cfg.CONFIG_DIR / "common.yaml")),
        "environments": {
            name: sorted(values)
            for name, values in environments.items()
        },
        "release_metadata_keys": [
            "BRAIN_RELEASE_ENV",
            "BRAIN_RELEASE_SHA",
            "BRAIN_RELEASE_VERSION",
        ],
        "render_metadata_keys": [
            "BRAIN_CONFIG_RENDER_SHA",
            "BRAIN_CONFIG_RENDERED_AT",
            "BRAIN_CONFIG_RENDER_SOURCE",
        ],
    }


def app_routes(app: Any) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for route in app.routes:
        methods = sorted(
            method
            for method in getattr(route, "methods", set())
            if method not in {"HEAD", "OPTIONS"}
        )
        if not methods:
            continue
        routes.append(
            {
                "path": getattr(route, "path", ""),
                "methods": methods,
                "name": getattr(route, "name", ""),
                "include_in_schema": bool(getattr(route, "include_in_schema", False)),
            }
        )
    return sorted(routes, key=lambda item: (item["path"], item["methods"]))


def collect_mcp_tools() -> dict[str, list[dict[str, Any]]]:
    surfaces = {
        "chatgpt_app": mcp_server.MCP_SURFACE_CHATGPT_APP,
        "internal_admin": mcp_server.MCP_SURFACE_INTERNAL,
    }
    return {
        name: [
            {
                "name": tool["name"],
                "description": one_line(tool.get("description", "")),
                "required": sorted(tool.get("inputSchema", {}).get("required", [])),
            }
            for tool in mcp_server.memory_tool_definitions(surface=surface)
        ]
        for name, surface in surfaces.items()
    }


def collect_workflows() -> dict[str, Any]:
    workflows: dict[str, Any] = {}
    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        on_block = data.get("on", data.get(True, {}))
        dispatch = {}
        if isinstance(on_block, dict):
            dispatch = on_block.get("workflow_dispatch") or {}
        workflows[path.name] = {
            "name": data.get("name", path.stem),
            "triggers": sorted(str(key) for key in on_block) if isinstance(on_block, dict) else [],
            "workflow_dispatch_inputs": sorted((dispatch.get("inputs") or {}).keys())
            if isinstance(dispatch, dict)
            else [],
            "jobs": sorted((data.get("jobs") or {}).keys()),
        }
    return workflows


def collect_ui_facts() -> dict[str, Any]:
    app_dir = SRC_ROOT / "memory_stack" / "static" / "brain_app"
    files = {
        "html_pages": sorted(path.name for path in app_dir.glob("*.html")),
        "js_actions": javascript_actions(app_dir / "app.js"),
        "visible_text": visible_text(app_dir),
    }
    return files


def javascript_actions(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    names = set(re.findall(r"\basync function ([A-Za-z0-9_]+)\(", text))
    names.update(re.findall(r"\bfunction ([A-Za-z0-9_]+)\(", text))
    return sorted(names)


def visible_text(app_dir: Path) -> list[str]:
    snippets: set[str] = set()
    for path in app_dir.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.DOTALL | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        for snippet in re.split(r"\s{2,}|\n", text):
            cleaned = one_line(snippet)
            if 3 <= len(cleaned) <= 100:
                snippets.add(cleaned)
    return sorted(snippets)


def one_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def facts_json(facts: dict[str, Any]) -> str:
    return json.dumps(facts, indent=2, sort_keys=True) + "\n"


def hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
