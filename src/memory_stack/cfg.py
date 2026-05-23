from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Mapping
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Any, Literal

import json
import yaml
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


CONFIG_DIR = Path(os.environ.get("BRAIN_CONFIG_DIR", Path(__file__).resolve().parents[2] / "cfg"))
DEFAULT_ENV = "dev"
SUPPORTED_ENVS = {"dev", "qa", "staging", "prod"}

_CACHE: dict[str, Any] | None = None
_CACHE_ENV: str | None = None
_ACTIVE_ENV = DEFAULT_ENV


class ConfigError(RuntimeError):
    pass


def active_env() -> str:
    raw = _ACTIVE_ENV
    if raw not in SUPPORTED_ENVS:
        raise ConfigError(f"Config environment must be one of: {', '.join(sorted(SUPPORTED_ENVS))}")
    return raw


def set_env(env: str) -> str:
    global _ACTIVE_ENV, _CACHE, _CACHE_ENV
    normalized = normalize_env(env)
    _ACTIVE_ENV = normalized
    _CACHE = None
    _CACHE_ENV = None
    return _ACTIVE_ENV


@contextmanager
def using_env(env: str) -> Iterator[None]:
    previous = _ACTIVE_ENV
    set_env(env)
    try:
        yield
    finally:
        set_env(previous)


def get(key: str, default: Any = None) -> Any:
    return all().get(key, default)


def require(key: str) -> Any:
    values = all()
    if key not in values:
        raise ConfigError(f"Missing config key: {key}")
    return values[key]


def all() -> dict[str, Any]:
    global _CACHE, _CACHE_ENV
    env = active_env()
    if _CACHE is None or _CACHE_ENV != env:
        _CACHE = load(env)
        _CACHE_ENV = env
    return dict(_CACHE)


def reload(env: str | None = None) -> dict[str, Any]:
    global _CACHE, _CACHE_ENV
    if env is not None:
        set_env(env)
        return all()
    _CACHE = None
    _CACHE_ENV = None
    return all()


def load(env: str | None = None) -> dict[str, Any]:
    active = normalize_env(env or active_env())
    common = read_yaml(CONFIG_DIR / "common.yaml")
    override = read_yaml(CONFIG_DIR / f"{active}.yaml")
    merged = {**common, **override}
    merged.setdefault("CONFIG_ENV", active)
    return merged


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, Mapping):
        raise ConfigError(f"Config file must contain a mapping: {path}")
    return {str(key): value for key, value in payload.items()}


def lower_key(key: str) -> str:
    return key.lower()


def normalize_env(env: str) -> str:
    normalized = str(env).strip().lower() or DEFAULT_ENV
    if normalized not in SUPPORTED_ENVS:
        raise ConfigError(f"Unsupported config environment: {normalized}")
    return normalized


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
FALLBACK_ENV_FILE = PROJECT_ROOT / ".env.example"


PROVIDER_API_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "openai": ("openai_api_key",),
    "openrouter": ("openrouter_api_key",),
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
    "openrouter": ("OPENROUTER_API_KEY",),
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
    "openrouter",
    "gemini",
    "anthropic",
    "aws-bedrock",
    "groq",
    "voyage",
)


