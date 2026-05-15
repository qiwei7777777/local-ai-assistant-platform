from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = Field(default="Local AI Assistant Platform", alias="APP_NAME")
    app_version: str = Field(default="1.2.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("APP_HOST", "BACKEND_HOST"),
    )
    app_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("APP_PORT", "BACKEND_PORT"),
    )
    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "BACKEND_CORS_ORIGINS"),
    )
    backend_cors_origin_regex: str = Field(
        default=r"^https?://(localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?::3000)?$",
        validation_alias=AliasChoices("CORS_ORIGIN_REGEX", "BACKEND_CORS_ORIGIN_REGEX"),
    )
    database_url: str = Field(
        default="sqlite:///./data/local_ai_assistant.db",
        alias="DATABASE_URL",
    )
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    vector_store_dir: str = Field(default="./data/vector_store", alias="VECTOR_STORE_DIR")
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_default_model: str = Field(
        default="gemma4:e4b",
        alias="OLLAMA_DEFAULT_MODEL",
    )
    ollama_request_timeout: int = Field(
        default=120,
        alias="OLLAMA_REQUEST_TIMEOUT",
    )
    chat_default_temperature: float = Field(
        default=0.7,
        alias="CHAT_DEFAULT_TEMPERATURE",
    )
    chat_default_max_tokens: int = Field(
        default=1024,
        alias="CHAT_DEFAULT_MAX_TOKENS",
    )
    chat_max_context_messages: int = Field(
        default=12,
        alias="CHAT_MAX_CONTEXT_MESSAGES",
    )
    chat_enable_streaming: bool = Field(default=True, alias="CHAT_ENABLE_STREAMING")
    rag_chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=120, alias="RAG_CHUNK_OVERLAP")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    memory_top_k: int = Field(default=3, alias="MEMORY_TOP_K")
    code_workspace_root: str = Field(default="..", alias="CODE_WORKSPACE_ROOT")
    code_agent_max_file_bytes: int = Field(default=120_000, alias="CODE_AGENT_MAX_FILE_BYTES")
    code_agent_command_timeout: int = Field(default=60, alias="CODE_AGENT_COMMAND_TIMEOUT")
    code_agent_model_timeout: int = Field(default=300, alias="CODE_AGENT_MODEL_TIMEOUT")

    @property
    def code_workspace_path(self) -> Path:
        workspace_root = Path(self.code_workspace_root)
        if workspace_root.is_absolute():
            return workspace_root.resolve()
        return (BACKEND_DIR / workspace_root).resolve()

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        return self.backend_cors_origin_regex.strip() or None

    @property
    def database_file_path(self) -> Path | None:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        raw_path = self.database_url[len(prefix):]
        return Path(raw_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
