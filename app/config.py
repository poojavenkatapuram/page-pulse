from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", enable_decoding=False)

    app_name: str = "Page Pulse API"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    fetch_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    max_redirects: int = Field(default=5, ge=0, le=10)
    max_response_bytes: int = Field(default=2_000_000, ge=1_024, le=10_000_000)
    user_agent: str = "PagePulse/1.0"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
