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
        Path("deployment/mcp/claude_desktop_config.template.json"),
    }

    assert all(path.exists() for path in expected)
    assert not Path("cloudflare").exists()
    assert not Path("launchd").exists()
    assert not Path("mcp").exists()


def test_local_production_deploy_manages_mcp_ui_and_slack_services() -> None:
    script = Path("scripts/deploy-local-production.sh").read_text(encoding="utf-8")

    for label in [
        "com.brain.prod.mcp",
        "com.brain.prod.ui",
        "com.brain.prod.slack-agent",
        "com.brain.prod.agent-memory",
    ]:
        assert label in script

    assert 'DEPLOYMENT_CONFIG_DIR="$REPO_ROOT/deployment"' in script
    assert "deployment" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.agent-memory.plist.template" in script
    assert 'ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"' in script
    assert 'set_env_var "BRAIN_SLACK_AGENT_PORT" "18003"' in script
    assert 'BRAIN_DATABASE_URL=$DATABASE_URL' in script
    assert 'ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"' in script
    assert 'ensure_env_var "BRAIN_PROVIDER_AUTH_PROFILES_PATH"' in script
    assert 'ensure_env_var "BRAIN_TASTE_ENABLED" "true"' in script
    assert 'ensure_env_var "BRAIN_TASTE_LLM_ROUTING_ENABLED" "false"' in script
    assert 'ensure_env_var "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD" "0.80"' in script
    assert 'ensure_env_var "BRAIN_TASTE_IMPORT_SOURCE_PATH"' not in script
    assert "${BRAIN_SLACK_AGENT_PORT:-18003}/slack/healthz" in script
    assert "uv run python scripts/verify_slack_agent.py" in script
    assert 'ensure_env_var "BRAIN_AGENT_MEMORY_SESSION_ID" "portable_agent_session"' in script
    assert "docker compose -f deployment/docker-compose.prod.yml up -d neo4j" in script
    assert "GRAPH_DATABASE_PASSWORD must be set to a real secret" in script
    assert "uv run python scripts/live_model_smoke.py" in script
    assert 'MODEL_SMOKE_SCOPE="${BRAIN_MODEL_SMOKE_SCOPE:-active}"' in script
    assert script.index("uv run python scripts/live_model_smoke.py") < script.index(
        'ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"'
    )
    assert script.index("uv run python scripts/live_model_smoke.py") < script.index(
        "waiting for local health"
    )


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


def test_production_verifier_checks_brain_database_under_shared_data() -> None:
    verifier = Path("scripts/verify_mcp_production.py").read_text(encoding="utf-8")

    assert '"BRAIN_DATABASE_URL": sqlite_path(settings.brain_database_url)' in verifier


def test_cloudflare_routes_slack_to_agent_before_mcp_catchall() -> None:
    config = Path("deployment/cloudflare/config.example.yml").read_text(encoding="utf-8")

    slack_route = "path: /slack*"
    slack_service = "service: http://127.0.0.1:18003"
    mcp_catchall = "service: http://127.0.0.1:18000"

    assert slack_route in config
    assert slack_service in config
    assert config.index(slack_route) < config.index(mcp_catchall)
    assert config.index(slack_service) < config.index(mcp_catchall)
