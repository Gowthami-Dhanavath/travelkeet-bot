"""App configuration settings."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: list[str] = []
    database_url: str = Field(..., alias="DATABASE_URL")

    @property
    def async_database_url(self) -> str:
        """Return DATABASE_URL with the asyncpg driver prefix.

        Railway injects postgresql://... — SQLAlchemy async needs
        postgresql+asyncpg://... This normalizes for either format.
        """
        url = self.database_url
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    grok_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GROK_API_KEY", "XAI_API_KEY"),
    )


settings = Settings()
