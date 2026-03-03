"""System / diagnostic tools."""

from server.auth import is_databricks_sdk_available


def register(mcp_server) -> None:
    @mcp_server.tool
    def health() -> dict:
        """
        Check the health of the MCP server.

        This is a simple diagnostic tool that confirms the server is running
        properly.  It is useful for:
        - Monitoring and health checks
        - Testing the MCP connection
        - Verifying the server is responsive

        Returns:
            dict: A dictionary containing:
                - status (str): The health status ("healthy" if operational)
                - message (str): A human-readable status message
                - databricks_sdk_available (bool): Whether the SDK is installed

        Example response::

            {
                "status": "healthy",
                "message": "Custom MCP Server is healthy.",
                "databricks_sdk_available": true
            }
        """
        return {
            "status": "healthy",
            "message": "Custom MCP Server is healthy.",
            "databricks_sdk_available": is_databricks_sdk_available(),
        }
