"""
Standardized error handling for MCP tools.

Every tool should return structured data — including on failure.  This module
provides a single ``tool_error_response`` helper that:

1. Logs the exception with full traceback (visible to operators).
2. Returns a **consistent** error dict to the AI client.

Consistent error shape
----------------------
All error responses follow this structure::

    {
        "success": False,
        "error": "Human-readable message",
        "error_type": "ValueError",
        "context": "get_current_user"
    }

AI consumers can rely on ``"success": False`` to detect failures regardless
of which tool produced them.

Usage in a tool adapter::

    from server.errors import tool_error_response

    @mcp_server.tool
    def my_tool(param: str) -> dict:
        try:
            result = my_service.do_work(param)
            return {"success": True, "data": result}
        except Exception as e:
            return tool_error_response(e, context="my_tool")
"""

import logging

logger = logging.getLogger(__name__)


def tool_error_response(
    exc: Exception,
    *,
    context: str,
    message: str | None = None,
) -> dict:
    """
    Build a standardized error dict and log the exception.

    Args:
        exc: The caught exception.
        context: A short label identifying the tool or operation that failed
            (e.g. ``"get_current_user"``, ``"list_workspace_files"``).
        message: Optional human-friendly message.  When omitted, the
            string representation of *exc* is used.

    Returns:
        A dict with keys ``success``, ``error``, ``error_type``, and
        ``context`` — safe to return directly from a tool function.
    """
    logger.exception("Tool error in %s", context)
    return {
        "success": False,
        "error": message or str(exc),
        "error_type": type(exc).__name__,
        "context": context,
    }
