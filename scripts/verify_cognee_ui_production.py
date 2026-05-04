#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
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
    parser.add_argument("--skip-launchd", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    failures: list[str] = []

    if not args.skip_launchd:
        check_launchd(settings.brain_ui_launchd_label, failures)

    base = f"http://{settings.brain_ui_host}:{settings.brain_ui_proxy_port}"
    check_health(f"{base}/healthz", failures)
    check_backend_health(
        f"http://127.0.0.1:{settings.brain_ui_backend_port}/health",
        failures,
    )
    check_ui_requires_auth(f"{base}{settings.brain_public_ui_path}", failures)
    check_api_requires_auth(f"{base}{settings.brain_public_ui_api_path}/api/v1/users/me", failures)

    if failures:
        for failure in failures:
            console.print(f"[red][FAIL][/red] {failure}")
        return 1

    console.print("[green][OK][/green] Cognee UI production verification passed")
    return 0


def check_health(url: str, failures: list[str]) -> None:
    status, _headers, body = fetch(url)
    if status != 200:
        failures.append(f"UI health returned {status}: {body[:200]}")
        return
    if "Brain UI" not in body:
        failures.append(f"UI health does not identify Brain UI: {body[:200]}")
        return
    console.print(f"[green][OK][/green] local UI health: {url}")


def check_backend_health(url: str, failures: list[str]) -> None:
    status, _headers, body = fetch(url)
    if status != 200:
        failures.append(f"Cognee backend health returned {status}: {body[:200]}")
        return
    if '"ready"' not in body or '"healthy"' not in body:
        failures.append(f"Cognee backend health was not ready: {body[:200]}")
        return
    console.print(f"[green][OK][/green] Cognee backend health: {url}")


def check_ui_requires_auth(url: str, failures: list[str]) -> None:
    status, headers, _body = fetch(url)
    if status not in {303, 307}:
        failures.append(f"UI did not redirect unauthenticated request; status={status}")
        return
    if "/ui-login" not in headers.get("location", ""):
        failures.append(f"UI auth redirect does not target /ui-login: {headers}")
        return
    console.print("[green][OK][/green] UI fails closed behind Brain password gate")


def check_api_requires_auth(url: str, failures: list[str]) -> None:
    status, headers, _body = fetch(url)
    if status not in {303, 307}:
        failures.append(f"UI API did not redirect unauthenticated request; status={status}")
        return
    if "/ui-login" not in headers.get("location", ""):
        failures.append(f"UI API auth redirect does not target /ui-login: {headers}")
        return
    console.print("[green][OK][/green] UI API fails closed behind Brain password gate")


def check_launchd(label: str, failures: list[str]) -> None:
    if not command_exists("launchctl"):
        failures.append("launchctl is not available")
        return
    result = subprocess.run(
        ["launchctl", "print", f"gui/{uid()}/{label}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append(f"launchd service not loaded: {label}")
        return
    if "pid =" not in result.stdout:
        failures.append(f"launchd service loaded but no pid found: {label}")
        return
    console.print(f"[green][OK][/green] launchd service running: {label}")


def fetch(url: str) -> tuple[int | None, dict[str, str], str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "brain-ui-verifier/0.1"},
        method="GET",
    )
    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        with opener.open(request, timeout=8) as response:
            return (
                response.status,
                {key.lower(): value for key, value in response.headers.items()},
                response.read().decode("utf-8", errors="replace"),
            )
    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            {key.lower(): value for key, value in exc.headers.items()},
            exc.read().decode("utf-8", errors="replace"),
        )
    except Exception as exc:
        return None, {}, str(exc)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def command_exists(command: str) -> bool:
    return subprocess.run(["/usr/bin/env", "which", command], capture_output=True).returncode == 0


def uid() -> str:
    return subprocess.check_output(["id", "-u"], text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
