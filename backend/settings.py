"""
Centralized application settings.

Provides a single source of truth for backend runtime configuration.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEV_JWT_FALLBACK = "coliseum-dev-jwt-secret-change-in-production"  # allow-secret


class Settings(BaseSettings):
    """Environment-backed backend configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(default="development", alias="APP_ENV")

    database_url: str = Field(
        default="postgresql+asyncpg://council_user:council_pass@localhost:5432/ai_council",
        alias="DATABASE_URL",
    )
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")
    jwt_secret: str | None = Field(default=None, alias="JWT_SECRET")
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60 * 24, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    demo_director_enabled: bool = Field(default=False, alias="DEMO_DIRECTOR_ENABLED")
    demo_director_autostart_scenario: str | None = Field(
        default=None, alias="DEMO_DIRECTOR_AUTOSTART_SCENARIO"
    )
    demo_scenario_dir: str = Field(default="backend/demo/scenarios", alias="DEMO_SCENARIO_DIR")
    demo_local_reset_enabled: bool = Field(default=True, alias="DEMO_LOCAL_RESET_ENABLED")

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local", "test", "testing"}

    @property
    def database_url_async(self) -> str:
        """Normalize DATABASE_URL for SQLAlchemy async engines."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def jwt_secret_key_resolved(self) -> str:
        """Resolve JWT signing secret with a dev-only fallback."""
        secret = self.jwt_secret_key or self.jwt_secret or self.secret_key  # allow-secret
        if secret:
            return secret
        if self.is_development:
            return DEV_JWT_FALLBACK
        raise RuntimeError(
            "JWT_SECRET_KEY (or legacy JWT_SECRET / SECRET_KEY) must be set when APP_ENV is not development/test"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
