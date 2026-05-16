from __future__ import annotations

import os
import subprocess
import sys


def run_renderer(tmp_path, env_overrides, *, check=True):
    output = tmp_path / "brain.env"
    auth_password_file = tmp_path / "brain-auth-password"
    env = {
        **os.environ,
        "BRAIN_PROD_ROOT": str(tmp_path / "prod" / "brain"),
        "OPENAI_API_KEY": "sk-prod-openai",
        "OPENROUTER_API_KEY": "sk-prod-openrouter",
        "GRAPH_DATABASE_PASSWORD": "prod-graph-password",
        "BRAIN_AUTH_PASSWORD": "prod-auth-password",
        "GITHUB_SHA": "abc123",
        **env_overrides,
    }
    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_prod_env.py",
            "--output",
            str(output),
            "--auth-password-file",
            str(auth_password_file),
        ],
        check=check,
        capture_output=True,
        encoding="utf-8",
        env=env,
    )
    return result, output, auth_password_file


def run_renderer_with_args(tmp_path, env_overrides, extra_args, *, check=True):
    output = tmp_path / "brain.env"
    auth_password_file = tmp_path / "brain-auth-password"
    env = {
        **os.environ,
        "BRAIN_PROD_ROOT": str(tmp_path / "prod" / "brain"),
        "OPENAI_API_KEY": "sk-prod-openai",
        "OPENROUTER_API_KEY": "sk-prod-openrouter",
        "GRAPH_DATABASE_PASSWORD": "prod-graph-password",
        "BRAIN_AUTH_PASSWORD": "prod-auth-password",
        "GITHUB_SHA": "abc123",
        **env_overrides,
    }
    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_prod_env.py",
            "--output",
            str(output),
            "--auth-password-file",
            str(auth_password_file),
            *extra_args,
        ],
        check=check,
        capture_output=True,
        encoding="utf-8",
        env=env,
    )
    return result, output, auth_password_file


