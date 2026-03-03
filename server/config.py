"""
Centralized configuration for the MCP server.

All application settings are defined here using Pydantic BaseSettings,
which provides:
- Type validation at startup
- Environment variable overrides (e.g., SERVER_PORT=9000)
- .env file support for local development
- A single source of truth for configuration values

Usage:
    from server.config import get_settings

    settings = get_settings()
    print(settings.server_name)
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable overrides.

    Every field can be overridden by setting an environment variable with
    the matching name (case-insensitive). For example:
        SERVER_PORT=8080  →  settings.server_port == 8080
        SERVER_HOST=127.0.0.1  →  settings.server_host == "127.0.0.1"
    """

    # --- Server ---
    server_name: str = "custom-mcp-server"
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    log_level: str = "INFO"

    # --- Paths ---
    static_dir: Path = Path(__file__).parent / "../static"

    # --- Databricks ---
    databricks_app_name: str | None = None
    """
    When set (automatically by Databricks Apps runtime), the server switches
    to production auth mode: app-level service principal + user token from
    the ``x-forwarded-access-token`` header.  When absent, the server uses
    default local Databricks CLI authentication for both auth modes.
    """

    # --- Auth header ---
    user_token_header: str = "x-forwarded-access-token"
    """Name of the header that carries the end-user OAuth token in production."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def is_deployed(self) -> bool:
        """True when running inside a Databricks App (production)."""
        return self.databricks_app_name is not None


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The instance is created once and reused for the lifetime of the process.
    To override values in tests, monkeypatch environment variables *before*
    the first call, or clear the cache with ``get_settings.cache_clear()``.
    """
    return Settings()
