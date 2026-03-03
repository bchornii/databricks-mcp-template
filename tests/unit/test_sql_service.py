"""Unit tests for ``server.infrastructure.sql``."""

from unittest.mock import MagicMock

import pytest

from server.infrastructure.sql import NoWarehouseError, execute_query


def _make_mock_sql_client(*, success: bool = True, warehouses=None):
    """Build a mock WorkspaceClient wired for SQL execution."""
    client = MagicMock()

    # warehouses.list()
    if warehouses is None:
        wh = MagicMock()
        wh.id = "wh-001"
        warehouses = [wh]
    client.warehouses.list.return_value = warehouses

    # statement_execution.execute_statement()
    result = MagicMock()
    result.status.state.value = "SUCCEEDED" if success else "FAILED"
    if success:
        result.result.data_array = [["row1_col1", "row1_col2"]]
    else:
        result.status.error.message = "Syntax error near SELECT"
    client.statement_execution.execute_statement.return_value = result

    return client


class TestExecuteQuery:
    def test_successful_query_with_explicit_warehouse(self):
        client = _make_mock_sql_client(success=True)
        result = execute_query(client, "SELECT 1", warehouse_id="wh-explicit")

        assert result["status"] == "success"
        assert result["warehouse_id"] == "wh-explicit"
        assert result["query"] == "SELECT 1"
        assert len(result["result"]) == 1

    def test_auto_selects_first_warehouse(self):
        client = _make_mock_sql_client(success=True)
        result = execute_query(client, "SELECT 1")

        assert result["warehouse_id"] == "wh-001"

    def test_raises_when_no_warehouses(self):
        client = _make_mock_sql_client(warehouses=[])

        with pytest.raises(NoWarehouseError, match="No SQL warehouses"):
            execute_query(client, "SELECT 1")

    def test_failed_query_returns_error(self):
        client = _make_mock_sql_client(success=False)
        result = execute_query(client, "BAD SQL", warehouse_id="wh-001")

        assert result["status"] == "failed"
        assert "Syntax error" in result["error"]
