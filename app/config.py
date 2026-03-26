"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./newbirth_church.db"

    # Integrations
    YOUTUBE_API_KEY: str = ""

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    # Church Info (White Label)
    CHURCH_NAME: str = "New Birth Praise and Worship Center"
    CHURCH_ADDRESS: str = ""
    CHURCH_PHONE: str = ""
    CHURCH_EMAIL: str = ""
    CHURCH_WEBSITE: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
