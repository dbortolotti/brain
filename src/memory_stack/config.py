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
    brain_google_drive_backup_enabled: bool = False
    brain_google_drive_folder: str = "backup/brain"
    brain_google_drive_remote: str = "gdrive"
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
    brain_prod_root: str = "/Volumes/xpg_usb4/prod/brain"
    brain_launchd_label: str = "com.brain.mcp"
    brain_health_path: str = "/healthz"

    @model_validator(mode="after")
    def validate_profile(self) -> "Settings":
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
        return self

    @property
    def public_mcp_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_mcp_path}"

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


def normalize_path(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return "/"
    return "/" + stripped.strip("/")


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
    }
    optional_values = {
        "LLM_API_KEY": settings.llm_api_key,
        "LLM_ENDPOINT": settings.llm_endpoint,
        "EMBEDDING_API_KEY": settings.embedding_api_key,
        "OPENAI_API_KEY": settings.llm_api_key if settings.llm_provider == "openai" else None,
        "BRAIN_AUTH_TOKEN": settings.brain_auth_token,
        "BRAIN_AUTH_PASSWORD": settings.brain_auth_password,
    }
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