def strip_provider_prefix(provider: str, model: str) -> str:
    normalized = normalize_provider_name(provider) or ""
    aliases = [normalized]
    if normalized == "google":
        aliases.append("gemini")
    elif normalized == "aws-bedrock":
        aliases.append("bedrock")
    for alias in aliases:
        for prefix in (f"{alias}/", f"{alias}:"):
            if model.startswith(prefix):
                return model.removeprefix(prefix)
    return model


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DEFAULT_ENV_FILE if DEFAULT_ENV_FILE.exists() else FALLBACK_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    profile: Literal["openai"] = Field(default_factory=lambda: get("PROFILE"))

    llm_provider: str = Field(default_factory=lambda: get("LLM_PROVIDER"))
    llm_model: str = Field(default_factory=lambda: get("LLM_MODEL"))
    llm_api_key: str | None = None
    llm_endpoint: str | None = None
    llm_temperature: float = Field(default_factory=lambda: get("LLM_TEMPERATURE"))
    llm_max_tokens: int = Field(default_factory=lambda: get("LLM_MAX_TOKENS"))

    openai_auth_mode: Literal["oauth", "api_key"] = Field(
        default_factory=lambda: get("OPENAI_AUTH_MODE")
    )
    openai_codex_auth_profile: str = Field(default_factory=lambda: get("OPENAI_CODEX_AUTH_PROFILE"))
    openai_codex_base_url: str = Field(default_factory=lambda: get("OPENAI_CODEX_BASE_URL"))
    brain_provider_auth_profiles_path: str = Field(
        default_factory=lambda: get("BRAIN_PROVIDER_AUTH_PROFILES_PATH")
    )
    brain_provider_auth_state_dir: str = Field(
        default_factory=lambda: get("BRAIN_PROVIDER_AUTH_STATE_DIR")
    )

    embedding_provider: str = Field(default_factory=lambda: get("EMBEDDING_PROVIDER"))
    embedding_model: str = Field(default_factory=lambda: get("EMBEDDING_MODEL"))
    embedding_api_key: str | None = None
    embedding_dimensions: int = Field(default_factory=lambda: get("EMBEDDING_DIMENSIONS"))

    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
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

    graph_database_provider: str = Field(default_factory=lambda: get("GRAPH_DATABASE_PROVIDER"))
    graph_database_url: str = Field(default_factory=lambda: get("GRAPH_DATABASE_URL"))
    graph_database_name: str = Field(default_factory=lambda: get("GRAPH_DATABASE_NAME"))
    graph_database_username: str = Field(default_factory=lambda: get("GRAPH_DATABASE_USERNAME"))
    graph_database_password: str = Field(default_factory=lambda: get("GRAPH_DATABASE_PASSWORD"))
    enable_backend_access_control: bool = Field(
        default_factory=lambda: get("ENABLE_BACKEND_ACCESS_CONTROL")
    )

    vector_db_provider: str = Field(default_factory=lambda: get("VECTOR_DB_PROVIDER"))
    vector_db_url: str = Field(default_factory=lambda: get("VECTOR_DB_URL"))
    vector_db_port: int = Field(default_factory=lambda: get("VECTOR_DB_PORT"))
    vector_db_name: str = Field(default_factory=lambda: get("VECTOR_DB_NAME"))
    vector_db_key: str = Field(default_factory=lambda: get("VECTOR_DB_KEY"))
    vector_dataset_database_handler: str = Field(
        default_factory=lambda: get("VECTOR_DATASET_DATABASE_HANDLER")
    )
    vector_db_username: str = Field(default_factory=lambda: get("VECTOR_DB_USERNAME"))
    vector_db_password: str = Field(default_factory=lambda: get("VECTOR_DB_PASSWORD"))
    vector_db_host: str = Field(default_factory=lambda: get("VECTOR_DB_HOST"))

    db_provider: str = Field(default_factory=lambda: get("DB_PROVIDER"))
    db_name: str = Field(default_factory=lambda: get("DB_NAME"))
    db_host: str = Field(default_factory=lambda: get("DB_HOST"))
    db_port: int = Field(default_factory=lambda: get("DB_PORT"))
    db_username: str = Field(default_factory=lambda: get("DB_USERNAME"))
    db_password: str = Field(default_factory=lambda: get("DB_PASSWORD"))

    system_root_directory: str = Field(default_factory=lambda: get("SYSTEM_ROOT_DIRECTORY"))
    data_root_directory: str = Field(default_factory=lambda: get("DATA_ROOT_DIRECTORY"))

    google_free_tier: bool = Field(default_factory=lambda: get("GOOGLE_FREE_TIER", False))
    allow_embedding_dimension_change: bool = Field(
        default_factory=lambda: get("ALLOW_EMBEDDING_DIMENSION_CHANGE", False)
    )

    brain_mcp_host: str = Field(default_factory=lambda: get("BRAIN_MCP_HOST"))
    brain_mcp_port: int = Field(default_factory=lambda: get("BRAIN_MCP_PORT"))
    brain_mcp_path: str = Field(default_factory=lambda: get("BRAIN_MCP_PATH"))
    brain_admin_mcp_path: str = Field(
        default_factory=lambda: get("BRAIN_ADMIN_MCP_PATH", "/admin/mcp")
    )
    brain_public_base_url: str = Field(default_factory=lambda: get("BRAIN_PUBLIC_BASE_URL"))
    brain_public_mcp_path: str = Field(default_factory=lambda: get("BRAIN_PUBLIC_MCP_PATH"))
    brain_public_admin_mcp_path: str = Field(
        default_factory=lambda: get("BRAIN_PUBLIC_ADMIN_MCP_PATH", "/admin/mcp")
    )
    brain_backup_dir: str = Field(default_factory=lambda: get("BRAIN_BACKUP_DIR"))
    brain_neo4j_dump_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_NEO4J_DUMP_ENABLED", False)
    )
    brain_neo4j_stop_for_dump: bool = Field(
        default_factory=lambda: get("BRAIN_NEO4J_STOP_FOR_DUMP", False)
    )
    brain_neo4j_docker_container: str = Field(
        default_factory=lambda: get("BRAIN_NEO4J_DOCKER_CONTAINER", "neo4j-cognee")
    )
    brain_neo4j_brew_service: str = Field(
        default_factory=lambda: get("BRAIN_NEO4J_BREW_SERVICE", "neo4j")
    )
    brain_neo4j_launchd_label: str = Field(
        default_factory=lambda: get("BRAIN_NEO4J_LAUNCHD_LABEL", "homebrew.mxcl.neo4j")
    )
    brain_google_drive_backup_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED", False)
    )
    brain_google_drive_folder: str = Field(
        default_factory=lambda: get("BRAIN_GOOGLE_DRIVE_FOLDER", "backup/brain")
    )
    brain_google_drive_remote: str = Field(
        default_factory=lambda: get("BRAIN_GOOGLE_DRIVE_REMOTE", "gdrive")
    )
    brain_google_drive_local_path: str | None = None
    brain_auth_token: str | None = None
    brain_auth_password: str | None = None
    brain_auth_password_file: str = Field(
        default_factory=lambda: get("BRAIN_AUTH_PASSWORD_FILE", "./secrets/brain-auth-password")
    )
    brain_auth_users_file: str | None = Field(
        default_factory=lambda: get("BRAIN_AUTH_USERS_FILE", None)
    )
    brain_auth_superuser_ids: str = Field(
        default_factory=lambda: get("BRAIN_AUTH_SUPERUSER_IDS", "")
    )
    brain_auth_state_path: str = Field(
        default_factory=lambda: get("BRAIN_AUTH_STATE_PATH", "./secrets/brain-oauth.json")
    )
    brain_auth_scopes: str = Field(
        default_factory=lambda: get("BRAIN_AUTH_SCOPES", "brain.memory.read brain.memory.write")
    )
    brain_auth_require_pkce: bool = Field(
        default_factory=lambda: get("BRAIN_AUTH_REQUIRE_PKCE", True)
    )
    brain_auth_access_token_seconds: int = Field(
        default_factory=lambda: get("BRAIN_AUTH_ACCESS_TOKEN_SECONDS", 3600)
    )
    brain_auth_refresh_token_seconds: int = Field(
        default_factory=lambda: get("BRAIN_AUTH_REFRESH_TOKEN_SECONDS", 60 * 60 * 24 * 30)
    )
    brain_request_log_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_REQUEST_LOG_ENABLED", False)
    )
    brain_request_log_path: str = Field(
        default_factory=lambda: get("BRAIN_REQUEST_LOG_PATH", "./.data/logs/requests.jsonl")
    )
    brain_request_log_max_body_bytes: int = Field(
        default_factory=lambda: get("BRAIN_REQUEST_LOG_MAX_BODY_BYTES", 1024 * 1024)
    )
    brain_request_log_retention_days: int = Field(
        default_factory=lambda: get("BRAIN_REQUEST_LOG_RETENTION_DAYS", 30)
    )
    brain_routing_log_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_ROUTING_LOG_ENABLED", False)
    )
    brain_routing_log_path: str = Field(
        default_factory=lambda: get("BRAIN_ROUTING_LOG_PATH", "./.data/logs/routing/{date}.jsonl")
    )
    brain_routing_log_retention_days: int = Field(
        default_factory=lambda: get("BRAIN_ROUTING_LOG_RETENTION_DAYS", 90)
    )
    brain_service_name: str = Field(default_factory=lambda: get("BRAIN_SERVICE_NAME"))
    brain_database_url: str = Field(default_factory=lambda: get("BRAIN_DATABASE_URL"))
    brain_user_id: str = Field(
        default_factory=lambda: get("BRAIN_USER_ID", get("BRAIN_DEFAULT_USER_ID", "default"))
    )
    brain_owner_full_name: str = Field(
        default_factory=lambda: get("BRAIN_OWNER_FULL_NAME", get("BRAIN_OWNER_NAME"))
    )
    brain_owner_name: str = Field(default_factory=lambda: get("BRAIN_OWNER_NAME"))
    brain_profile_context_path: str = Field(
        default_factory=lambda: get("BRAIN_PROFILE_CONTEXT_PATH")
    )
    brain_llm_enabled: bool = Field(default_factory=lambda: get("BRAIN_LLM_ENABLED"))
    brain_cognee_sync_on_ingest: bool = Field(
        default_factory=lambda: get("BRAIN_COGNEE_SYNC_ON_INGEST", False)
    )
    brain_cognee_sync_on_ingest_sweep_limit: int = Field(
        default_factory=lambda: get("BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT", 25)
    )
    brain_ingest_background_auto_chars: int = Field(
        default_factory=lambda: get("BRAIN_INGEST_BACKGROUND_AUTO_CHARS", 12_000)
    )
    brain_cognee_recall_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_COGNEE_RECALL_ENABLED")
    )
    brain_cognee_memory_dataset: str = Field(
        default_factory=lambda: get("BRAIN_COGNEE_MEMORY_DATASET")
    )
    brain_cognee_sources_dataset: str = Field(
        default_factory=lambda: get("BRAIN_COGNEE_SOURCES_DATASET")
    )
    brain_cognee_data_dataset: str = Field(default_factory=lambda: get("BRAIN_COGNEE_DATA_DATASET"))
    brain_cognee_palate_dataset: str = Field(
        default_factory=lambda: get("BRAIN_COGNEE_PALATE_DATASET", "palate")
    )
    brain_cognee_recall_top_k: int = Field(default_factory=lambda: get("BRAIN_COGNEE_RECALL_TOP_K"))
    brain_taste_enabled: bool = Field(default_factory=lambda: get("BRAIN_TASTE_ENABLED"))
    brain_taste_llm_model: str = Field(default_factory=lambda: get("BRAIN_TASTE_LLM_MODEL"))
    brain_taste_llm_reasoning_effort: Literal["minimal", "low", "medium", "high"] = Field(
        default_factory=lambda: get("BRAIN_TASTE_LLM_REASONING_EFFORT")
    )
    brain_taste_llm_routing_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_TASTE_LLM_ROUTING_ENABLED")
    )
    brain_taste_auto_enrich_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_TASTE_AUTO_ENRICH_ENABLED")
    )
    brain_taste_omdb_api_key: str | None = None
    brain_taste_web_enrichment_enabled: bool = Field(
        default_factory=lambda: get("BRAIN_TASTE_WEB_ENRICHMENT_ENABLED")
    )
    brain_taste_google_places_api_key: str | None = None
    brain_taste_auto_write_threshold: float = Field(
        default_factory=lambda: get("BRAIN_TASTE_AUTO_WRITE_THRESHOLD")
    )
    brain_taste_confirmation_threshold: float = Field(
        default_factory=lambda: get("BRAIN_TASTE_CONFIRMATION_THRESHOLD")
    )
    brain_taste_open_loop_close_threshold: float = Field(
        default_factory=lambda: get("BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD")
    )
    brain_taste_open_loop_confirmation_threshold: float = Field(
        default_factory=lambda: get("BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD")
    )
    brain_taste_proposal_expiry_hours: int = Field(
        default_factory=lambda: get("BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS")
    )
    brain_log_level: str = Field(default_factory=lambda: get("BRAIN_LOG_LEVEL", "INFO"))
    brain_prod_root: str = Field(
        default_factory=lambda: get("BRAIN_PROD_ROOT", "/Volumes/xpg_usb4/prod/brain")
    )
    brain_release_env: str = Field(default_factory=lambda: get("BRAIN_RELEASE_ENV", "dev"))
    brain_release_sha: str = Field(default_factory=lambda: get("BRAIN_RELEASE_SHA", "unknown"))
    brain_release_version: str = Field(default_factory=lambda: get("BRAIN_RELEASE_VERSION", "dev"))
    brain_launchd_label: str = Field(
        default_factory=lambda: get("BRAIN_LAUNCHD_LABEL", "com.brain.mcp")
    )
    brain_health_path: str = Field(default_factory=lambda: get("BRAIN_HEALTH_PATH", "/healthz"))
    brain_ui_enabled: bool = Field(default_factory=lambda: get("BRAIN_UI_ENABLED", False))
    brain_ui_host: str = Field(default_factory=lambda: get("BRAIN_UI_HOST", "127.0.0.1"))
    brain_ui_proxy_port: int = Field(default_factory=lambda: get("BRAIN_UI_PROXY_PORT", 8002))
    brain_ui_frontend_port: int = Field(default_factory=lambda: get("BRAIN_UI_FRONTEND_PORT", 3000))
    brain_ui_backend_port: int = Field(default_factory=lambda: get("BRAIN_UI_BACKEND_PORT", 8001))
    brain_public_ui_path: str = Field(default_factory=lambda: get("BRAIN_PUBLIC_UI_PATH", "/ui"))
    brain_public_ui_api_path: str = Field(
        default_factory=lambda: get("BRAIN_PUBLIC_UI_API_PATH", "/ui-api")
    )
    brain_ui_session_seconds: int = Field(
        default_factory=lambda: get("BRAIN_UI_SESSION_SECONDS", 60 * 60 * 12)
    )
    brain_ui_cache_dir: str = Field(default_factory=lambda: get("BRAIN_UI_CACHE_DIR", ""))
    brain_ui_launchd_label: str = Field(
        default_factory=lambda: get("BRAIN_UI_LAUNCHD_LABEL", "com.brain.ui")
    )

    @model_validator(mode="after")
    def validate_profile(self) -> "Settings":
        if not (
            normalize_provider_name(self.llm_provider) == "openai"
            and self.openai_auth_mode == "oauth"
        ):
            self.llm_api_key = self.llm_api_key or self.configured_provider_api_key(
                self.llm_provider
            )
        if not (
            normalize_provider_name(self.embedding_provider) == "openai"
            and self.openai_auth_mode == "oauth"
        ):
            self.embedding_api_key = self.embedding_api_key or self.configured_provider_api_key(
                self.embedding_provider
            )

        if self.profile != "openai":
            raise ValueError("Brain runtime supports PROFILE=openai only")

        self.llm_provider = normalize_provider_name(self.llm_provider) or self.llm_provider
        self.llm_model = strip_provider_prefix(self.llm_provider, self.llm_model)
        expected_llm_provider = str(get("LLM_PROVIDER"))
        expected_llm_model = str(get("LLM_MODEL"))
        if self.llm_provider != expected_llm_provider or self.llm_model != expected_llm_model:
            raise ValueError(
                "Brain runtime LLM is fixed to "
                f"{expected_llm_provider}:{expected_llm_model}; "
                "use eval/smoke --models for explicit model experiments."
            )

        self.embedding_provider = (
            normalize_provider_name(self.embedding_provider) or self.embedding_provider
        )
        self.embedding_model = strip_provider_prefix(
            self.embedding_provider,
            self.embedding_model,
        )
        expected_embedding_provider = str(get("EMBEDDING_PROVIDER"))
        expected_embedding_model = str(get("EMBEDDING_MODEL"))
        expected_embedding_dimensions = int(get("EMBEDDING_DIMENSIONS"))
        if (
            self.embedding_provider != expected_embedding_provider
            or self.embedding_model != expected_embedding_model
            or self.embedding_dimensions != expected_embedding_dimensions
        ):
            raise ValueError(
                "Brain runtime embeddings are fixed to "
                f"{expected_embedding_provider}:{expected_embedding_model} "
                f"with {expected_embedding_dimensions} dimensions; "
                "use eval/smoke --models for explicit embedding experiments."
            )

        self.brain_mcp_path = normalize_path(self.brain_mcp_path)
        self.brain_admin_mcp_path = normalize_path(self.brain_admin_mcp_path)
        self.brain_public_mcp_path = normalize_path(self.brain_public_mcp_path)
        self.brain_public_admin_mcp_path = normalize_path(self.brain_public_admin_mcp_path)
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
        if normalize_provider_name(provider) == "openai" and self.openai_auth_mode != "api_key":
            return None

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
    def public_admin_mcp_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_admin_mcp_path}"

    @property
    def public_ui_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_ui_path}"

    @property
    def public_ui_api_url(self) -> str:
        return f"{self.brain_public_base_url.rstrip('/')}{self.brain_public_ui_api_path}"

    @property
    def protected_resource_metadata_url(self) -> str:
        return self.protected_resource_metadata_url_for_path(self.brain_public_mcp_path)

    def protected_resource_metadata_url_for_path(self, resource_path: str) -> str:
        path = normalize_path(resource_path).strip("/")
        return (
            f"{self.brain_public_base_url.rstrip('/')}/.well-known/oauth-protected-resource/{path}"
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
    def brain_auth_superuser_id_list(self) -> list[str]:
        return split_csv_setting(self.brain_auth_superuser_ids)

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


def load_settings(
    env_file: str | Path | None = None,
    *,
    config_env: str | None = None,
) -> Settings:
    if config_env is not None:
        set_env(config_env)
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
        "OPENAI_AUTH_MODE": settings.openai_auth_mode,
        "OPENAI_CODEX_AUTH_PROFILE": settings.openai_codex_auth_profile,
        "OPENAI_CODEX_BASE_URL": settings.openai_codex_base_url,
        "BRAIN_PROVIDER_AUTH_PROFILES_PATH": settings.brain_provider_auth_profiles_path,
        "BRAIN_PROVIDER_AUTH_STATE_DIR": settings.brain_provider_auth_state_dir,
        "EMBEDDING_PROVIDER": settings.embedding_provider,
        "EMBEDDING_MODEL": settings.embedding_model,
        "EMBEDDING_DIMENSIONS": str(settings.embedding_dimensions),
        "GRAPH_DATABASE_PROVIDER": settings.graph_database_provider,
        "GRAPH_DATABASE_URL": settings.graph_database_url,
        "GRAPH_DATABASE_NAME": settings.graph_database_name,
        "GRAPH_DATABASE_USERNAME": settings.graph_database_username,
        "GRAPH_DATABASE_PASSWORD": settings.graph_database_password,
        "ENABLE_BACKEND_ACCESS_CONTROL": str(settings.enable_backend_access_control).lower(),
        "VECTOR_DB_PROVIDER": settings.vector_db_provider,
        "VECTOR_DB_URL": (
            str(repo_path(settings.vector_db_url))
            if settings.vector_db_provider == "lancedb" and settings.vector_db_url
            else settings.vector_db_url
        ),
        "VECTOR_DB_PORT": str(settings.vector_db_port),
        "VECTOR_DB_NAME": settings.vector_db_name,
        "VECTOR_DB_KEY": settings.vector_db_key,
        "VECTOR_DATASET_DATABASE_HANDLER": settings.vector_dataset_database_handler,
        "VECTOR_DB_USERNAME": settings.vector_db_username,
        "VECTOR_DB_PASSWORD": settings.vector_db_password,
        "VECTOR_DB_HOST": settings.vector_db_host,
        "DB_PROVIDER": settings.db_provider,
        "DB_NAME": settings.db_name,
        "DB_HOST": settings.db_host,
        "DB_PORT": str(settings.db_port),
        "DB_USERNAME": settings.db_username,
        "DB_PASSWORD": settings.db_password,
        "SYSTEM_ROOT_DIRECTORY": str(repo_path(settings.system_root_directory)),
        "DATA_ROOT_DIRECTORY": str(repo_path(settings.data_root_directory)),
        "BRAIN_MCP_HOST": settings.brain_mcp_host,
        "BRAIN_MCP_PORT": str(settings.brain_mcp_port),
        "BRAIN_MCP_PATH": settings.brain_mcp_path,
        "BRAIN_ADMIN_MCP_PATH": settings.brain_admin_mcp_path,
        "BRAIN_PUBLIC_BASE_URL": settings.brain_public_base_url,
        "BRAIN_PUBLIC_MCP_PATH": settings.brain_public_mcp_path,
        "BRAIN_PUBLIC_ADMIN_MCP_PATH": settings.brain_public_admin_mcp_path,
        "BRAIN_BACKUP_DIR": settings.brain_backup_dir,
        "BRAIN_NEO4J_DUMP_ENABLED": str(settings.brain_neo4j_dump_enabled).lower(),
        "BRAIN_NEO4J_STOP_FOR_DUMP": str(settings.brain_neo4j_stop_for_dump).lower(),
        "BRAIN_NEO4J_DOCKER_CONTAINER": settings.brain_neo4j_docker_container,
        "BRAIN_NEO4J_BREW_SERVICE": settings.brain_neo4j_brew_service,
        "BRAIN_NEO4J_LAUNCHD_LABEL": settings.brain_neo4j_launchd_label,
        "BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED": str(
            settings.brain_google_drive_backup_enabled
        ).lower(),
        "BRAIN_GOOGLE_DRIVE_FOLDER": settings.brain_google_drive_folder,
        "BRAIN_AUTH_PASSWORD_FILE": settings.brain_auth_password_file,
        "BRAIN_AUTH_USERS_FILE": settings.brain_auth_users_file or "",
        "BRAIN_AUTH_SUPERUSER_IDS": settings.brain_auth_superuser_ids,
        "BRAIN_AUTH_STATE_PATH": settings.brain_auth_state_path,
        "BRAIN_AUTH_SCOPES": settings.brain_auth_scopes,
        "BRAIN_AUTH_REQUIRE_PKCE": str(settings.brain_auth_require_pkce).lower(),
        "BRAIN_AUTH_ACCESS_TOKEN_SECONDS": str(settings.brain_auth_access_token_seconds),
        "BRAIN_AUTH_REFRESH_TOKEN_SECONDS": str(settings.brain_auth_refresh_token_seconds),
        "BRAIN_REQUEST_LOG_ENABLED": str(settings.brain_request_log_enabled).lower(),
        "BRAIN_REQUEST_LOG_PATH": settings.brain_request_log_path,
        "BRAIN_REQUEST_LOG_MAX_BODY_BYTES": str(settings.brain_request_log_max_body_bytes),
        "BRAIN_REQUEST_LOG_RETENTION_DAYS": str(settings.brain_request_log_retention_days),
        "BRAIN_ROUTING_LOG_ENABLED": str(settings.brain_routing_log_enabled).lower(),
        "BRAIN_ROUTING_LOG_PATH": settings.brain_routing_log_path,
        "BRAIN_ROUTING_LOG_RETENTION_DAYS": str(settings.brain_routing_log_retention_days),
        "BRAIN_DATABASE_URL": settings.brain_database_url,
        "BRAIN_USER_ID": settings.brain_user_id,
        "BRAIN_OWNER_FULL_NAME": settings.brain_owner_full_name,
        "BRAIN_OWNER_NAME": settings.brain_owner_name,
        "BRAIN_PROFILE_CONTEXT_PATH": settings.brain_profile_context_path,
        "BRAIN_LLM_ENABLED": str(settings.brain_llm_enabled).lower(),
        "BRAIN_COGNEE_SYNC_ON_INGEST": str(settings.brain_cognee_sync_on_ingest).lower(),
        "BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT": str(
            settings.brain_cognee_sync_on_ingest_sweep_limit
        ),
        "BRAIN_INGEST_BACKGROUND_AUTO_CHARS": str(settings.brain_ingest_background_auto_chars),
        "BRAIN_COGNEE_RECALL_ENABLED": str(settings.brain_cognee_recall_enabled).lower(),
        "BRAIN_COGNEE_MEMORY_DATASET": settings.brain_cognee_memory_dataset,
        "BRAIN_COGNEE_SOURCES_DATASET": settings.brain_cognee_sources_dataset,
        "BRAIN_COGNEE_DATA_DATASET": settings.brain_cognee_data_dataset,
        "BRAIN_COGNEE_PALATE_DATASET": settings.brain_cognee_palate_dataset,
        "BRAIN_COGNEE_RECALL_TOP_K": str(settings.brain_cognee_recall_top_k),
        "BRAIN_TASTE_ENABLED": str(settings.brain_taste_enabled).lower(),
        "BRAIN_TASTE_LLM_MODEL": settings.brain_taste_llm_model,
        "BRAIN_TASTE_LLM_REASONING_EFFORT": settings.brain_taste_llm_reasoning_effort,
        "BRAIN_TASTE_LLM_ROUTING_ENABLED": str(settings.brain_taste_llm_routing_enabled).lower(),
        "BRAIN_TASTE_AUTO_ENRICH_ENABLED": str(settings.brain_taste_auto_enrich_enabled).lower(),
        "BRAIN_TASTE_WEB_ENRICHMENT_ENABLED": str(
            settings.brain_taste_web_enrichment_enabled
        ).lower(),
        "BRAIN_TASTE_AUTO_WRITE_THRESHOLD": str(settings.brain_taste_auto_write_threshold),
        "BRAIN_TASTE_CONFIRMATION_THRESHOLD": str(settings.brain_taste_confirmation_threshold),
        "BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD": str(
            settings.brain_taste_open_loop_close_threshold
        ),
        "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD": str(
            settings.brain_taste_open_loop_confirmation_threshold
        ),
        "BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS": str(settings.brain_taste_proposal_expiry_hours),
        "BRAIN_LOG_LEVEL": settings.brain_log_level,
        "BRAIN_UI_ENABLED": str(settings.brain_ui_enabled).lower(),
        "BRAIN_UI_HOST": settings.brain_ui_host,
        "BRAIN_UI_PROXY_PORT": str(settings.brain_ui_proxy_port),
        "BRAIN_UI_FRONTEND_PORT": str(settings.brain_ui_frontend_port),
        "BRAIN_UI_BACKEND_PORT": str(settings.brain_ui_backend_port),
        "BRAIN_PUBLIC_UI_PATH": settings.brain_public_ui_path,
        "BRAIN_PUBLIC_UI_API_PATH": settings.brain_public_ui_api_path,
        "BRAIN_UI_SESSION_SECONDS": str(settings.brain_ui_session_seconds),
        "BRAIN_UI_CACHE_DIR": settings.brain_ui_cache_dir,
        "BRAIN_RELEASE_ENV": settings.brain_release_env,
        "BRAIN_RELEASE_SHA": settings.brain_release_sha,
        "BRAIN_RELEASE_VERSION": settings.brain_release_version,
    }
    optional_values = {
        "LLM_API_KEY": settings.llm_api_key,
        "LLM_ENDPOINT": settings.llm_endpoint,
        "EMBEDDING_API_KEY": settings.embedding_api_key,
        "BRAIN_AUTH_TOKEN": settings.brain_auth_token,
        "BRAIN_AUTH_PASSWORD": settings.brain_auth_password,
        "BRAIN_GOOGLE_DRIVE_LOCAL_PATH": settings.brain_google_drive_local_path,
        "BRAIN_TASTE_OMDB_API_KEY": settings.brain_taste_omdb_api_key,
        "BRAIN_TASTE_GOOGLE_PLACES_API_KEY": settings.brain_taste_google_places_api_key,
    }
    optional_values.update(provider_api_environment(settings))
    for key, value in optional_values.items():
        if value:
            values[key] = value
    return values


def apply_runtime_environment(settings: Settings) -> None:
    for key, value in runtime_env(settings).items():
        os.environ[key] = value
    path_values = [
        runtime_env(settings)["SYSTEM_ROOT_DIRECTORY"],
        runtime_env(settings)["DATA_ROOT_DIRECTORY"],
    ]
    if settings.vector_db_provider == "lancedb" and runtime_env(settings)["VECTOR_DB_URL"]:
        path_values.append(runtime_env(settings)["VECTOR_DB_URL"])
    for path_value in path_values:
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
