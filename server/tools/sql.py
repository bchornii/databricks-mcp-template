"""Databricks SQL tools."""

from server.auth import get_user_authenticated_workspace_client
from server.errors import tool_error_response
from server.infrastructure.sql import execute_query


def register(mcp_server) -> None:
    @mcp_server.tool
    def run_sql_query(query: str, warehouse_id: str = None) -> dict:
        """
        Execute a SQL query using Databricks SQL.

        Args:
            query: The SQL query to execute.
            warehouse_id: SQL warehouse ID (optional, uses first available
                warehouse if not specified).

        Returns:
            Dictionary containing query results.
        """
        try:
            client = get_user_authenticated_workspace_client()
            return execute_query(client, query, warehouse_id)
        except Exception as e:
            return tool_error_response(e, context="run_sql_query")
