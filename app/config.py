"""App configuration settings."""
from pydantic import BaseModel


class Settings(BaseModel):
    cors_origins: list[str] = []


settings = Settings()
