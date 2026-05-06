from __future__ import annotations

import os
import subprocess
import sys


def test_render_prod_env_writes_github_secret_values_without_printing_them(tmp_path) -> None:
    env = {
        **os.environ,
        "BRAIN_PROD_ROOT": str(tmp_path / "prod" / "brain"),
        "OPENAI_API_KEY": "sk-prod-openai",
        "BRAIN_AUTH_PASSWORD": "prod-auth-password",
        "BRAIN_SLACK_SIGNING_SECRET": "prod-slack-signing-secret",
    }
    output = tmp_path / "brain.env"
    auth_password_file = tmp_path / "brain-auth-password"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_prod_env.py",
            "--output",
            str(output),
            "--auth-password-file",
            str(auth_password_file),
            "--no-preserve-existing",
        ],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
    )

    rendered = output.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-prod-openai" in rendered
    assert "BRAIN_SLACK_SIGNING_SECRET=prod-slack-signing-secret" in rendered
    assert auth_password_file.read_text(encoding="utf-8").strip() == "prod-auth-password"
    assert output.stat().st_mode & 0o777 == 0o600
    assert auth_password_file.stat().st_mode & 0o777 == 0o600
    assert "sk-prod-openai" not in result.stdout
    assert "prod-auth-password" not in result.stdout


def test_render_prod_env_preserves_existing_secret_when_github_secret_is_empty(tmp_path) -> None:
    output = tmp_path / "brain.env"
    output.write_text(
        "\n".join(
            [
                "PROFILE=openai",
                "OPENAI_API_KEY=sk-existing-openai",
                "BRAIN_SLACK_SIGNING_SECRET=existing-slack-secret",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "BRAIN_PROD_ROOT": str(tmp_path / "prod" / "brain"),
        "OPENAI_API_KEY": "",
        "BRAIN_SLACK_SIGNING_SECRET": "",
    }
    subprocess.run(
        [
            sys.executable,
            "scripts/render_prod_env.py",
            "--output",
            str(output),
            "--auth-password-file",
            str(tmp_path / "brain-auth-password"),
        ],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
    )

    rendered = output.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-existing-openai" in rendered
    assert "BRAIN_SLACK_SIGNING_SECRET=existing-slack-secret" in rendered
