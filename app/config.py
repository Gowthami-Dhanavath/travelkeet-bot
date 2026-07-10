"""App configuration settings."""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: list[str] = []

    groq_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GROQ_API_KEY", "XAI_API_KEY"),
    )
    resend_api_key: str = ""
    sales_notification_email: str = ""
    sync_feed_url: str = ""
    sentry_dsn: str = ""
    sentry_environment: str = "local"

settings = Settings()
