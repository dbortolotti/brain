from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
FALLBACK_ENV_FILE = PROJECT_ROOT / ".env.example"


PROVIDER_API_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "openai": ("openai_api_key",),
    "gemini": ("gemini_api_key", "google_api_key"),
    "google": ("google_api_key", "gemini_api_key"),
    "anthropic": ("anthropic_api_key",),
    "aws-bedrock": ("aws_bearer_token_bedrock",),
    "bedrock": ("aws_bearer_token_bedrock",),
    "groq": ("groq_api_key",),
    "voyage": ("voyage_api_key",),
}
PROVIDER_API_KEY_ENV_NAMES: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "google": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "aws-bedrock": ("AWS_BEARER_TOKEN_BEDROCK",),
    "bedrock": ("AWS_BEARER_TOKEN_BEDROCK",),
    "groq": ("GROQ_API_KEY",),
    "voyage": ("VOYAGE_API_KEY",),
}
PROVIDER_RUNTIME_ENV_FIELDS: dict[str, tuple[tuple[str, str], ...]] = {
    "aws-bedrock": (
        ("AWS_REGION", "aws_region"),
        ("AWS_DEFAULT_REGION", "aws_default_region"),
        ("AWS_PROFILE", "aws_profile"),
        ("AWS_ACCESS_KEY_ID", "aws_access_key_id"),
        ("AWS_SECRET_ACCESS_KEY", "aws_secret_access_key"),
        ("AWS_SESSION_TOKEN", "aws_session_token"),
    ),
    "bedrock": (
        ("AWS_REGION", "aws_region"),
        ("AWS_DEFAULT_REGION", "aws_default_region"),
        ("AWS_PROFILE", "aws_profile"),
        ("AWS_ACCESS_KEY_ID", "aws_access_key_id"),
        ("AWS_SECRET_ACCESS_KEY", "aws_secret_access_key"),
        ("AWS_SESSION_TOKEN", "aws_session_token"),
    ),
}
CANONICAL_PROVIDER_API_KEY_PROVIDERS = (
    "openai",
    "gemini",
    "anthropic",
    "aws-bedrock",
    "groq",
    "voyage",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DEFAULT_ENV_FILE if DEFAULT_ENV_FILE.exists() else FALLBACK_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    profile: Literal["gemini", "openai", "local"] = "gemini"

    llm_provider: str = "gemini"
    llm_model: str = "gemini/gemini-3.1-flash-lite-preview"
    llm_api_key: str | None = None
    llm_endpoint: str | None = None
    llm_temperature: float = 0.0
    llm_max_tokens: int = 8192

    embedding_provider: str = "gemini"
    embedding_model: str = "gemini/gemini-embedding-001"
    embedding_api_key: str | None = None
    embedding_dimensions: int = 768

    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    google_api_key: str | None = None
    anthropic_api_key: str | None = None
    aws_region: str | None = None
    aws_default_region: str | None = None
    aws_profile: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_bearer_token_bedrock: str | None = None
    groq_api_key: str | None = None
    voyage_api_key: str | None = None

    graph_database_provider: str = "neo4j"
    graph_database_url: str = "bolt://localhost:7687"
    graph_database_name: str = "neo4j"
    graph_database_username: str = "neo4j"
    graph_database_password: str = "change-me"

    vector_db_provider: str = "lancedb"
    vector_db_url: str = "./.data/lancedb/cognee.lancedb"

    db_provider: str = "sqlite"
    db_name: str = "cognee_db"

    system_root_directory: str = "./.data/system"
    data_root_directory: str = "./.data/data"

    google_free_tier: bool = False
    allow_cloud_keys_in_local: bool = False
    allow_embedding_dimension_change: bool = False

    brain_mcp_host: str = "127.0.0.1"
    brain_mcp_port: int = 8000
    brain_mcp_path: str = "/mcp"
    brain_public_base_url: str = "https://brain.dceb.net"
    brain_public_mcp_path: str = "/mcp"
    brain_backup_dir: str = "/Volumes/xpg_usb4/prod/brain/shared/backups"
    brain_neo4j_dump_enabled: bool = False
    brain_neo4j_stop_for_dump: bool = False
    brain_neo4j_brew_service: str = "neo4j"
    brain_neo4j_launchd_label: str = "homebrew.mxcl.neo4j"
    brain_google_drive_backup_enabled: bool = False
    brain_google_drive_folder: str = "backup/brain"
    brain_google_drive_remote: str = "gdrive"
    brain_google_drive_local_path: str | None = None
    brain_auth_enabled: bool = False
    brain_auth_token: str | None = None
    brain_auth_password: str | None = None
    brain_auth_password_file: str = "./secrets/brain-auth-password"
    brain_auth_state_path: str = "./secrets/brain-oauth.json"
    brain_auth_scopes: str = "brain.memory.read brain.memory.write"
    brain_auth_require_pkce: bool = True
    brain_auth_access_token_seconds: int = 3600
    brain_auth_refresh_token_seconds: int = 60 * 60 * 24 * 30
    brain_request_log_enabled: bool = False
    brain_request_log_path: str = "./.data/logs/requests.jsonl"
    brain_request_log_max_body_bytes: int = 1024 * 1024
    brain_service_name: str = "Brain"
    brain_database_url: str = "sqlite:///.data/brain/brain.db"
    brain_owner_name: str = "Daniele"
    brain_llm_enabled: bool = False
    brain_llm_provider: str | None = None
    brain_llm_model: str | None = None
    brain_cognee_enabled: bool = False
    brain_cognee_recall_enabled: bool = False
    brain_cognee_memory_dataset: str = "memory"
    brain_cognee_sources_dataset: str = "sources"
    brain_cognee_data_dataset: str = "data"
    brain_cognee_recall_top_k: int = 10
    brain_slack_enabled: bool = False
    brain_slack_agent_enabled: bool = False
    brain_slack_agent_host: str = "127.0.0.1"
    brain_slack_agent_port: int = 8003
    brain_slack_signing_secret: str | None = None
    brain_slack_bot_token: str | None = None
    brain_slack_allowed_team_ids: str = ""
    brain_slack_allowed_channel_ids: str = ""
    brain_slack_allowed_user_ids: str = ""
    brain_slack_admin_user_ids: str = ""
    brain_slack_rules_path: str = "./config/slack_memory_agent_rules.md"
    brain_slack_auto_commit_high_confidence: bool = False
    brain_log_level: str = "INFO"
    brain_prod_root: str = "/Volumes/xpg_usb4/prod/brain"
    brain_launchd_label: str = "com.brain.mcp"
    brain_health_path: str = "/healthz"
    brain_ui_enabled: bool = False
    brain_ui_host: str = "127.0.0.1"
    brain_ui_proxy_port: int = 8002
    brain_ui_frontend_port: int = 3000
    brain_ui_backend_port: int = 8001
    brain_public_ui_path: str = "/ui"
    brain_public_ui_api_path: str = "/ui-api"
    brain_ui_session_seconds: int = 60 * 60 * 12
    brain_ui_launchd_label: str = "com.brain.ui"

    @model_validator(mode="after")
    def validate_profile(self) -> "Settings":
        self.llm_api_key = self.llm_api_key or self.configured_provider_api_key(
            self.llm_provider
        )
        self.embedding_api_key = (
            self.embedding_api_key
            or self.configured_provider_api_key(self.embedding_provider)
        )

        if self.profile == "local":
            if self.llm_provider != "ollama":
                raise ValueError("PROFILE=local requires LLM_PROVIDER=ollama")

            if self.embedding_provider not in {"fastembed", "ollama"}:
                raise ValueError(
                    "PROFILE=local requires EMBEDDING_PROVIDER=fastembed or ollama"
                )

            if not self.allow_cloud_keys_in_local:
                cloud_indicators = [
                    self.llm_api_key and self.llm_api_key.startswith("sk-"),
                    self.embedding_api_key and self.embedding_api_key.startswith("sk-"),
                    self.llm_api_key and self.llm_api_key.startswith("AIza"),
                    self.embedding_api_key and self.embedding_api_key.startswith("AIza"),
                    self.openai_api_key,
                    self.gemini_api_key,
                    self.google_api_key,
                    self.anthropic_api_key,
                    self.aws_bearer_token_bedrock,
                    self.groq_api_key,
                    self.voyage_api_key,
                    self.llm_provider in {"openai", "gemini"},
                    self.embedding_provider in {"openai", "gemini"},
                ]
                if any(cloud_indicators):
                    raise ValueError(
                        "PROFILE=local appears to contain cloud provider settings. "
                        "Set ALLOW_CLOUD_KEYS_IN_LOCAL=true only if intentional."
                    )

        if self.profile == "gemini":
            if self.llm_provider != "gemini":
                raise ValueError("PROFILE=gemini requires LLM_PROVIDER=gemini")
            if self.embedding_provider != "gemini":
                raise ValueError("PROFILE=gemini requires EMBEDDING_PROVIDER=gemini")

        if self.profile == "openai":
            if self.llm_provider != "openai":
                raise ValueError("PROFILE=openai requires LLM_PROVIDER=openai")
            if self.embedding_provider != "openai":
                raise ValueError("PROFILE=openai requires EMBEDDING_PROVIDER=openai")

        self.brain_mcp_path = normalize_path(self.brain_mcp_path)
        self.brain_public_mcp_path = normalize_path(self.brain_public_mcp_path)
        self.brain_health_path = normalize_path(self.brain_health_path)
        self.brain_public_ui_path = normalize_path(self.brain_public_ui_path)
        self.brain_public_ui_api_path = normalize_path(self.brain_public_ui_api_path)
        return self

    def configured_provider_api_key(self, provider: str | None) -> str | None:
        for field_name in provider_api_key_fields(provider):
            value = getattr(self, field_name, None)
            if value:
                return value
        return None

    def provider_api_key(self, provider: str | None) -> str | None:
        direct_key = self.configured_provider_api_key(provider)
        if direct_key:
            return direct_key

        normalized = normalize_provider_name(provider)
        if not normalized:
            return None
        if normalize_provider_name(self.llm_provider) == normalized and self.llm_api_key:
            return self.llm_api_key
        if (
            normalize_provider_name(self.embedding_provider) == normalized
            and self.embedding_api_key
        ):
            return self.embedding_api_key
        return None

    @property
    def public_mcp_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_mcp_path}"

    @property
    def public_ui_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_ui_path}"

    @property
    def public_ui_api_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_ui_api_path}"

    @property
    def protected_resource_metadata_url(self) -> str:
        path = self.brain_public_mcp_path.strip("/")
        return (
            f"{self.brain_public_base_url.rstrip('/')}"
            f"/.well-known/oauth-protected-resource/{path}"
        )

    @property
    def prod_root_path(self) -> Path:
        return Path(self.brain_prod_root)

    @property
    def shared_data_path(self) -> Path:
        return self.prod_root_path / "shared" / "data"

    @property
    def auth_password_path(self) -> Path:
        return Path(self.brain_auth_password_file).expanduser()

    @property
    def auth_state_path(self) -> Path:
        return Path(self.brain_auth_state_path).expanduser()

    @property
    def oauth_scopes(self) -> list[str]:
        return [scope for scope in self.brain_auth_scopes.split() if scope]

    @property
    def brain_auth_scope_list(self) -> list[str]:
        return self.oauth_scopes

    @property
    def brain_slack_allowed_team_id_list(self) -> list[str]:
        return split_csv_setting(self.brain_slack_allowed_team_ids)

    @property
    def brain_slack_allowed_channel_id_list(self) -> list[str]:
        return split_csv_setting(self.brain_slack_allowed_channel_ids)

    @property
    def brain_slack_allowed_user_id_list(self) -> list[str]:
        return split_csv_setting(self.brain_slack_allowed_user_ids)

    @property
    def brain_slack_admin_user_id_list(self) -> list[str]:
        return split_csv_setting(self.brain_slack_admin_user_ids)


