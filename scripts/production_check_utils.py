from __future__ import annotations

import subprocess


def command_exists(command: str) -> bool:
    return subprocess.run(["/usr/bin/env", "which", command], capture_output=True).returncode == 0


def uid() -> str:
    return subprocess.check_output(["id", "-u"], text=True).strip()
