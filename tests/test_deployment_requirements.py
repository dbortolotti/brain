from __future__ import annotations

from pathlib import Path


def test_github_deploy_action_validates_before_deploying() -> None:
    workflow = Path(".github/workflows/deploy-local-production.yml").read_text(encoding="utf-8")

    assert "uv sync --all-extras" in workflow
    assert "uv run ruff check src tests scripts" in workflow
    assert "uv run pytest" in workflow
    assert "Render production config from GitHub Secrets" in workflow
    assert "scripts/render_prod_env.py" in workflow
    assert "force_config_override" not in workflow
    assert "--force-config-override" not in workflow
    assert "secrets.OPENAI_API_KEY" in workflow
    assert "secrets.BRAIN_AUTH_PASSWORD" in workflow
    renderer = Path("scripts/render_prod_env.py").read_text(encoding="utf-8")
    assert "brain.env.last-deployed" in renderer
    assert "BRAIN_CONFIG_RENDER_SHA" in renderer
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


def test_local_production_deploy_manages_mcp_ui_and_slack_services() -> None:
    script = Path("scripts/deploy-local-production.sh").read_text(encoding="utf-8")

    for label in ["com.brain.mcp", "com.brain.ui", "com.brain.slack-agent"]:
        assert label in script

    assert "launchd/com.brain.slack-agent.plist.template" in script
    assert 'ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"' in script
    assert 'ensure_env_var "BRAIN_SLACK_AGENT_PORT" "8003"' in script
    assert 'ensure_env_var "BRAIN_SLACK_RULES_PATH"' in script
    assert 'BRAIN_DATABASE_URL=$DATABASE_URL' in script
    assert 'ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"' in script
    assert "http://127.0.0.1:8003/slack/healthz" in script
    assert "uv run python scripts/verify_slack_agent.py" in script


def test_production_verifier_checks_brain_database_under_shared_data() -> None:
    verifier = Path("scripts/verify_mcp_production.py").read_text(encoding="utf-8")

    assert '"BRAIN_DATABASE_URL": sqlite_path(settings.brain_database_url)' in verifier


def test_cloudflare_routes_slack_to_agent_before_mcp_catchall() -> None:
    config = Path("cloudflare/config.example.yml").read_text(encoding="utf-8")

    slack_route = "path: /slack*"
    slack_service = "service: http://127.0.0.1:8003"
    mcp_catchall = "service: http://127.0.0.1:8000"

    assert slack_route in config
    assert slack_service in config
    assert config.index(slack_route) < config.index(mcp_catchall)
    assert config.index(slack_service) < config.index(mcp_catchall)