def normalize_path(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return "/"
    return "/" + stripped.strip("/")


def split_csv_setting(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_provider_name(provider: str | None) -> str | None:
    if provider is None:
        return None
    normalized = provider.strip().lower()
    if not normalized:
        return None
    return normalized.split(":", maxsplit=1)[0].split("/", maxsplit=1)[0]


def provider_api_key_fields(provider: str | None) -> tuple[str, ...]:
    normalized = normalize_provider_name(provider)
    if not normalized:
        return ()
    return PROVIDER_API_KEY_FIELDS.get(normalized, (f"{normalized}_api_key",))


def provider_api_key_env_names(provider: str | None) -> tuple[str, ...]:
    normalized = normalize_provider_name(provider)
    if not normalized:
        return ()
    return PROVIDER_API_KEY_ENV_NAMES.get(normalized, (f"{normalized.upper()}_API_KEY",))


def provider_runtime_env_fields(provider: str | None) -> tuple[tuple[str, str], ...]:
    normalized = normalize_provider_name(provider)
    if not normalized:
        return ()
    return PROVIDER_RUNTIME_ENV_FIELDS.get(normalized, ())


def load_settings(env_file: str | Path | None = None) -> Settings:
    if env_file is None:
        env_file = os.getenv("ENV_FILE")
    if env_file:
        return Settings(_env_file=str(env_file))
    return Settings()


def repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def provider_api_environment(settings: Settings) -> dict[str, str]:
    providers = {
        normalize_provider_name(settings.llm_provider),
        normalize_provider_name(settings.embedding_provider),
        normalize_provider_name(settings.brain_llm_provider),
    }
    providers.update(CANONICAL_PROVIDER_API_KEY_PROVIDERS)
    values: dict[str, str] = {}
    for provider in providers:
        for env_name, field_name in provider_runtime_env_fields(provider):
            value = getattr(settings, field_name, None)
            if value:
                values[env_name] = value
        api_key = settings.provider_api_key(provider)
        if not api_key:
            continue
        for env_name in provider_api_key_env_names(provider):
            values[env_name] = api_key
    return values


def runtime_env(settings: Settings) -> dict[str, str]:
    values = {
        "PROFILE": settings.profile,
        "LLM_PROVIDER": settings.llm_provider,
        "LLM_MODEL": settings.llm_model,
        "LLM_TEMPERATURE": str(settings.llm_temperature),
        "LLM_MAX_TOKENS": str(settings.llm_max_tokens),
        "EMBEDDING_PROVIDER": settings.embedding_provider,
        "EMBEDDING_MODEL": settings.embedding_model,
        "EMBEDDING_DIMENSIONS": str(settings.embedding_dimensions),
        "GRAPH_DATABASE_PROVIDER": settings.graph_database_provider,
        "GRAPH_DATABASE_URL": settings.graph_database_url,
        "GRAPH_DATABASE_NAME": settings.graph_database_name,
        "GRAPH_DATABASE_USERNAME": settings.graph_database_username,
        "GRAPH_DATABASE_PASSWORD": settings.graph_database_password,
        "VECTOR_DB_PROVIDER": settings.vector_db_provider,
        "VECTOR_DB_URL": str(repo_path(settings.vector_db_url)),
        "DB_PROVIDER": settings.db_provider,
        "DB_NAME": settings.db_name,
        "SYSTEM_ROOT_DIRECTORY": str(repo_path(settings.system_root_directory)),
        "DATA_ROOT_DIRECTORY": str(repo_path(settings.data_root_directory)),
        "BRAIN_MCP_HOST": settings.brain_mcp_host,
        "BRAIN_MCP_PORT": str(settings.brain_mcp_port),
        "BRAIN_MCP_PATH": settings.brain_mcp_path,
        "BRAIN_PUBLIC_BASE_URL": settings.brain_public_base_url,
        "BRAIN_PUBLIC_MCP_PATH": settings.brain_public_mcp_path,
        "BRAIN_BACKUP_DIR": settings.brain_backup_dir,
        "BRAIN_NEO4J_DUMP_ENABLED": str(settings.brain_neo4j_dump_enabled).lower(),
        "BRAIN_NEO4J_STOP_FOR_DUMP": str(settings.brain_neo4j_stop_for_dump).lower(),
        "BRAIN_NEO4J_BREW_SERVICE": settings.brain_neo4j_brew_service,
        "BRAIN_NEO4J_LAUNCHD_LABEL": settings.brain_neo4j_launchd_label,
        "BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED": str(
            settings.brain_google_drive_backup_enabled
        ).lower(),
        "BRAIN_GOOGLE_DRIVE_FOLDER": settings.brain_google_drive_folder,
        "BRAIN_AUTH_ENABLED": str(settings.brain_auth_enabled).lower(),
        "BRAIN_AUTH_PASSWORD_FILE": settings.brain_auth_password_file,
        "BRAIN_AUTH_STATE_PATH": settings.brain_auth_state_path,
        "BRAIN_AUTH_SCOPES": settings.brain_auth_scopes,
        "BRAIN_AUTH_REQUIRE_PKCE": str(settings.brain_auth_require_pkce).lower(),
        "BRAIN_AUTH_ACCESS_TOKEN_SECONDS": str(settings.brain_auth_access_token_seconds),
        "BRAIN_AUTH_REFRESH_TOKEN_SECONDS": str(settings.brain_auth_refresh_token_seconds),
        "BRAIN_REQUEST_LOG_ENABLED": str(settings.brain_request_log_enabled).lower(),
        "BRAIN_REQUEST_LOG_PATH": settings.brain_request_log_path,
        "BRAIN_REQUEST_LOG_MAX_BODY_BYTES": str(settings.brain_request_log_max_body_bytes),
        "BRAIN_DATABASE_URL": settings.brain_database_url,
        "BRAIN_OWNER_NAME": settings.brain_owner_name,
        "BRAIN_LLM_ENABLED": str(settings.brain_llm_enabled).lower(),
        "BRAIN_LLM_PROVIDER": settings.brain_llm_provider or "",
        "BRAIN_LLM_MODEL": settings.brain_llm_model or "",
        "BRAIN_COGNEE_ENABLED": str(settings.brain_cognee_enabled).lower(),
        "BRAIN_COGNEE_RECALL_ENABLED": str(settings.brain_cognee_recall_enabled).lower(),
        "BRAIN_COGNEE_MEMORY_DATASET": settings.brain_cognee_memory_dataset,
        "BRAIN_COGNEE_SOURCES_DATASET": settings.brain_cognee_sources_dataset,
        "BRAIN_COGNEE_DATA_DATASET": settings.brain_cognee_data_dataset,
        "BRAIN_COGNEE_RECALL_TOP_K": str(settings.brain_cognee_recall_top_k),
        "BRAIN_SLACK_ENABLED": str(settings.brain_slack_enabled).lower(),
        "BRAIN_SLACK_AGENT_ENABLED": str(settings.brain_slack_agent_enabled).lower(),
        "BRAIN_SLACK_AGENT_HOST": settings.brain_slack_agent_host,
        "BRAIN_SLACK_AGENT_PORT": str(settings.brain_slack_agent_port),
        "BRAIN_SLACK_ALLOWED_TEAM_IDS": settings.brain_slack_allowed_team_ids,
        "BRAIN_SLACK_ALLOWED_CHANNEL_IDS": settings.brain_slack_allowed_channel_ids,
        "BRAIN_SLACK_ALLOWED_USER_IDS": settings.brain_slack_allowed_user_ids,
        "BRAIN_SLACK_ADMIN_USER_IDS": settings.brain_slack_admin_user_ids,
        "BRAIN_SLACK_RULES_PATH": settings.brain_slack_rules_path,
        "BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE": str(
            settings.brain_slack_auto_commit_high_confidence
        ).lower(),
        "BRAIN_LOG_LEVEL": settings.brain_log_level,
        "BRAIN_UI_ENABLED": str(settings.brain_ui_enabled).lower(),
        "BRAIN_UI_HOST": settings.brain_ui_host,
        "BRAIN_UI_PROXY_PORT": str(settings.brain_ui_proxy_port),
        "BRAIN_UI_FRONTEND_PORT": str(settings.brain_ui_frontend_port),
        "BRAIN_UI_BACKEND_PORT": str(settings.brain_ui_backend_port),
        "BRAIN_PUBLIC_UI_PATH": settings.brain_public_ui_path,
        "BRAIN_PUBLIC_UI_API_PATH": settings.brain_public_ui_api_path,
        "BRAIN_UI_SESSION_SECONDS": str(settings.brain_ui_session_seconds),
    }
    optional_values = {
        "LLM_API_KEY": settings.llm_api_key,
        "LLM_ENDPOINT": settings.llm_endpoint,
        "EMBEDDING_API_KEY": settings.embedding_api_key,
        "BRAIN_AUTH_TOKEN": settings.brain_auth_token,
        "BRAIN_AUTH_PASSWORD": settings.brain_auth_password,
        "BRAIN_GOOGLE_DRIVE_LOCAL_PATH": settings.brain_google_drive_local_path,
        "BRAIN_SLACK_SIGNING_SECRET": settings.brain_slack_signing_secret,
        "BRAIN_SLACK_BOT_TOKEN": settings.brain_slack_bot_token,
    }
    optional_values.update(provider_api_environment(settings))
    for key, value in optional_values.items():
        if value:
            values[key] = value
    return values


def apply_runtime_environment(settings: Settings) -> None:
    for key, value in runtime_env(settings).items():
        os.environ[key] = value
    for path_value in (
        runtime_env(settings)["SYSTEM_ROOT_DIRECTORY"],
        runtime_env(settings)["DATA_ROOT_DIRECTORY"],
        runtime_env(settings)["VECTOR_DB_URL"],
    ):
        path = repo_path(path_value)
        if path.suffix and path.suffix != ".lancedb":
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)


def embedding_dimension_state_path() -> Path:
    return PROJECT_ROOT / ".data" / "embedding_dimensions.json"


def check_embedding_dimension_change(settings: Settings) -> tuple[bool, str]:
    state_path = embedding_dimension_state_path()
    if not state_path.exists():
        return True, "No previous embedding-dimension state found."

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    previous = payload.get("embedding_dimensions")
    if previous == settings.embedding_dimensions:
        return True, f"Embedding dimensions unchanged: {settings.embedding_dimensions}."

    if settings.allow_embedding_dimension_change:
        return True, (
            f"Embedding dimensions changed from {previous} to "
            f"{settings.embedding_dimensions}; override is enabled."
        )

    return False, (
        f"Embedding dimensions changed from {previous} to {settings.embedding_dimensions}. "
        "Run a hard reset or set ALLOW_EMBEDDING_DIMENSION_CHANGE=true."
    )


def record_embedding_dimension(settings: Settings) -> None:
    state_path = embedding_dimension_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "profile": settings.profile,
                "embedding_provider": settings.embedding_provider,
                "embedding_model": settings.embedding_model,
                "embedding_dimensions": settings.embedding_dimensions,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
