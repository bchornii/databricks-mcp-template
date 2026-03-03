"""
Backwards-compatibility shim — all functionality has moved to ``server.auth``.

Existing imports like ``from server import utils`` or
``from .utils import header_store`` will continue to work.  New code should
import from ``server.auth`` directly.
"""

from server.auth import (  # noqa: F401
    get_user_authenticated_workspace_client,
    get_workspace_client,
    header_store,
    is_databricks_sdk_available,
)
