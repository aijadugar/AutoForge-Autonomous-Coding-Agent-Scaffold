from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from env with sane local defaults."""

    model_config = SettingsConfigDict(env_prefix="AUTOFORGE_", env_file=".env", extra="ignore")
    GEMINI_API_KEY: str
    environment: str = "local"
    database_url: str = "sqlite:///./autoforge.db"
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    log_level: str = "INFO"
    tool_timeout_seconds: int = 30
    max_tool_retries: int = 2
    rate_limit_per_minute: int = 120
    trace_sample_rate: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

