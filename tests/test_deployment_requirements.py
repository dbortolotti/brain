from __future__ import annotations

from pathlib import Path


def test_github_deploy_action_validates_before_deploying() -> None:
    workflow = Path(".github/workflows/deploy-local-production.yml").read_text(encoding="utf-8")

    assert "push:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "uv sync --all-extras" in workflow
    assert "uv run ruff check src tests scripts" in workflow
    assert "uv run pytest" in workflow
    assert "Render production config from GitHub Secrets" in workflow
    assert "scripts/render_prod_env.py --env prod" in workflow
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
    assert "BRAIN_DEPLOY_ENV=prod ./scripts/deploy-local-production.sh" in workflow


def test_github_staging_action_deploys_main_to_staging() -> None:
    workflow = Path(".github/workflows/deploy-local-staging.yml").read_text(encoding="utf-8")

    assert "push:" in workflow
    assert "main" in workflow
    assert "group: brain-staging" in workflow
    assert "uv sync --all-extras" in workflow
    assert "uv run ruff check src tests scripts" in workflow
    assert "uv run pytest" in workflow
    assert "Render staging config from GitHub Secrets" in workflow
    assert "Resolve staging version" in workflow
    assert "BRAIN_RELEASE_VERSION" in workflow
    assert "Tag staged release" in workflow
    assert "BRAIN_DEPLOY_ENV: staging" in workflow
    assert "BRAIN_PUBLIC_BASE_URL: https://brain-staging.dceb.net" in workflow
    assert 'BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED: "false"' in workflow
    assert "scripts/render_prod_env.py --env staging" in workflow
    assert "BRAIN_DEPLOY_ENV=staging ./scripts/deploy-local-production.sh" in workflow
    assert workflow.index("Validate repository") < workflow.index(
        "Render staging config from GitHub Secrets"
    )
    assert workflow.index("Render staging config from GitHub Secrets") < workflow.index(
        "Deploy to local staging LaunchAgents"
    )


