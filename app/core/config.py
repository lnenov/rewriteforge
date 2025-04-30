# app/core/config.py
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings"""

    model_config = SettingsConfigDict(
        env_file=".env",  # Load .env file if present
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars not defined in the model
    )

    PORT: int = 8000
    RELOAD: bool = False  # Set to True for development uvicorn reload

    # LLM Configuration
    LLM_PROVIDER: Literal["stub", "openai", "anthropic"] = "stub"
    LLM_API_KEY: Optional[str] = Field(
        None, description="API Key for the selected LLM provider"
    )

    # Feature Flags / Limits
    MAX_TEXT_LENGTH: int = 5000

    # Stretch Goal: Caching
    CACHE_ENABLED: bool = False  # Set to True via env var to enable
    CACHE_TTL_SECONDS: int = 300  # Time-to-live for cache entries (5 mins)
    CACHE_MAX_SIZE: int = 1024  # Max number of entries in cache


# Singleton instance for easy access
settings = Settings()
