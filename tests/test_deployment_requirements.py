from __future__ import annotations

from pathlib import Path


def test_release_action_validates_before_deploying_to_prod() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "push:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "version:" in workflow
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
    assert workflow.index("Validate staged revision") < workflow.index(
        "Render production config from GitHub Secrets"
    )
    assert workflow.index("Render production config from GitHub Secrets") < workflow.index(
        "Promote staging revision to production"
    )
    assert "sudo -n" in workflow
    assert "BRAIN_DEPLOY_ENV=prod" in workflow
    assert "/Volumes/xpg_usb4/sandbox/git/brain/scripts/deploy-local-production.sh" in workflow
    assert '--source-root "$PWD"' in workflow
    assert "--rendered-env" in workflow
    assert "--rendered-auth-password" in workflow
    assert not Path(".github/workflows/deploy-local-production.yml").exists()


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
    assert "sudo -n" in workflow
    assert "BRAIN_DEPLOY_ENV=staging" in workflow
    assert "/Volumes/xpg_usb4/sandbox/git/brain/scripts/deploy-local-production.sh" in workflow
    assert '--source-root "$PWD"' in workflow
    assert "--rendered-env" in workflow
    assert "--rendered-auth-password" in workflow
    assert workflow.index("Validate repository") < workflow.index(
        "Render staging config from GitHub Secrets"
    )
    assert workflow.index("Render staging config from GitHub Secrets") < workflow.index(
        "Deploy to local staging LaunchDaemons"
    )


def test_release_action_promotes_staging_sha_to_prod_and_tags() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "version:" in workflow
    assert "contents: write" in workflow
    assert "/Volumes/xpg_usb4/staging/brain/current" in workflow
    assert "/Volumes/xpg_usb4/staging/brain/shared/release.json" in workflow
    assert 'readlink "$STAGING_CURRENT"' in workflow
    assert "requested version $TAG is not the staged version" in workflow
    assert "tag $TAG does not exist; deploy it to staging first" in workflow
    assert 'git checkout "$STAGING_SHA"' in workflow
    assert "BRAIN_RELEASE_VERSION" in workflow
    assert "scripts/render_prod_env.py --env prod" in workflow
    assert "BRAIN_DEPLOY_ENV=prod" in workflow
    assert "/Volumes/xpg_usb4/sandbox/git/brain/scripts/deploy-local-production.sh" in workflow
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
        Path("deployment/launchd/com.brain.databases.plist.template"),
        Path("deployment/launchd/com.brain.maintenance.plist.template"),
        Path("deployment/launchd/com.brain.log-rotation.plist.template"),
        Path("deployment/mcp/claude_desktop_config.template.json"),
        Path("deployment/newsyslog/brain.conf"),
        Path("scripts/run_launchd_service.sh"),
        Path("scripts/start_launchd_databases.sh"),
        Path("scripts/setup-macos-service-users.sh"),
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
    assert 'user: "${BRAIN_NEO4J_CONTAINER_USER:-7474:7474}"' in compose
    assert "127.0.0.1:${BRAIN_NEO4J_HTTP_PORT:-17474}:7474" in compose
    assert "127.0.0.1:${BRAIN_NEO4J_BOLT_PORT:-17687}:7687" in compose


