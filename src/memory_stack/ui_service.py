from __future__ import annotations

import os
import signal
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import uvicorn

from memory_stack.cfg import load_settings, runtime_env


processes: list[subprocess.Popen] = []


def main() -> None:
    settings = load_settings()
    configure_environment(settings)

    frontend_dir = prepare_frontend(settings)
    start_backend(settings.brain_ui_backend_port)
    start_frontend(frontend_dir, settings.brain_ui_frontend_port)

    install_signal_handlers()
    wait_for_tcp("127.0.0.1", settings.brain_ui_backend_port, "Cognee backend")
    wait_for_http(f"http://127.0.0.1:{settings.brain_ui_frontend_port}/", "Cognee frontend")

    uvicorn.run(
        "memory_stack.ui_proxy:app",
        host=settings.brain_ui_host,
        port=settings.brain_ui_proxy_port,
        reload=False,
    )


def configure_environment(settings) -> None:
    os.environ.update(runtime_env(settings))
    os.environ.update(
        {
            "BRAIN_UI_ENABLED": "true",
            "UI_APP_URL": settings.brain_public_base_url.rstrip("/"),
            "CORS_ALLOWED_ORIGINS": settings.brain_public_base_url.rstrip("/"),
            "NEXT_PUBLIC_LOCAL_API_URL": settings.public_ui_api_url,
            "NEXT_PUBLIC_IS_CLOUD_ENVIRONMENT": "false",
            "REQUIRE_AUTHENTICATION": "false",
            "ENABLE_BACKEND_ACCESS_CONTROL": "false",
            "HTTP_API_HOST": "127.0.0.1",
            "HTTP_API_PORT": str(settings.brain_ui_backend_port),
            "HOST": "127.0.0.1",
            "PORT": str(settings.brain_ui_frontend_port),
        }
    )


def prepare_frontend(settings) -> Path:
    from cognee.api.v1.ui.ui import download_frontend_assets, find_frontend_path
    from cognee.version import get_cognee_version

    if not download_frontend_assets(force=False):
        raise RuntimeError("failed to download Cognee frontend assets")
    frontend_dir = find_frontend_path()
    if frontend_dir is None:
        raise RuntimeError("Cognee frontend cache was not found")

    isolated_dir = isolate_frontend_cache(
        frontend_dir,
        cache_root=Path(
            settings.brain_ui_cache_dir or Path(settings.brain_prod_root) / "shared" / "ui-cache"
        ),
        version=get_cognee_version(),
    )
    if not frontend_dependencies_ready(isolated_dir):
        run(["npm", "install"], cwd=isolated_dir)
    return isolated_dir


def frontend_dependencies_ready(frontend_dir: Path) -> bool:
    return (frontend_dir / "node_modules" / ".bin" / "next").exists()


def isolate_frontend_cache(frontend_dir: Path, *, cache_root: Path, version: str) -> Path:
    target_dir = cache_root / "frontend"
    marker = cache_root / "version.txt"
    try:
        if frontend_dir.resolve() == target_dir.resolve():
            return frontend_dir
    except FileNotFoundError:
        pass

    needs_refresh = (
        not target_dir.exists()
        or not (target_dir / "package.json").exists()
        or not marker.exists()
        or marker.read_text(encoding="utf-8").strip() != version
    )
    if needs_refresh:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        cache_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            frontend_dir,
            target_dir,
            ignore=shutil.ignore_patterns(".next", "node_modules"),
        )
        marker.write_text(version + "\n", encoding="utf-8")
    return target_dir


def start_backend(port: int) -> None:
    processes.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "cognee.api.client:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env=os.environ.copy(),
        )
    )


def start_frontend(frontend_dir: Path, port: int) -> None:
    processes.append(
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            env=os.environ.copy(),
        )
    )


def run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, env=os.environ.copy(), check=True)


def wait_for_http(url: str, label: str) -> None:
    for attempt in range(1, 61):
        check_child_processes()
        try:
            with urllib.request.urlopen(url, timeout=5):
                print(f"[brain-ui] {label} is ready", flush=True)
                return
        except Exception:
            if attempt == 60:
                raise RuntimeError(f"{label} did not become ready at {url}")
            time.sleep(1)


def wait_for_tcp(host: str, port: int, label: str) -> None:
    for attempt in range(1, 61):
        check_child_processes()
        try:
            with socket.create_connection((host, port), timeout=5):
                print(f"[brain-ui] {label} port is open", flush=True)
                return
        except OSError:
            if attempt == 60:
                raise RuntimeError(f"{label} did not open {host}:{port}")
            time.sleep(1)


def check_child_processes() -> None:
    for process in processes:
        if process.poll() is not None:
            raise RuntimeError(f"child process exited early: pid={process.pid}")


def install_signal_handlers() -> None:
    def stop(_signum, _frame) -> None:
        cleanup()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)


def cleanup() -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
