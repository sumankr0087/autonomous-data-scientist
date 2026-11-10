"""Central application configuration.

All runtime configuration is loaded from environment variables (and an optional
`.env` file) through a single typed `Settings` object. Import `get_settings()`
anywhere in the codebase instead of reading `os.environ` directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = two levels up from this file (config/ -> project root).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


class Settings(BaseSettings):
    """Typed application settings loaded from the environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "autonomous-data-scientist"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # ---- Logging ----
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = Field(
        default=False,
        description="Emit JSON lines to the file handler (useful in production).",
    )
    log_to_file: bool = True

    # ---- LLM ----
    llm_provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2000
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    # ---- Data / DB ----
    duckdb_path: str = str(DATA_DIR / "warehouse.duckdb")

    # ---- Agent workflow ----
    max_agent_steps: int = 25
    enable_human_approval: bool = True
    enable_reflection: bool = True

    @property
    def active_api_key(self) -> str | None:
        """Return the API key for the configured provider."""
        return {
            "gemini": self.google_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }.get(self.llm_provider)


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton `Settings` instance."""
    settings = Settings()
    # Ensure runtime directories exist.
    for directory in (LOGS_DIR, DATA_DIR, ARTIFACTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    return settings