def test_local_production_deploy_manages_mcp_ui_and_slack_services() -> None:
    script = Path("scripts/deploy-local-production.sh").read_text(encoding="utf-8")

    assert 'DEPLOY_ENV="${BRAIN_DEPLOY_ENV:-prod}"' in script
    assert 'DEFAULT_ROOT="/Volumes/xpg_usb4/$DEPLOY_ENV/brain"' in script
    assert 'DEFAULT_PUBLIC_BASE_URL="https://brain-staging.dceb.net"' in script
    assert 'BRAIN_DOCKER_PROJECT="${BRAIN_DOCKER_PROJECT:-brain-$ENV_SUFFIX}"' in script
    for label in [
        "com.brain.$ENV_SUFFIX.mcp",
        "com.brain.$ENV_SUFFIX.ui",
        "com.brain.$ENV_SUFFIX.slack-agent",
        "com.brain.$ENV_SUFFIX.databases",
        "com.brain.$ENV_SUFFIX.maintenance",
        "com.brain.$ENV_SUFFIX.log-rotation",
    ]:
        assert label in script

    assert 'DEPLOYMENT_CONFIG_DIR="$REPO_ROOT/deployment"' in script
    assert "deployment" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.databases.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.maintenance.plist.template" in script
    assert "$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.log-rotation.plist.template" in script
    assert "disable_launch_daemon" in script
    assert "com.brain.$ENV_SUFFIX.agent-memory" in script
    assert "com.brain.$ENV_SUFFIX.backup" in script
    assert 'ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"' in script
    assert 'set_env_var "BRAIN_SLACK_AGENT_PORT" "$BRAIN_SLACK_AGENT_PORT"' in script
    assert "BRAIN_DATABASE_URL=$DATABASE_URL" in script
    assert "BRAIN_PROD_ROOT=$PROD_ROOT" in script
    assert "BRAIN_RELEASE_VERSION=$FALLBACK_RELEASE_VERSION" in script
    assert 'write_release_metadata "$RELEASE_DIR/release.json"' in script
    assert 'write_release_metadata "$SHARED_DIR/release.json"' in script
    assert 'ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"' in script
    assert "BRAIN_AUTH_USERS_FILE=$SECRETS_DIR/brain-auth-users.json" in script
    assert "BRAIN_AUTH_SUPERUSER_IDS=default" in script
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
    assert 'DEFAULT_SERVICE_USER="oric_prod"' in script
    assert 'DEFAULT_SERVICE_USER="oric_staging"' in script
    assert 'BRAIN_DEPLOY_USER="${BRAIN_DEPLOY_USER:-${SUDO_USER:-${LOGNAME:-oric}}}"' in script
    assert 'BRAIN_DEPLOY_PYTHON="${BRAIN_DEPLOY_PYTHON:-3.12}"' in script
    assert 'PLIST_DST="/Library/LaunchDaemons/$LABEL.plist"' in script
    assert "enable_launch_daemon()" in script
    assert 'launchctl enable "system/$label"' in script
    assert 'chown root:wheel "$plist"' in script
    assert 'if is_true "${BRAIN_FULL_CHOWN:-false}"; then' in script
    assert (
        'run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$PROD_ROOT" "$LOCAL_SUPPORT_DIR"'
        in script
    )
    assert "apply_runtime_permissions bootstrap" in script
    assert "apply_runtime_permissions final" in script
    assert 'LOCAL_SUPPORT_DIR="/var/db/brain-$ENV_SUFFIX"' in script
    assert 'LOCAL_SYSTEM_DIR="$LOCAL_SUPPORT_DIR/system"' in script
    assert 'LOCAL_DATA_DIR="$LOCAL_SUPPORT_DIR/data"' in script
    assert 'LOCAL_UI_CACHE_DIR="$LOCAL_SUPPORT_DIR/ui-cache"' in script
    assert 'LOCAL_REQUEST_LOG_DIR="$LOCAL_SUPPORT_DIR/logs/requests"' in script
    assert 'LOCAL_ROUTING_LOG_DIR="$LOCAL_SUPPORT_DIR/logs/routing"' in script
    assert 'UV_CACHE_DIR="$LOCAL_SUPPORT_DIR/uv-cache"' in script
    assert 'UV_PYTHON_INSTALL_DIR="$LOCAL_SUPPORT_DIR/python"' in script
    assert 'LOCAL_VENVS_DIR="$LOCAL_SUPPORT_DIR/venvs"' in script
    assert 'LOCAL_VENV_DIR="$LOCAL_VENVS_DIR/$SHA"' in script
    assert 'LOCAL_CURRENT_VENV_LINK="$LOCAL_SUPPORT_DIR/current-venv"' in script
    assert 'LOCAL_SECRETS_DIR="$LOCAL_SUPPORT_DIR/secrets"' in script
    assert 'LOCAL_ENV_FILE="$LOCAL_SECRETS_DIR/brain.env"' in script
    assert 'LOCAL_SCRIPTS_DIR="$LOCAL_SUPPORT_DIR/scripts"' in script
    assert 'LOCAL_CFG_DIR="$LOCAL_SUPPORT_DIR/cfg"' in script
    assert 'LOCAL_DEPLOYMENT_DIR="$LOCAL_SUPPORT_DIR/deployment"' in script
    assert 'LAUNCHD_LOG_DIR="$LOCAL_SUPPORT_DIR/logs/launchd"' in script
    assert 'BRAIN_SOURCE_ROOT=""' in script
    assert 'BRAIN_RENDERED_ENV_FILE=""' in script
    assert 'BRAIN_RENDERED_AUTH_PASSWORD_FILE=""' in script
    assert "--source-root PATH" in script
    assert "--rendered-env PATH" in script
    assert "--rendered-auth-password PATH" in script
    assert "BRAIN_DEPLOY_DELEGATED=true" in script
    assert (
        'LEGACY_LAUNCH_AGENT_DIR="${BRAIN_LEGACY_LAUNCH_AGENT_DIR:-/Users/$BRAIN_DEPLOY_USER/Library/LaunchAgents}"'
        in script
    )
    assert "sync_runtime_secrets()" in script
    assert "import_rendered_config()" in script
    assert 'cp "$BRAIN_RENDERED_ENV_FILE" "$SECRETS_DIR/brain.env"' in script
    assert 'cp "$BRAIN_RENDERED_AUTH_PASSWORD_FILE" "$SECRETS_DIR/brain-auth-password"' in script
    assert "import_rendered_config" in script
    assert "bootstrap_local_runtime_data()" in script
    assert "text = text.replace(source_secrets, local_secrets)" in script
    assert '"SYSTEM_ROOT_DIRECTORY": f"{local_support}/system"' in script
    assert '"DATA_ROOT_DIRECTORY": f"{local_support}/data"' in script
    assert '"BRAIN_REQUEST_LOG_PATH": f"{local_support}/logs/requests/{{date}}.jsonl"' in script
    assert '"BRAIN_ROUTING_LOG_PATH": f"{local_support}/logs/routing/{{date}}.jsonl"' in script
    assert '"BRAIN_UI_CACHE_DIR": f"{local_support}/ui-cache"' in script
    assert 'ENV_FILE="$LOCAL_ENV_FILE"' in script
    assert 'SYSTEM_ROOT_DIRECTORY="$LOCAL_SYSTEM_DIR"' in script
    assert 'DATA_ROOT_DIRECTORY="$LOCAL_DATA_DIR"' in script
    assert 'BRAIN_REQUEST_LOG_PATH="$LOCAL_REQUEST_LOG_DIR/{date}.jsonl"' in script
    assert 'BRAIN_ROUTING_LOG_PATH="$LOCAL_ROUTING_LOG_DIR/{date}.jsonl"' in script
    assert 'BRAIN_UI_CACHE_DIR="$LOCAL_UI_CACHE_DIR"' in script
    assert 'BRAIN_AUTH_USERS_FILE="$LOCAL_SECRETS_DIR/brain-auth-users.json"' in script
    assert (
        "rsync -rt --ignore-existing --no-owner --no-group --no-perms "
        '"$DATA_DIR/system/" "$LOCAL_SYSTEM_DIR/"'
    ) in script
    assert (
        "rsync -rt --ignore-existing --no-owner --no-group --no-perms "
        '"$DATA_DIR/data/" "$LOCAL_DATA_DIR/"'
    ) in script
    assert 'rsync -a --delete "$RELEASE_DIR/scripts/" "$LOCAL_SCRIPTS_DIR/"' in script
    assert 'rsync -a --delete "$RELEASE_DIR/cfg/" "$LOCAL_CFG_DIR/"' in script
    assert 'rsync -a --delete "$RELEASE_DIR/deployment/" "$LOCAL_DEPLOYMENT_DIR/"' in script
    assert "UV_LINK_MODE=copy" in script
    assert 'UV_PROJECT_ENVIRONMENT="$LOCAL_VENV_DIR"' in script
    assert 'BRAIN_CONFIG_DIR="$LOCAL_CFG_DIR"' in script
    assert (
        "uv sync --all-extras --no-editable --reinstall-package memory-stack "
        '--python "$BRAIN_DEPLOY_PYTHON"' in script
    )
    assert 'run_privileged chmod 700 "$SECRETS_DIR"' in script
    assert 'ln -sfn "$LOCAL_VENV_DIR" "$LOCAL_CURRENT_VENV_LINK"' in script
    assert 'enable_launch_daemon "$LABEL" "$PLIST_DST"' in script
    assert 'enable_launch_daemon "$UI_LABEL" "$UI_PLIST_DST"' in script
    assert 'enable_launch_daemon "$SLACK_LABEL" "$SLACK_PLIST_DST"' in script
    assert 'enable_launch_daemon "$DATABASES_LABEL" "$DATABASES_PLIST_DST"' in script
    assert 'enable_launch_daemon "$MAINTENANCE_LABEL" "$MAINTENANCE_PLIST_DST"' in script
    assert 'enable_launch_daemon "$LOG_ROTATION_LABEL" "$LOG_ROTATION_PLIST_DST"' in script
    assert script.index(
        'enable_launch_daemon "$DATABASES_LABEL" "$DATABASES_PLIST_DST"'
    ) < script.index('enable_launch_daemon "$LABEL" "$PLIST_DST"')
    assert (
        'disable_launch_daemon "$LEGACY_AGENT_MEMORY_LABEL" "$LEGACY_AGENT_MEMORY_PLIST_DST"'
        in script
    )
    assert 'disable_launch_daemon "$LEGACY_BACKUP_LABEL" "$LEGACY_BACKUP_PLIST_DST"' in script
    assert "retire_legacy_launch_agents()" in script
    assert 'launchctl bootout "gui/$deploy_uid" "$plist"' in script
    assert 'launchctl bootout "gui/$deploy_uid/$label"' in script
    assert 'launchctl disable "gui/$deploy_uid/$label"' in script
    assert 'target="$retired_dir/$label.$timestamp.plist"' in script
    assert script.index("retire_legacy_launch_agents") < script.index(
        'enable_launch_daemon "$LABEL" "$PLIST_DST"'
    )
    assert 'ensure_env_var "BRAIN_LLM_ENABLED" "false"' in script
    assert 'ensure_env_var "BRAIN_TASTE_ENABLED" "true"' in script
    assert 'ensure_env_var "BRAIN_TASTE_LLM_ROUTING_ENABLED" "false"' in script
    assert 'ensure_env_var "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD" "0.80"' in script
    assert 'ensure_env_var "BRAIN_TASTE_IMPORT_SOURCE_PATH"' not in script
    assert "${BRAIN_SLACK_AGENT_PORT:-18003}/slack/healthz" in script
    assert '"$LOCAL_VENV_DIR/bin/python" scripts/verify_slack_agent.py' in script
    assert 'ensure_env_var "BRAIN_AGENT_MEMORY_SESSION_ID" "portable_agent_session"' in script
    assert (
        'docker compose -p "$BRAIN_DOCKER_PROJECT" -f deployment/docker-compose.prod.yml up -d postgres neo4j'
        in script
    )
    assert "BRAIN_DOCKER_HOST_USER=" in script
    assert 'POSTGRES_CONTAINER_UID="${BRAIN_POSTGRES_CONTAINER_UID:-999}"' in script
    assert 'NEO4J_CONTAINER_UID="${BRAIN_NEO4J_CONTAINER_UID:-7474}"' in script
    assert "resolve_docker_runtime_user" in script
    assert (
        'BRAIN_NEO4J_CONTAINER_USER="$(id -u "$BRAIN_DOCKER_HOST_USER"):$(id -g "$BRAIN_DOCKER_HOST_USER")"'
        in script
    )
    assert 'BRAIN_NEO4J_CONTAINER_USER="$BRAIN_NEO4J_CONTAINER_USER"' in script
    assert "prepare_container_bind_mounts" in script
    assert (
        'docker compose -p "$BRAIN_DOCKER_PROJECT" -f deployment/docker-compose.prod.yml stop postgres neo4j'
        in script
    )
    assert (
        'run_privileged chown -R "$POSTGRES_CONTAINER_UID:$POSTGRES_CONTAINER_GID" "$POSTGRES_DATA_DIR"'
        in script
    )
    assert 'grant_docker_host_acl "$POSTGRES_DATA_DIR"' in script
    assert "writesecurity,chown" in script
    assert 'run_privileged chmod -R +a "$acl" "$path"' in script
    assert 'run_privileged chmod -R u+rwX,go-rwx "$POSTGRES_DATA_DIR"' in script
    assert 'run_privileged chmod -R u+rwX,go+rX "$NEO4J_DATA_DIR"' in script
    assert 'wait_for_tcp "127.0.0.1" "$BRAIN_NEO4J_BOLT_PORT" "$DEPLOY_ENV Neo4j Bolt"' in script
    assert "clear_mutable_data_provenance" in script
    assert 'xattr -dr com.apple.provenance "$DATA_DIR"' in script
    assert 'set_env_var "VECTOR_DB_PROVIDER" "pgvector"' in script
    assert 'set_env_var "VECTOR_DB_PORT" "$VECTOR_DB_PORT"' in script
    assert 'set_env_var "VECTOR_DATASET_DATABASE_HANDLER" "pgvector"' in script
    assert 'set_env_var "DB_PROVIDER" "postgres"' in script
    assert 'set_env_var "DB_PORT" "$DB_PORT"' in script
    assert 'set_env_var "BRAIN_DOCKER_PROJECT" "$BRAIN_DOCKER_PROJECT"' in script
    assert 'set_env_var "BRAIN_DOCKER_HOST_USER" "$BRAIN_DOCKER_HOST_USER"' in script
    assert 'set_env_var "BRAIN_POSTGRES_CONTAINER" "$BRAIN_POSTGRES_CONTAINER"' in script
    assert 'set_env_var "BRAIN_NEO4J_CONTAINER" "$BRAIN_NEO4J_CONTAINER"' in script
    assert 'set_env_var "BRAIN_NEO4J_CONTAINER_USER" "$BRAIN_NEO4J_CONTAINER_USER"' in script
    assert 'set_env_var "BRAIN_NEO4J_BOLT_PORT" "$BRAIN_NEO4J_BOLT_PORT"' in script
    assert "GRAPH_DATABASE_PASSWORD must be set to a real secret" in script
    assert '"$LOCAL_VENV_DIR/bin/python" scripts/live_model_smoke.py' in script
    assert 'MODEL_SMOKE_SCOPE="${BRAIN_MODEL_SMOKE_SCOPE:-active}"' in script
    assert "--exclude '.env'" in script
    assert 'rm -f "$RELEASE_DIR/.env"' in script
    assert 'DEFAULT_REFRESH_RELEASE="false"' in script
    assert 'DEFAULT_REFRESH_RELEASE="true"' in script
    assert 'BRAIN_REFRESH_RELEASE="${BRAIN_REFRESH_RELEASE:-$DEFAULT_REFRESH_RELEASE}"' in script
    assert script.index('"$LOCAL_VENV_DIR/bin/python" scripts/live_model_smoke.py') < script.index(
        'ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"'
    )
    assert script.index('"$LOCAL_VENV_DIR/bin/python" scripts/live_model_smoke.py') < script.index(
        "waiting for local health"
    )


