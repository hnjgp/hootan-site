"""Application settings loaded from environment variables and the root .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Typed settings; real environment variables override values from .env."""

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    app_env: str = "development"
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Return the settings, read once and cached."""
    return Settings()