def test_release_action_promotes_staging_sha_to_prod_and_tags() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "version:" in workflow
    assert "contents: write" in workflow
    assert "/Volumes/xpg_usb4/staging/brain/current" in workflow
    assert "/Volumes/xpg_usb4/staging/brain/shared/release.json" in workflow
    assert "readlink \"$STAGING_CURRENT\"" in workflow
    assert "requested version $TAG is not the staged version" in workflow
    assert "tag $TAG does not exist; deploy it to staging first" in workflow
    assert "git checkout \"$STAGING_SHA\"" in workflow
    assert "BRAIN_RELEASE_VERSION" in workflow
    assert "scripts/render_prod_env.py --env prod" in workflow
    assert "BRAIN_DEPLOY_ENV=prod ./scripts/deploy-local-production.sh" in workflow
    assert "git tag -a" not in workflow
    assert "git push origin" not in workflow
    assert "Verify promoted release tag" in workflow
    assert workflow.index("Resolve staging release") < workflow.index("Validate staged revision")
    assert workflow.index("Validate staged revision") < workflow.index(
        "Render production config from GitHub Secrets"
    )
    assert workflow.index("Promote staging revision to production") < workflow.index(
        "Verify promoted release tag"
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
        Path("deployment/launchd/com.brain.maintenance.plist.template"),
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

    assert "name: ${BRAIN_DOCKER_PROJECT:-brain-prod}" in compose
    assert "brain-prod-postgres" in compose
    assert "${BRAIN_POSTGRES_CONTAINER:-brain-prod-postgres}" in compose
    assert "pgvector/pgvector:pg16" in compose
    assert "127.0.0.1:${DB_PORT:-15432}:5432" in compose
    assert "./postgres/initdb:/docker-entrypoint-initdb.d:ro" in compose
    assert "CREATE EXTENSION IF NOT EXISTS vector" in Path(
        "deployment/postgres/initdb/001-vector.sql"
    ).read_text(encoding="utf-8")
    assert "brain-prod-neo4j" in compose
    assert "${BRAIN_NEO4J_CONTAINER:-brain-prod-neo4j}" in compose
    assert "127.0.0.1:${BRAIN_NEO4J_HTTP_PORT:-17474}:7474" in compose
    assert "127.0.0.1:${BRAIN_NEO4J_BOLT_PORT:-17687}:7687" in compose


def test_local_production_deploy_manages_mcp_ui_and_slack_services() -> None:
    script = Path("scripts/deploy-local-production.sh").read_text(encoding="utf-8")

    assert 'DEPLOY_ENV="${BRAIN_DEPLOY_ENV:-prod}"' in script
    assert 'DEFAULT_ROOT="/Volumes/xpg_usb4/$DEPLOY_ENV/brain"' in script
    assert 'DEFAULT_PUBLIC_BASE_URL="https://brain-staging.dceb.net"' in script
    assert 'BRAIN_DOCKER_PROJECT="${BRAIN_DOCKER_PROJECT:-brain-$ENV_SUFFIX}"' in script
    for label in [
        'com.brain.$ENV_SUFFIX.mcp',
        'com.brain.$ENV_SUFFIX.ui',
        'com.brain.$ENV_SUFFIX.slack-agent',
        'com.brain.$ENV_SUFFIX.maintenance',
        'com.brain.$ENV_SUFFIX.log-rotation',
    ]:
        assert label in script

    assert 'DEPLOYMENT_CONFIG_DIR="$REPO_ROOT/deployment"' in script
    assert "deployment" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.maintenance.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.log-rotation.plist.template" in script
    assert "disable_launch_agent" in script
    assert 'com.brain.$ENV_SUFFIX.agent-memory' in script
    assert 'com.brain.$ENV_SUFFIX.backup' in script
    assert 'ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"' in script
    assert 'set_env_var "BRAIN_SLACK_AGENT_PORT" "$BRAIN_SLACK_AGENT_PORT"' in script
    assert 'BRAIN_DATABASE_URL=$DATABASE_URL' in script
    assert 'BRAIN_PROD_ROOT=$PROD_ROOT' in script
    assert 'BRAIN_RELEASE_VERSION=$FALLBACK_RELEASE_VERSION' in script
    assert 'write_release_metadata "$RELEASE_DIR/release.json"' in script
    assert 'write_release_metadata "$SHARED_DIR/release.json"' in script
    assert 'ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"' in script
    assert 'BRAIN_AUTH_USERS_FILE=$SECRETS_DIR/brain-auth-users.json' in script
    assert 'BRAIN_AUTH_SUPERUSER_IDS=default' in script
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
    assert 'enable_launch_agent "$MAINTENANCE_LABEL" "$MAINTENANCE_PLIST_DST"' in script
    assert 'enable_launch_agent "$LOG_ROTATION_LABEL" "$LOG_ROTATION_PLIST_DST"' in script
    assert 'disable_launch_agent "$LEGACY_AGENT_MEMORY_LABEL" "$LEGACY_AGENT_MEMORY_PLIST_DST"' in script
    assert 'disable_launch_agent "$LEGACY_BACKUP_LABEL" "$LEGACY_BACKUP_PLIST_DST"' in script
    assert 'ensure_env_var "BRAIN_LLM_ENABLED" "false"' in script
    assert 'ensure_env_var "BRAIN_TASTE_ENABLED" "true"' in script
    assert 'ensure_env_var "BRAIN_TASTE_LLM_ROUTING_ENABLED" "false"' in script
    assert 'ensure_env_var "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD" "0.80"' in script
    assert 'ensure_env_var "BRAIN_TASTE_IMPORT_SOURCE_PATH"' not in script
    assert "${BRAIN_SLACK_AGENT_PORT:-18003}/slack/healthz" in script
    assert "uv run python scripts/verify_slack_agent.py" in script
    assert 'ensure_env_var "BRAIN_AGENT_MEMORY_SESSION_ID" "portable_agent_session"' in script
    assert (
        'docker compose -p "$BRAIN_DOCKER_PROJECT" -f deployment/docker-compose.prod.yml up -d postgres neo4j'
        in script
    )
    assert 'set_env_var "VECTOR_DB_PROVIDER" "pgvector"' in script
    assert 'set_env_var "VECTOR_DB_PORT" "$VECTOR_DB_PORT"' in script
    assert 'set_env_var "VECTOR_DATASET_DATABASE_HANDLER" "pgvector"' in script
    assert 'set_env_var "DB_PROVIDER" "postgres"' in script
    assert 'set_env_var "DB_PORT" "$DB_PORT"' in script
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
    assert "brain-maintenance.err.log" in config
    assert "@T00" in config
    assert " J" in config


def test_maintenance_launchd_runs_cognify_then_backup_nightly_at_3am() -> None:
    plist = Path("deployment/launchd/com.brain.maintenance.plist.template").read_text(
        encoding="utf-8"
    )

    assert "com.brain.prod.maintenance" in plist
    assert "scripts/nightly_maintenance.py" in plist
    assert "--env prod" in plist
    assert "--env-file /Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env" in plist
    assert "--session-id portable_agent_session" not in plist
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