def test_mcp_launchd_uses_dated_request_and_routing_logs() -> None:
    plist = Path("deployment/launchd/com.brain.mcp.plist.template").read_text(encoding="utf-8")

    assert "<key>UserName</key>" in plist
    assert "<string>oric_prod</string>" in plist
    assert "<string>/bin/sh</string>" in plist
    assert "<string>-c</string>" in plist
    assert "<key>SessionCreate</key>" in plist
    assert "<string>/</string>" in plist
    assert "/var/db/brain-prod/scripts/run_launchd_service.sh mcp" in plist
    assert "/var/db/brain-prod/secrets/brain.env" in plist
    assert "RELEASE_DIR=$(/usr/bin/readlink /Volumes/xpg_usb4/prod/brain/current)" not in plist
    assert "memory_stack.mcp_server" not in plist
    assert "<key>PATH</key>" in plist
    assert "/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin" in plist
    assert "<key>UV_CACHE_DIR</key>" in plist
    assert "<string>/var/db/brain-prod/uv-cache</string>" in plist
    assert "<key>UV_PYTHON_INSTALL_DIR</key>" in plist
    assert "<string>/var/db/brain-prod/python</string>" in plist
    assert "<key>BRAIN_CONFIG_DIR</key>" in plist
    assert "<string>/var/db/brain-prod/cfg</string>" in plist
    assert "/var/db/brain-prod/logs/requests/{date}.jsonl" in plist
    assert "<key>BRAIN_REQUEST_LOG_MAX_BODY_BYTES</key>" in plist
    assert "<string>8192</string>" in plist
    assert "<key>BRAIN_REQUEST_LOG_RETENTION_DAYS</key>" in plist
    assert "<string>30</string>" in plist
    assert "<key>BRAIN_ROUTING_LOG_ENABLED</key>" in plist
    assert "/var/db/brain-prod/logs/routing/{date}.jsonl" in plist
    assert "<key>BRAIN_ROUTING_LOG_RETENTION_DAYS</key>" in plist
    assert "<string>90</string>" in plist
    assert "<key>SYSTEM_ROOT_DIRECTORY</key>" in plist
    assert "<string>/var/db/brain-prod/system</string>" in plist
    assert "<key>DATA_ROOT_DIRECTORY</key>" in plist
    assert "<string>/var/db/brain-prod/data</string>" in plist


