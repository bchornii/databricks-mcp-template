"""
Authentication helpers for the MCP server.

This module provides two levels of Databricks ``WorkspaceClient`` authentication:

* **App-level** (``get_workspace_client``) — authenticates as the Databricks App
  service principal in production, or via ``~/.databrickscfg`` locally.
* **User-level** (``get_user_authenticated_workspace_client``) — authenticates on
  behalf of the end-user whose OAuth token is forwarded by the Databricks Apps
  proxy in the ``x-forwarded-access-token`` header.

The ``header_store`` context-variable is populated per-request by the middleware
in ``app.py`` and consumed here to extract the user token.

Design note
-----------
Services should **never** import this module directly.  Instead, tool adapters
call the factories here and pass the resulting client into service functions.
This keeps the service layer free of global state and easy to unit-test.
"""

import contextvars
import logging
from typing import Any

from server.config import get_settings

logger = logging.getLogger(__name__)

try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    WorkspaceClient = None

# --------------------------------------------------------------------------- #
# Request-scoped header storage (set by middleware in app.py)
# --------------------------------------------------------------------------- #

header_store: contextvars.ContextVar[dict] = contextvars.ContextVar("header_store")


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #


def is_databricks_sdk_available() -> bool:
    """Return ``True`` if the ``databricks-sdk`` package is importable."""
    return WorkspaceClient is not None


# --------------------------------------------------------------------------- #
# Client factories
# --------------------------------------------------------------------------- #


def _require_workspace_client() -> Any:
    """Guard: raise immediately if the SDK is not installed."""
    if WorkspaceClient is None:
        raise RuntimeError(
            "databricks-sdk is not installed. Install optional Databricks dependencies "
            "to use Databricks-backed tools."
        )
    return WorkspaceClient


def get_workspace_client():
    """
    Return a ``WorkspaceClient`` authenticated as the **application** identity.

    * In production (Databricks App): uses the service principal attached to the app.
    * Locally: falls back to default ``~/.databrickscfg`` authentication.
    """
    workspace_client_cls = _require_workspace_client()
    logger.debug("Creating app-level WorkspaceClient")
    return workspace_client_cls()


def get_user_authenticated_workspace_client():
    """
    Return a ``WorkspaceClient`` authenticated as the **end-user**.

    * In production: reads the user's OAuth token from the
      ``x-forwarded-access-token`` request header (set by Databricks Apps proxy).
    * Locally: falls back to default ``~/.databrickscfg`` authentication.

    Raises:
        RuntimeError: If the Databricks SDK is not installed.
        ValueError: If running in production but the user token header is missing.
    """
    workspace_client_cls = _require_workspace_client()
    settings = get_settings()

    if not settings.is_deployed:
        logger.debug("Local mode — using default auth for user client")
        return workspace_client_cls()

    # Production: extract user token from request headers
    headers = header_store.get({})
    token = headers.get(settings.user_token_header)

    if not token:
        logger.warning("Missing user token header '%s'", settings.user_token_header)
        raise ValueError(
            f"Authentication token not found in request headers ({settings.user_token_header}). "
        )

    logger.debug("Creating user-authenticated WorkspaceClient")
    return workspace_client_cls(token=token, auth_type="pat")
