"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Multi-Agent Academic Research Platform"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    api_key: SecretStr | None = None

    database_url: str = "postgresql+asyncpg://marp:marp@localhost:5432/marp"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: SecretStr | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    semantic_scholar_api_key: SecretStr | None = None
    arxiv_user_agent: str = "MultiAgentResearchPlatform/0.1 (mailto:research@example.com)"

    default_max_papers: int = Field(default=20, ge=1, le=100)
    default_max_critic_loops: int = Field(default=2, ge=0, le=5)
    http_timeout_seconds: float = Field(default=30.0, ge=5.0, le=120.0)

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def api_key_required(self) -> bool:
        return self.api_key is not None and bool(self.api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
