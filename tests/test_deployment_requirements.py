from __future__ import annotations

from pathlib import Path


def test_github_deploy_action_validates_before_deploying() -> None:
    workflow = Path(".github/workflows/deploy-local-production.yml").read_text(encoding="utf-8")

    assert "uv sync --all-extras" in workflow
    assert "uv run ruff check src tests scripts" in workflow
    assert "uv run pytest" in workflow
    assert "Render production config from GitHub Secrets" in workflow
    assert "scripts/render_prod_env.py" in workflow
    assert "force_config_override" in workflow
    assert "default: false" in workflow
    assert "--force-config-override" in workflow
    assert 'inputs.force_config_override }}" == "true"' in workflow
    assert "model_smoke_scope" not in workflow
    assert "BRAIN_MODEL_SMOKE_SCOPE" not in workflow
    assert "vars.OPENAI_AUTH_MODE" in workflow
    assert "vars.OPENAI_CODEX_AUTH_PROFILE" in workflow
    assert "secrets.OPENAI_API_KEY" in workflow
    assert "secrets.OPENROUTER_API_KEY" in workflow
    assert "secrets.BRAIN_AUTH_PASSWORD" in workflow
    assert "secrets.BRAIN_TASTE_OMDB_API_KEY" in workflow
    assert "vars.BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD" in workflow
    assert "vars.BRAIN_TASTE_IMPORT_SOURCE_PATH" not in workflow
    renderer = Path("scripts/render_prod_env.py").read_text(encoding="utf-8")
    assert "brain.env.last-deployed" in renderer
    assert "BRAIN_CONFIG_RENDER_SHA" in renderer
    assert "BRAIN_PROVIDER_AUTH_PROFILES_PATH" in renderer
    assert workflow.index("Validate repository") < workflow.index(
        "Render production config from GitHub Secrets"
    )
    assert workflow.index("Render production config from GitHub Secrets") < workflow.index(
        "Deploy to local LaunchAgents"
    )


