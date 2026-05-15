#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cfg import load_settings
from production_check_utils import command_exists, uid


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", default=None)
    parser.add_argument("--skip-local", action="store_true")
    parser.add_argument("--skip-cloudflared", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    hostname = args.hostname or settings.brain_public_base_url.removeprefix("https://")
    failures: list[str] = []

    check_dns(hostname, failures)
    check_tls(hostname, failures)
    if not args.skip_local:
        check_url(
            f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_health_path}",
            "local health",
            failures,
            require_brain=True,
        )
    check_public_mcp(settings, failures)
    check_public_app_mcp(settings, failures)
    check_url(
        f"https://{hostname}/",
        "public Brain dashboard",
        failures,
        require_text="Brain",
    )
    for path, label in [
        ("/privacy", "public privacy page"),
        ("/terms", "public terms page"),
        ("/support", "public support page"),
    ]:
        check_url(f"https://{hostname}{path}", label, failures, require_text="Brain")
    check_protected_resource_metadata(
        f"https://{hostname}/.well-known/oauth-protected-resource{settings.brain_public_mcp_path}",
        settings,
        failures,
    )
    check_protected_resource_metadata(
        f"https://{hostname}/.well-known/oauth-protected-resource{settings.brain_public_app_mcp_path}",
        settings,
        failures,
        expected_resource=settings.public_app_mcp_url,
        label="OAuth app protected-resource metadata",
    )
    check_authorization_server_metadata(
        f"https://{hostname}/.well-known/oauth-authorization-server",
        settings,
        failures,
    )
    if not args.skip_cloudflared:
        check_cloudflared(failures)

    if failures:
        for failure in failures:
            console.print(f"[red][FAIL][/red] {failure}")
        return 1

    console.print("[green][OK][/green] Cloudflare MCP verification passed")
    return 0


def check_dns(hostname: str, failures: list[str]) -> None:
    try:
        addresses = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        failures.append(f"DNS lookup failed for {hostname}: {exc}")
        return
    if not addresses:
        failures.append(f"DNS lookup returned no addresses for {hostname}")
        return
    console.print(f"[green][OK][/green] DNS resolves for {hostname}")


def check_tls(hostname: str, failures: list[str]) -> None:
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, 443), timeout=8) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls:
                cert = tls.getpeercert()
    except Exception as exc:
        failures.append(f"TLS check failed for {hostname}: {exc}")
        return
    names = [value for key, value in cert.get("subjectAltName", []) if key == "DNS"]
    if hostname not in names and not any(name.startswith("*.") and hostname.endswith(name[1:]) for name in names):
        failures.append(f"TLS certificate SAN does not include {hostname}: {names}")
        return
    console.print(f"[green][OK][/green] TLS certificate valid for {hostname}")


def check_public_mcp(settings, failures: list[str]) -> None:
    check_public_mcp_url(
        settings.public_mcp_url,
        settings.protected_resource_metadata_url,
        settings,
        failures,
        label="public MCP",
    )


def check_public_app_mcp(settings, failures: list[str]) -> None:
    check_public_mcp_url(
        settings.public_app_mcp_url,
        settings.protected_resource_metadata_url_for_path(settings.brain_public_app_mcp_path),
        settings,
        failures,
        label="public ChatGPT App MCP",
    )


def check_public_mcp_url(
    url: str,
    expected_metadata_url: str,
    settings,
    failures: list[str],
    *,
    label: str,
) -> None:
    status, headers, body = fetch(url)
    if status is None:
        failures.append(f"{label} request failed: {body}")
        return
    if settings.brain_auth_enabled:
        if status != 401:
            failures.append(f"auth-enabled {label} did not fail closed; status={status}")
            return
        challenge = headers.get("www-authenticate") or headers.get("WWW-Authenticate") or ""
        if "Brain" not in challenge and "brain" not in challenge:
            failures.append(f"{label} auth challenge does not identify Brain: {challenge}")
            return
        if expected_metadata_url not in challenge:
            failures.append(f"{label} challenge points at wrong OAuth metadata: {challenge}")
            return
        console.print(f"[green][OK][/green] {label} fails closed with Brain auth metadata")
        return
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {body[:200]}")
        return
    if "Brain" not in body and "brain" not in body:
        failures.append(f"{label} response does not identify Brain")
        return
    console.print(f"[green][OK][/green] {label} routes to Brain")


def check_url(
    url: str,
    label: str,
    failures: list[str],
    *,
    require_brain: bool = False,
    require_text: str | None = None,
) -> None:
    status, _headers, body = fetch(url)
    if status is None:
        failures.append(f"{label} failed: {body}")
        return
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return
    if require_brain and "Brain" not in body and "brain" not in body:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body[:300]
        failures.append(f"{label} does not identify Brain: {payload}")
        return
    if require_text and require_text not in body:
        failures.append(f"{label} did not include expected text {require_text!r}")
        return
    console.print(f"[green][OK][/green] {label}: {url}")


def check_protected_resource_metadata(
    url: str,
    settings,
    failures: list[str],
    *,
    expected_resource: str | None = None,
    label: str = "OAuth protected-resource metadata",
) -> None:
    payload = fetch_json(url, label, failures)
    if not payload:
        return
    if payload.get("resource_name") != "Brain":
        failures.append(f"{label} is not Brain: {payload}")
    if payload.get("resource") != (expected_resource or settings.public_mcp_url):
        failures.append(f"{label} resource is wrong: {payload}")


def check_authorization_server_metadata(url: str, settings, failures: list[str]) -> None:
    payload = fetch_json(url, "OAuth authorization-server metadata", failures)
    if not payload:
        return
    if payload.get("service") != "Brain":
        failures.append(f"OAuth authorization-server metadata is not Brain: {payload}")
    if payload.get("issuer") != settings.brain_public_base_url.rstrip("/"):
        failures.append(f"OAuth authorization-server issuer is wrong: {payload}")


def fetch_json(url: str, label: str, failures: list[str]) -> dict | None:
    status, _headers, body = fetch(url)
    if status is None:
        failures.append(f"{label} failed: {body}")
        return None
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        failures.append(f"{label} did not return JSON: {body[:300]}")
        return None
    if "Brain" not in body and "brain" not in body:
        failures.append(f"{label} does not identify Brain: {payload}")
        return None
    console.print(f"[green][OK][/green] {label}: {url}")
    return payload


def fetch(url: str) -> tuple[int | None, dict[str, str], str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "brain-mcp-verifier/0.1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return (
                response.status,
                {k.lower(): v for k, v in response.headers.items()},
                response.read().decode("utf-8", errors="replace"),
            )
    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            {k.lower(): v for k, v in exc.headers.items()},
            exc.read().decode("utf-8", errors="replace"),
        )
    except Exception as exc:
        return None, {}, str(exc)


def check_cloudflared(failures: list[str]) -> None:
    if not command_exists("launchctl"):
        failures.append("launchctl is not available for cloudflared check")
        return
    result = subprocess.run(
        ["launchctl", "print", f"gui/{uid()}/com.cloudflare.cloudflared"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append("cloudflared launchd service is not loaded")
        return
    if "pid =" not in result.stdout:
        failures.append("cloudflared launchd service has no running pid")
        return
    console.print("[green][OK][/green] cloudflared launchd service running")


if __name__ == "__main__":
    raise SystemExit(main())
