"""Tools package — MCP tool registration adapters.

Each module in this package registers one or more MCP tools for a single
domain.  The tools themselves are **thin adapters** that follow this pattern:

1. Parse / validate input parameters (handled by FastMCP decorator).
2. Obtain an authenticated client from ``server.auth``.
3. Delegate to an application workflow or integration function.
4. Catch exceptions and return a standardized error via ``server.errors``.

Adding a new domain
-------------------
1. Create ``server/application/my_flow.py`` for orchestration logic (optional).
2. Create ``server/tools/my_domain.py`` with a ``register(mcp_server)``
   function that decorates thin adapters with ``@mcp_server.tool``.
3. Call ``server.infrastructure`` from workflows for external I/O.
4. Import and call ``my_domain.register`` inside ``register_all_tools``
   below.
"""

from server.tools import calculations, sql, system, user, workspace


def register_all_tools(mcp_server) -> None:
    """Register every tool domain with *mcp_server*.

    Called once from ``server.app`` during application startup.
    """
    system.register(mcp_server)
    calculations.register(mcp_server)
    user.register(mcp_server)
    workspace.register(mcp_server)
    sql.register(mcp_server)
