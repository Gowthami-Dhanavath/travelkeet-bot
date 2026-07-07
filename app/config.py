"""App configuration settings."""
import sys

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Required
    database_url: str = Field(..., validation_alias=AliasChoices("DATABASE_URL"))

    # LLM — accept multiple aliases in case older env has GROK_/XAI_
    groq_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GROQ_API_KEY", "GROK_API_KEY", "XAI_API_KEY"),
    )

    # Optional (Railway sets these; missing ones default to empty)
    allowed_origins: str = ""
    admin_api_key_hash: str = ""
    resend_api_key: str = ""

    # DB pool tuning (defaults are fine)
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_echo: bool = False

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        """Normalize Railway's postgresql:// to postgresql+asyncpg://."""
        url = self.database_url
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()

# Debug prints — remove after Day 13 is green
