"""Application settings loaded from environment variables and ``.env``.

All settings are environment-driven; nothing is hardcoded. Values are
validated at startup by pydantic-settings.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Typed runtime configuration.

    Environment variables (or a ``.env`` file in the project root) override
    the defaults below. Field names match ``.env.example`` keys case-insensitively.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Database (PostgreSQL)
    database_url: str = Field(
        default="postgresql+psycopg2://dota_tracker:change_me@localhost:5432/dota_tracker"
    )

    # OpenDota API
    opendota_base_url: str = Field(default="https://api.opendota.com/api")
    opendota_api_key: str = Field(default="")
    opendota_timeout_seconds: int = Field(default=30)
    opendota_max_retries: int = Field(default=3)
    opendota_rate_limit_rpm: int = Field(default=60)


def load_settings() -> AppSettings:
    """Load and validate application settings from environment / ``.env``."""
    return AppSettings()


__all__ = ["AppSettings", "load_settings"]
