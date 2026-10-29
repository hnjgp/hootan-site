"""Application settings loaded from environment variables and the root .env file."""

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Typed settings; real environment variables override values from .env."""

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    app_env: str = "development"
    database_url: str
    secret_key: str = "dev-secret"
    contact_email: str = ""

    llm_base_url: str = "https://api.avalai.ir/v1"
    llm_api_key: str = ""
    model_twin: str = "gemini-2.5-flash-lite"
    model_jobfit: str = "gpt-4.1-mini"
    model_trading: str = "gpt-5-nano"
    model_translate: str = "gpt-4.1-nano"
    model_embed: str = "text-embedding-3-small"

    budget_monthly_usd: Decimal = Decimal(5)
    budget_trading_daily_usd: Decimal = Decimal("0.06")
    budget_public_daily_usd: Decimal = Decimal("0.10")
    ai_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return the settings, read once and cached."""
    return Settings()
