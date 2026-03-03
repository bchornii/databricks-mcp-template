"""HTTP / external-API tools."""

from server.application.calculations_workflow import execute_calculations
from server.errors import tool_error_response
from server.infrastructure.http import fetch_url_status


def register(mcp_server) -> None:
    @mcp_server.tool
    def fetch_api_status(url: str, timeout_seconds: int = 10) -> dict:
        """
        Call a REST endpoint and return a summarized response.

        This provider-agnostic tool is useful when your MCP server needs to
        integrate with any HTTP API (internal or external) instead of
        Databricks.

        Args:
            url: The HTTP/HTTPS endpoint to call with a GET request.
            timeout_seconds: Request timeout in seconds (default: 10).

        Returns:
            dict: Response summary including status code, content type, and a
            parsed JSON payload when available.
        """
        return fetch_url_status(url, timeout_seconds=timeout_seconds)

    @mcp_server.tool
    def execute_calculations(
        url: str,
        timeout_seconds: int = 10,
        expect_json: bool = False,
    ) -> dict:
        """
        Execute calculation workflow for an API endpoint (fetch → reshape → rules).

        Args:
            url: The HTTP/HTTPS endpoint to execute calculations for.
            timeout_seconds: Request timeout in seconds (default: 10).
            expect_json: Whether JSON response is expected from the endpoint.

        Returns:
            dict: Workflow result including normalized response, rule checks,
            and an overall verdict.
        """
        try:
            return execute_calculations(
                url=url,
                timeout_seconds=timeout_seconds,
                expect_json=expect_json,
            )
        except Exception as e:
            return tool_error_response(e, context="execute_calculations")