def test_launchd_wrappers_wait_for_databases_and_start_containers() -> None:
    service_script = Path("scripts/run_launchd_service.sh").read_text(encoding="utf-8")
    database_script = Path("scripts/start_launchd_databases.sh").read_text(encoding="utf-8")
    database_plist = Path("deployment/launchd/com.brain.databases.plist.template").read_text(
        encoding="utf-8"
    )

    assert "wait_for_tcp" in service_script
    assert 'wait_for_tcp "127.0.0.1" "$DB_PORT" "Postgres"' in service_script
    assert 'wait_for_tcp "127.0.0.1" "$BRAIN_NEO4J_BOLT_PORT" "Neo4j Bolt"' in service_script
    assert "memory_stack.mcp_server" in service_script
    assert "memory_stack.ui_service" in service_script
    assert "memory_stack.slack_agent_server" in service_script
    assert "/Users/$BRAIN_DOCKER_HOST_USER/.colima/default/docker.sock" in database_script
    assert '/usr/bin/nc -z -G 2 "$host" "$port"' in database_script
    assert 'export DOCKER_HOST="unix://$socket"' in database_script
    assert 'DOCKER_BIN="$(command -v "$candidate")"' in database_script
    assert '"$DOCKER_BIN" info' in database_script
    assert 'export BRAIN_DOCKER_PROJECT' in database_script
    assert 'log "using Docker binary: $DOCKER_BIN"' in database_script
    assert "$LOCAL_SUPPORT_DIR/deployment/docker-compose.prod.yml" in database_script
    assert "/opt/homebrew/bin/docker-compose" in database_script
    assert '"$DOCKER_COMPOSE_BIN" -p "$BRAIN_DOCKER_PROJECT"' in database_script
    assert (
        '"$DOCKER_BIN" compose -p "$BRAIN_DOCKER_PROJECT" -f "$COMPOSE_FILE" '
        "up -d postgres neo4j"
    ) in database_script
    assert 'wait_for_tcp "127.0.0.1" "$DB_PORT" "$ENV_SUFFIX Postgres"' in database_script
    assert (
        'wait_for_tcp "127.0.0.1" "$BRAIN_NEO4J_BOLT_PORT" "$ENV_SUFFIX Neo4j Bolt"'
        in database_script
    )
    assert "com.brain.prod.databases" in database_plist
    assert "/var/db/brain-prod/scripts/start_launchd_databases.sh" in database_plist
    assert "<key>RunAtLoad</key>" in database_plist
    assert "<key>StartInterval</key>" in database_plist


