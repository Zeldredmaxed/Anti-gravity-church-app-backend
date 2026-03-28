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
    OPENAI_API_KEY: str = ""

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

    # SMTP (email delivery)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # Stripe Payment Gateway
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Twilio SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # SendGrid Email
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""

    # Church Info (White Label)
    CHURCH_NAME: str = "New Birth Praise and Worship Center"
    CHURCH_ADDRESS: str = ""
    CHURCH_PHONE: str = ""
    CHURCH_EMAIL: str = ""
    CHURCH_WEBSITE: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