def parse_rendered_env(rendered: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in rendered.splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_render_prod_env_writes_github_secret_values_without_printing_them(tmp_path) -> None:
    result, output, auth_password_file = run_renderer(
        tmp_path,
        {"BRAIN_SLACK_SIGNING_SECRET": "prod-slack-signing-secret"},
    )

    rendered = output.read_text(encoding="utf-8")
    base_rendered = output.with_name("brain.env.last-deployed").read_text(encoding="utf-8")
    assert "BRAIN_CONFIG_RENDER_SHA=abc123" in rendered
    assert "OPENAI_AUTH_MODE=oauth" in rendered
    assert "OPENAI_CODEX_AUTH_PROFILE=default" in rendered
    assert "LLM_PROVIDER=openai" in rendered
    assert "LLM_MODEL=gpt-5.4-mini" in rendered
    assert "EMBEDDING_PROVIDER=openai" in rendered
    assert "EMBEDDING_MODEL=text-embedding-3-large" in rendered
    assert "EMBEDDING_DIMENSIONS=3072" in rendered
    assert "VECTOR_DB_PROVIDER=pgvector" in rendered
    assert "VECTOR_DB_PORT=15432" in rendered
    assert "VECTOR_DATASET_DATABASE_HANDLER=pgvector" in rendered
    assert "VECTOR_DB_HOST=127.0.0.1" in rendered
    assert "DB_PROVIDER=postgres" in rendered
    assert "DB_PORT=15432" in rendered
    assert "OPENAI_API_KEY=sk-prod-openai" in rendered
    assert "OPENROUTER_API_KEY=sk-prod-openrouter" in rendered
    assert "GRAPH_DATABASE_PASSWORD=prod-graph-password" in rendered
    assert "BRAIN_TASTE_ENABLED=true" in rendered
    assert "BRAIN_TASTE_LLM_MODEL=gpt-5.5" in rendered
    assert "BRAIN_TASTE_LLM_REASONING_EFFORT=medium" in rendered
    assert "BRAIN_TASTE_LLM_ROUTING_ENABLED=false" in rendered
    assert "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD=0.80" in rendered
    assert "BRAIN_OWNER_FULL_NAME='Daniele Bortolotti'" in rendered
    assert "BRAIN_OWNER_NAME=Daniele" in rendered
    assert (
        "BRAIN_PROFILE_CONTEXT_PATH=/Volumes/xpg_usb4/prod/brain/shared/data/brain/profile_context.json"
        in rendered
    )
    assert "BRAIN_AUTH_USERS_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-users.json" in rendered
    assert "BRAIN_AUTH_SUPERUSER_IDS=default" in rendered
    assert "BRAIN_AGENT_MEMORY_SESSION_ID=portable_agent_session" in rendered
    assert "BRAIN_REQUEST_LOG_PATH=/Volumes/xpg_usb4/prod/brain/shared/logs/requests/{date}.jsonl" in rendered
    assert "BRAIN_REQUEST_LOG_MAX_BODY_BYTES=8192" in rendered
    assert "BRAIN_REQUEST_LOG_RETENTION_DAYS=30" in rendered
    assert "BRAIN_ROUTING_LOG_ENABLED=true" in rendered
    assert "BRAIN_ROUTING_LOG_PATH=/Volumes/xpg_usb4/prod/brain/shared/logs/routing/{date}.jsonl" in rendered
    assert "BRAIN_ROUTING_LOG_RETENTION_DAYS=90" in rendered
    assert "BRAIN_TASTE_IMPORT_SOURCE_PATH" not in rendered
    assert "BRAIN_SLACK_SIGNING_SECRET=prod-slack-signing-secret" in rendered
    assert base_rendered == rendered
    assert auth_password_file.read_text(encoding="utf-8").strip() == "prod-auth-password"
    assert (
        auth_password_file.with_name("brain-auth-password.last-deployed")
        .read_text(encoding="utf-8")
        .strip()
        == "prod-auth-password"
    )
    assert output.stat().st_mode & 0o777 == 0o600
    assert output.with_name("brain.env.last-deployed").stat().st_mode & 0o777 == 0o600
    assert auth_password_file.stat().st_mode & 0o777 == 0o600
    assert "sk-prod-openai" not in result.stdout
    assert "prod-auth-password" not in result.stdout


def test_render_prod_env_can_render_staging_defaults(tmp_path) -> None:
    _, output, _ = run_renderer_with_args(
        tmp_path,
        {
            "BRAIN_PROD_ROOT": "",
            "BRAIN_PUBLIC_BASE_URL": "",
            "BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED": "",
        },
        ["--env", "staging"],
    )

    values = parse_rendered_env(output.read_text(encoding="utf-8"))
    assert values["BRAIN_PROD_ROOT"] == "/Volumes/xpg_usb4/staging/brain"
    assert values["BRAIN_PUBLIC_BASE_URL"] == "https://brain-staging.dceb.net"
    assert (
        values["BRAIN_DATABASE_URL"]
        == "sqlite:////Volumes/xpg_usb4/staging/brain/shared/data/brain/brain.db"
    )
    assert values["BRAIN_MCP_PORT"] == "18100"
    assert values["BRAIN_UI_PROXY_PORT"] == "18102"
    assert values["BRAIN_UI_FRONTEND_PORT"] == "13100"
    assert values["BRAIN_UI_BACKEND_PORT"] == "18101"
    assert values["BRAIN_SLACK_AGENT_PORT"] == "18103"
    assert values["BRAIN_AUTH_USERS_FILE"] == "/Volumes/xpg_usb4/staging/brain/shared/secrets/brain-auth-users.json"
    assert values["BRAIN_AUTH_SUPERUSER_IDS"] == "default"
    assert values["VECTOR_DB_PORT"] == "16432"
    assert values["DB_PORT"] == "16432"
    assert values["BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED"] == "false"


def test_render_prod_env_uses_cfg_for_fixed_runtime_model_values(tmp_path) -> None:
    _, output, _ = run_renderer(
        tmp_path,
        {
            "LLM_MODEL": "gpt-5.5",
            "LLM_TEMPERATURE": "0.9",
            "LLM_MAX_TOKENS": "123",
            "EMBEDDING_MODEL": "text-embedding-3-small",
            "EMBEDDING_DIMENSIONS": "1536",
            "BRAIN_REQUEST_LOG_MAX_BODY_BYTES": "0",
            "BRAIN_ROUTING_LOG_ENABLED": "false",
        },
    )

    values = parse_rendered_env(output.read_text(encoding="utf-8"))
    assert values["LLM_MODEL"] == "gpt-5.4-mini"
    assert values["LLM_TEMPERATURE"] == "0.0"
    assert values["LLM_MAX_TOKENS"] == "8192"
    assert values["EMBEDDING_MODEL"] == "text-embedding-3-large"
    assert values["EMBEDDING_DIMENSIONS"] == "3072"
    assert values["BRAIN_REQUEST_LOG_MAX_BODY_BYTES"] == "8192"
    assert values["BRAIN_ROUTING_LOG_ENABLED"] == "true"
    assert values["BRAIN_TASTE_LLM_MODEL"] == "gpt-5.5"


def test_render_prod_env_allows_blank_openai_key_in_oauth_mode(tmp_path) -> None:
    _, output, _ = run_renderer(
        tmp_path,
        {
            "OPENAI_AUTH_MODE": "oauth",
            "OPENAI_API_KEY": "",
        },
    )

    rendered = output.read_text(encoding="utf-8")
    assert "OPENAI_AUTH_MODE=oauth" in rendered
    assert "OPENAI_API_KEY" not in rendered


def test_render_prod_env_requires_openai_key_in_api_key_mode(tmp_path) -> None:
    result, _, _ = run_renderer(
        tmp_path,
        {
            "OPENAI_AUTH_MODE": "api_key",
            "OPENAI_API_KEY": "",
        },
        check=False,
    )

    assert result.returncode == 2
    assert "OPENAI_API_KEY" in result.stderr


def test_render_prod_env_overwrites_when_prod_matches_last_deployed(tmp_path) -> None:
    output = tmp_path / "brain.env"
    base = output.with_name("brain.env.last-deployed")
    old_rendered = "\n".join(
        [
            "BRAIN_CONFIG_RENDER_SHA=old-sha",
            "PROFILE=openai",
            "OPENAI_API_KEY=sk-old-openai",
            "GRAPH_DATABASE_PASSWORD=old-graph-password",
        ]
    )
    output.write_text(old_rendered + "\n", encoding="utf-8")
    base.write_text(old_rendered + "\n", encoding="utf-8")
    auth_password_file = tmp_path / "brain-auth-password"
    auth_password_base = tmp_path / "brain-auth-password.last-deployed"
    auth_password_file.write_text("old-auth-password\n", encoding="utf-8")
    auth_password_base.write_text("old-auth-password\n", encoding="utf-8")

    run_renderer(tmp_path, {"OPENAI_API_KEY": "sk-new-openai"})

    rendered = output.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-new-openai" in rendered
    assert "GRAPH_DATABASE_PASSWORD=prod-graph-password" in rendered
    assert output.with_name("brain.env.last-deployed").read_text(encoding="utf-8") == rendered
    assert auth_password_file.read_text(encoding="utf-8").strip() == "prod-auth-password"


def test_render_prod_env_fails_when_prod_config_was_manually_changed(tmp_path) -> None:
    output = tmp_path / "brain.env"
    base = output.with_name("brain.env.last-deployed")
    base.write_text(
        "PROFILE=openai\nOPENAI_API_KEY=sk-old-openai\nGRAPH_DATABASE_PASSWORD=old-graph\n",
        encoding="utf-8",
    )
    output.write_text(
        "PROFILE=openai\nOPENAI_API_KEY=sk-manual-openai\nGRAPH_DATABASE_PASSWORD=old-graph\n",
        encoding="utf-8",
    )
    auth_password_file = tmp_path / "brain-auth-password"
    auth_password_base = tmp_path / "brain-auth-password.last-deployed"
    auth_password_file.write_text("old-auth-password\n", encoding="utf-8")
    auth_password_base.write_text("old-auth-password\n", encoding="utf-8")

    result, _, _ = run_renderer(
        tmp_path,
        {"OPENAI_API_KEY": "sk-github-openai"},
        check=False,
    )

    assert result.returncode == 3
    assert "OPENAI_API_KEY" in result.stderr
    assert "sk-manual-openai" not in result.stderr
    assert "sk-github-openai" not in result.stderr


def test_render_prod_env_ignores_render_metadata_conflicts(tmp_path) -> None:
    output = tmp_path / "brain.env"
    base = output.with_name("brain.env.last-deployed")
    base.write_text(
        "BRAIN_CONFIG_RENDER_SHA=old-sha\n"
        "PROFILE=openai\n"
        "OPENAI_API_KEY=sk-prod-openai\n"
        "GRAPH_DATABASE_PASSWORD=prod-graph-password\n",
        encoding="utf-8",
    )
    output.write_text(
        "BRAIN_CONFIG_RENDER_SHA=hotfix-sha\n"
        "PROFILE=openai\n"
        "OPENAI_API_KEY=sk-prod-openai\n"
        "GRAPH_DATABASE_PASSWORD=prod-graph-password\n",
        encoding="utf-8",
    )
    auth_password_file = tmp_path / "brain-auth-password"
    auth_password_base = tmp_path / "brain-auth-password.last-deployed"
    auth_password_file.write_text("prod-auth-password\n", encoding="utf-8")
    auth_password_base.write_text("prod-auth-password\n", encoding="utf-8")

    run_renderer(tmp_path, {"GITHUB_SHA": "new-sha"})

    assert "BRAIN_CONFIG_RENDER_SHA=new-sha" in output.read_text(encoding="utf-8")


def test_render_prod_env_fails_when_last_deployed_snapshot_is_missing(tmp_path) -> None:
    output = tmp_path / "brain.env"
    output.write_text(
        "PROFILE=openai\nOPENAI_API_KEY=sk-prod-openai\nGRAPH_DATABASE_PASSWORD=prod-graph\n",
        encoding="utf-8",
    )

    result, _, _ = run_renderer(tmp_path, {}, check=False)

    assert result.returncode == 3
    assert "brain.env.last-deployed" in result.stderr


def test_render_prod_env_force_config_override_rebaselines_prod(tmp_path) -> None:
    output = tmp_path / "brain.env"
    output.write_text(
        "PROFILE=openai\nOPENAI_API_KEY=sk-manual-openai\nGRAPH_DATABASE_PASSWORD=manual\n",
        encoding="utf-8",
    )

    result, _, auth_password_file = run_renderer_with_args(
        tmp_path,
        {"OPENAI_API_KEY": "sk-github-openai"},
        ["--force-config-override"],
    )

    rendered = output.read_text(encoding="utf-8")
    assert result.returncode == 0
    assert "OPENAI_API_KEY=sk-github-openai" in rendered
    assert "GRAPH_DATABASE_PASSWORD=prod-graph-password" in rendered
    assert output.with_name("brain.env.last-deployed").read_text(encoding="utf-8") == rendered
    assert (
        auth_password_file.with_name("brain-auth-password.last-deployed")
        .read_text(encoding="utf-8")
        .strip()
        == "prod-auth-password"
    )