def test_ui_launchd_uses_cognee_public_paths() -> None:
    plist = Path("deployment/launchd/com.brain.ui.plist.template").read_text(encoding="utf-8")

    assert "<key>BRAIN_PUBLIC_UI_PATH</key>" in plist
    assert "<string>/cognee</string>" in plist
    assert "<key>BRAIN_PUBLIC_UI_API_PATH</key>" in plist
    assert "<string>/cognee-api</string>" in plist


def test_newsyslog_rotates_launchd_logs_daily() -> None:
    config = Path("deployment/newsyslog/brain.conf").read_text(encoding="utf-8")

    assert "brain-prod.err.log" in config
    assert "/var/db/brain-prod/logs/launchd" in config
    assert "brain-ui.err.log" in config
    assert "brain-slack-agent.err.log" in config
    assert "brain-maintenance.err.log" in config
    assert "@T00" in config
    assert " J" in config


def test_maintenance_launchd_runs_cognify_then_backup_nightly_at_3am() -> None:
    plist = Path("deployment/launchd/com.brain.maintenance.plist.template").read_text(
        encoding="utf-8"
    )
    service_script = Path("scripts/run_launchd_service.sh").read_text(encoding="utf-8")

    assert "com.brain.prod.maintenance" in plist
    assert "/var/db/brain-prod/scripts/run_launchd_service.sh maintenance" in plist
    assert 'exec "$PYTHON" "$LOCAL_SUPPORT_DIR/scripts/nightly_maintenance.py"' in service_script
    assert '--env "$ENV_SUFFIX"' in service_script
    assert '--env-file "$ENV_FILE"' in service_script
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
    service_script = Path("scripts/run_launchd_service.sh").read_text(encoding="utf-8")

    assert "com.brain.prod.log-rotation" in plist
    assert "/var/db/brain-prod/scripts/run_launchd_service.sh log-rotation" in plist
    assert 'exec "$PYTHON" "$LOCAL_SUPPORT_DIR/scripts/rotate_launchd_logs.py"' in service_script
    assert '--log-dir "$LOCAL_SUPPORT_DIR/logs/launchd"' in service_script
    assert (
        '--archive-dir "/Volumes/xpg_usb4/$ENV_SUFFIX/brain/shared/logs/launchd/archive"'
        in service_script
    )
    assert "--retention-days 30" in service_script
    assert "<key>StartCalendarInterval</key>" in plist
    assert "<key>Hour</key>" in plist
    assert "<integer>0</integer>" in plist
    assert "<key>Minute</key>" in plist
    assert "<integer>5</integer>" in plist


