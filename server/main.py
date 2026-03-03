"""
Main entry point for the MCP server application.

This module provides the ``main()`` function that starts the uvicorn server.
It is registered as the ``custom-mcp-server`` CLI command in ``pyproject.toml``.

Startup sequence:
1. Configure structured logging (``server.logging_config``)
2. Read settings from ``server.config`` (env vars / ``.env``)
3. Parse CLI args (``--port`` overrides the configured default)
4. Start uvicorn with the combined FastAPI/FastMCP application
"""

import argparse
import logging

import uvicorn

from server.config import get_settings
from server.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main():
    """
    Start the MCP server using uvicorn.

    Usage:
        Run with default port:  ``uv run custom-mcp-server``
        Run with custom port:   ``uv run custom-mcp-server --port 8080``
    """
    # 1. Logging first — everything after this can use the logger
    configure_logging()

    # 2. Settings
    settings = get_settings()

    # 3. CLI arg (--port) overrides config default
    parser = argparse.ArgumentParser(description="Start the MCP server")
    parser.add_argument(
        "--port",
        type=int,
        default=settings.server_port,
        help=f"Port to run the server on (default: {settings.server_port})",
    )
    args = parser.parse_args()

    logger.info(
        "Starting %s on %s:%d",
        settings.server_name,
        settings.server_host,
        args.port,
    )

    # 4. Launch
    uvicorn.run(
        "server.app:combined_app",
        host=settings.server_host,
        port=args.port,
    )