def test_validation_workflow_runs_without_production_secrets() -> None:
    workflow = Path(".github/workflows/validate.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "uv sync --all-extras" in workflow
    assert "uv run ruff check src tests scripts" in workflow
    assert "uv run pytest" in workflow
    assert "secrets." not in workflow


def test_deployment_templates_live_under_deployment() -> None:
    expected = {
        Path("deployment/cloudflare/config.example.yml"),
        Path("deployment/docker-compose.prod.yml"),
        Path("deployment/launchd/com.brain.mcp.plist.template"),
        Path("deployment/launchd/com.brain.ui.plist.template"),
        Path("deployment/launchd/com.brain.slack-agent.plist.template"),
        Path("deployment/launchd/com.brain.agent-memory.plist.template"),
        Path("deployment/launchd/com.brain.log-rotation.plist.template"),
        Path("deployment/mcp/claude_desktop_config.template.json"),
        Path("deployment/newsyslog/brain.conf"),
    }

    assert all(path.exists() for path in expected)
    assert not Path("cloudflare").exists()
    assert not Path("launchd").exists()
    assert not Path("mcp").exists()


def test_production_docker_compose_runs_pgvector_and_neo4j() -> None:
    compose = Path("deployment/docker-compose.prod.yml").read_text(encoding="utf-8")

    assert "brain-prod-postgres" in compose
    assert "pgvector/pgvector:pg16" in compose
    assert "127.0.0.1:${DB_PORT:-15432}:5432" in compose
    assert "./postgres/initdb:/docker-entrypoint-initdb.d:ro" in compose
    assert "CREATE EXTENSION IF NOT EXISTS vector" in Path(
        "deployment/postgres/initdb/001-vector.sql"
    ).read_text(encoding="utf-8")
    assert "brain-prod-neo4j" in compose


def test_local_production_deploy_manages_mcp_ui_and_slack_services() -> None:
    script = Path("scripts/deploy-local-production.sh").read_text(encoding="utf-8")

    for label in [
        "com.brain.prod.mcp",
        "com.brain.prod.ui",
        "com.brain.prod.slack-agent",
        "com.brain.prod.agent-memory",
        "com.brain.prod.log-rotation",
    ]:
        assert label in script

    assert 'DEPLOYMENT_CONFIG_DIR="$REPO_ROOT/deployment"' in script
    assert "deployment" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.agent-memory.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.log-rotation.plist.template" in script
    assert 'ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"' in script
    assert 'set_env_var "BRAIN_SLACK_AGENT_PORT" "18003"' in script
    assert 'BRAIN_DATABASE_URL=$DATABASE_URL' in script
    assert 'ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"' in script
    assert "LLM_MODEL=gpt-5.4-mini" in script
    assert "LLM_TEMPERATURE=0.0" in script
    assert "LLM_MAX_TOKENS=8192" in script
    assert 'ensure_env_var "BRAIN_PROVIDER_AUTH_PROFILES_PATH"' in script
    assert 'set_env_var "BRAIN_REQUEST_LOG_PATH" "$LOG_DIR/requests/{date}.jsonl"' in script
    assert 'set_env_var "BRAIN_REQUEST_LOG_MAX_BODY_BYTES" "8192"' in script
    assert 'ensure_env_var "BRAIN_REQUEST_LOG_RETENTION_DAYS" "30"' in script
    assert 'ensure_env_var "BRAIN_ROUTING_LOG_ENABLED" "true"' in script
    assert 'set_env_var "BRAIN_ROUTING_LOG_PATH" "$LOG_DIR/routing/{date}.jsonl"' in script
    assert 'ensure_env_var "BRAIN_ROUTING_LOG_RETENTION_DAYS" "90"' in script
    assert "install_newsyslog_config()" in script
    assert 'NEWSYSLOG_DST="/etc/newsyslog.d/brain.conf"' in script
    assert "enable_launch_agent()" in script
    assert 'launchctl enable "$domain/$label"' in script
    assert 'enable_launch_agent "$LABEL" "$PLIST_DST"' in script
    assert 'enable_launch_agent "$UI_LABEL" "$UI_PLIST_DST"' in script
    assert 'enable_launch_agent "$SLACK_LABEL" "$SLACK_PLIST_DST"' in script
    assert 'enable_launch_agent "$AGENT_MEMORY_LABEL" "$AGENT_MEMORY_PLIST_DST"' in script
    assert 'enable_launch_agent "$LOG_ROTATION_LABEL" "$LOG_ROTATION_PLIST_DST"' in script
    assert 'ensure_env_var "BRAIN_TASTE_ENABLED" "true"' in script
    assert 'ensure_env_var "BRAIN_TASTE_LLM_ROUTING_ENABLED" "false"' in script
    assert 'ensure_env_var "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD" "0.80"' in script
    assert 'ensure_env_var "BRAIN_TASTE_IMPORT_SOURCE_PATH"' not in script
    assert "${BRAIN_SLACK_AGENT_PORT:-18003}/slack/healthz" in script
    assert "uv run python scripts/verify_slack_agent.py" in script
    assert 'ensure_env_var "BRAIN_AGENT_MEMORY_SESSION_ID" "portable_agent_session"' in script
    assert "docker compose -f deployment/docker-compose.prod.yml up -d postgres neo4j" in script
    assert 'set_env_var "VECTOR_DB_PROVIDER" "pgvector"' in script
    assert 'set_env_var "VECTOR_DB_PORT" "15432"' in script
    assert 'set_env_var "VECTOR_DATASET_DATABASE_HANDLER" "pgvector"' in script
    assert 'set_env_var "DB_PROVIDER" "postgres"' in script
    assert 'set_env_var "DB_PORT" "15432"' in script
    assert "GRAPH_DATABASE_PASSWORD must be set to a real secret" in script
    assert "uv run python scripts/live_model_smoke.py" in script
    assert 'MODEL_SMOKE_SCOPE="${BRAIN_MODEL_SMOKE_SCOPE:-active}"' in script
    assert "--exclude '.env'" in script
    assert 'rm -f "$RELEASE_DIR/.env"' in script
    assert script.index("uv run python scripts/live_model_smoke.py") < script.index(
        'ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"'
    )
    assert script.index("uv run python scripts/live_model_smoke.py") < script.index(
        "waiting for local health"
    )


def test_mcp_launchd_uses_dated_request_and_routing_logs() -> None:
    plist = Path("deployment/launchd/com.brain.mcp.plist.template").read_text(
        encoding="utf-8"
    )

    assert "/Volumes/xpg_usb4/prod/brain/shared/logs/requests/{date}.jsonl" in plist
    assert "<key>BRAIN_REQUEST_LOG_MAX_BODY_BYTES</key>" in plist
    assert "<string>8192</string>" in plist
    assert "<key>BRAIN_REQUEST_LOG_RETENTION_DAYS</key>" in plist
    assert "<string>30</string>" in plist
    assert "<key>BRAIN_ROUTING_LOG_ENABLED</key>" in plist
    assert "/Volumes/xpg_usb4/prod/brain/shared/logs/routing/{date}.jsonl" in plist
    assert "<key>BRAIN_ROUTING_LOG_RETENTION_DAYS</key>" in plist
    assert "<string>90</string>" in plist


def test_newsyslog_rotates_launchd_logs_daily() -> None:
    config = Path("deployment/newsyslog/brain.conf").read_text(encoding="utf-8")

    assert "brain-prod.err.log" in config
    assert "brain-ui.err.log" in config
    assert "brain-slack-agent.err.log" in config
    assert "@T00" in config
    assert " J" in config


def test_agent_memory_launchd_runs_nightly_at_3am() -> None:
    plist = Path("deployment/launchd/com.brain.agent-memory.plist.template").read_text(
        encoding="utf-8"
    )

    assert "com.brain.prod.agent-memory" in plist
    assert "scripts/brain_agent_memory.py" in plist
    assert "--env prod" in plist
    assert "--env-file /Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env" in plist
    assert "--session-id portable_agent_session" in plist
    assert "<key>StartCalendarInterval</key>" in plist
    assert "<key>Hour</key>" in plist
    assert "<integer>3</integer>" in plist
    assert "<key>Minute</key>" in plist
    assert "<integer>0</integer>" in plist


def test_log_rotation_launchd_runs_daily_after_midnight() -> None:
    plist = Path("deployment/launchd/com.brain.log-rotation.plist.template").read_text(
        encoding="utf-8"
    )

    assert "com.brain.prod.log-rotation" in plist
    assert "scripts/rotate_launchd_logs.py" in plist
    assert "--retention-days 30" in plist
    assert "<key>StartCalendarInterval</key>" in plist
    assert "<key>Hour</key>" in plist
    assert "<integer>0</integer>" in plist
    assert "<key>Minute</key>" in plist
    assert "<integer>5</integer>" in plist


def test_cognee_ui_verifier_retries_backend_health() -> None:
    verifier = Path("scripts/verify_cognee_ui_production.py").read_text(encoding="utf-8")

    assert "for _attempt in range(30):" in verifier
    assert "time.sleep(2)" in verifier


def test_production_verifier_checks_brain_database_under_shared_data() -> None:
    verifier = Path("scripts/verify_mcp_production.py").read_text(encoding="utf-8")

    assert '"BRAIN_DATABASE_URL": sqlite_path(settings.brain_database_url)' in verifier
    assert 'if getattr(settings, "vector_db_provider", "lancedb") == "lancedb":' in verifier
    assert 'paths["VECTOR_DB_URL"] = Path(settings.vector_db_url)' in verifier


def test_cloudflare_routes_slack_to_agent_before_mcp_catchall() -> None:
    config = Path("deployment/cloudflare/config.example.yml").read_text(encoding="utf-8")

    slack_route = "path: /slack*"
    slack_service = "service: http://127.0.0.1:18003"
    mcp_catchall = "service: http://127.0.0.1:18000"

    assert slack_route in config
    assert slack_service in config
    assert config.index(slack_route) < config.index(mcp_catchall)
    assert config.index(slack_service) < config.index(mcp_catchall)