def test_cognee_ui_verifier_retries_backend_health() -> None:
    verifier = Path("scripts/verify_cognee_ui_production.py").read_text(encoding="utf-8")

    assert "for _attempt in range(30):" in verifier
    assert "time.sleep(2)" in verifier
    assert '["launchctl", "print", f"system/{label}"]' in verifier


def test_production_verifier_checks_brain_database_under_shared_data_and_runtime_roots() -> None:
    verifier = Path("scripts/verify_mcp_production.py").read_text(encoding="utf-8")

    assert '"BRAIN_DATABASE_URL": sqlite_path(settings.brain_database_url)' in verifier
    assert 'local_support_root = Path(f"/var/db/brain-{settings.brain_release_env}")' in verifier
    assert "local_or_shared_paths = {" in verifier
    assert "SYSTEM_ROOT_DIRECTORY" in verifier
    assert "DATA_ROOT_DIRECTORY" in verifier
    assert "under local support root" in verifier
    assert 'if getattr(settings, "vector_db_provider", "lancedb") == "lancedb":' in verifier
    assert 'shared_paths["VECTOR_DB_URL"] = Path(settings.vector_db_url)' in verifier
    assert '["launchctl", "print", f"system/{label}"]' in verifier
    assert "process cwd under approved runtime root" in verifier


def test_cloudflare_routes_slack_to_agent_before_mcp_catchall() -> None:
    config = Path("deployment/cloudflare/config.example.yml").read_text(encoding="utf-8")

    slack_route = "path: /slack*"
    slack_service = "service: http://127.0.0.1:18003"
    mcp_catchall = "service: http://127.0.0.1:18000"

    assert slack_route in config
    assert slack_service in config
    assert config.index(slack_route) < config.index(mcp_catchall)
    assert config.index(slack_service) < config.index(mcp_catchall)
