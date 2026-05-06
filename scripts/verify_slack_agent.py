#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.config import load_settings


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()
    settings = load_settings()
    base_url = args.base_url or (
        f"http://{settings.brain_slack_agent_host}:{settings.brain_slack_agent_port}"
    )
    failures: list[str] = []

    check_health(base_url, failures)
    check_mcp_separation(base_url, failures)
    check_signature_failure(base_url, failures)

    if failures:
        for failure in failures:
            console.print(f"[red][FAIL][/red] {failure}")
        return 1
    console.print("[green][OK][/green] Slack agent verification passed")
    return 0


def check_health(base_url: str, failures: list[str]) -> None:
    payload = get_json(f"{base_url}/slack/healthz", failures, label="slack health")
    if payload and payload.get("service") != "brain-slack-agent":
        failures.append(f"unexpected Slack health payload: {payload}")


def check_mcp_separation(base_url: str, failures: list[str]) -> None:
    status, _body = post(f"{base_url}/mcp", b"{}", headers={"Content-Type": "application/json"})
    if status != 404:
        failures.append(f"Slack agent must not serve /mcp; got HTTP {status}")
    else:
        console.print("[green][OK][/green] Slack agent does not serve /mcp")


def check_signature_failure(base_url: str, failures: list[str]) -> None:
    status, _body = post(
        f"{base_url}/slack/events",
        json.dumps({"type": "url_verification", "challenge": "x"}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": "1700000000",
            "X-Slack-Signature": "v0=bad",
        },
    )
    if status not in {401, 503}:
        failures.append(f"Slack invalid signature should fail closed; got HTTP {status}")
    else:
        console.print("[green][OK][/green] Slack invalid signature fails closed")


def get_json(url: str, failures: list[str], *, label: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except Exception as exc:
        failures.append(f"{label} failed at {url}: {exc}")
        return None
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return None
    console.print(f"[green][OK][/green] {label}: {url}")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        failures.append(f"{label} did not return JSON")
        return None


def post(url: str, body: bytes, *, headers: dict[str, str]) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


if __name__ == "__main__":
    raise SystemExit(main())
