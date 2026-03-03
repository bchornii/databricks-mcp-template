"""Databricks SQL query execution integration.

All functions take an explicit ``client`` parameter (a ``WorkspaceClient``
instance) so they can be unit-tested with a mock.
"""

import logging

logger = logging.getLogger(__name__)


class NoWarehouseError(Exception):
    """Raised when no SQL warehouses are available for query execution."""


def execute_query(client, query: str, warehouse_id: str | None = None) -> dict:
    """
    Execute a SQL statement via Databricks SQL Statement Execution API.

    If *warehouse_id* is not provided, the first available warehouse is
    used automatically.

    Args:
        client: A user-authenticated ``WorkspaceClient``.
        query: The SQL statement to execute.
        warehouse_id: Optional warehouse ID.  When ``None``, the first
            available warehouse is selected automatically.

    Returns:
        A dict with ``status``, ``warehouse_id``, ``query``, and either
        ``result`` (on success) or ``error`` (on failure).

    Raises:
        NoWarehouseError: If no SQL warehouses are available and
            *warehouse_id* was not provided.
    """
    if not warehouse_id:
        warehouse_id = _resolve_warehouse(client)

    logger.debug("Executing SQL on warehouse %s: %.80s…", warehouse_id, query)

    result = client.statement_execution.execute_statement(
        statement=query,
        warehouse_id=warehouse_id,
    )

    if result.status.state.value == "SUCCEEDED":
        return {
            "status": "success",
            "warehouse_id": warehouse_id,
            "query": query,
            "result": result.result.data_array if result.result else [],
        }

    error_msg = (
        result.status.error.message if result.status.error else "Unknown error"
    )
    return {
        "status": "failed",
        "warehouse_id": warehouse_id,
        "query": query,
        "error": error_msg,
    }


def _resolve_warehouse(client) -> str:
    """Pick the first available warehouse or raise ``NoWarehouseError``."""
    warehouses = list(client.warehouses.list())
    if not warehouses:
        raise NoWarehouseError("No SQL warehouses available in this workspace")
    warehouse_id = warehouses[0].id
    logger.debug("Auto-selected warehouse %s", warehouse_id)
    return warehouse_id
