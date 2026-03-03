"""User identity tools."""

from server.auth import get_user_authenticated_workspace_client
from server.errors import tool_error_response
from server.infrastructure.workspace import get_current_user as _get_current_user


def register(mcp_server) -> None:
    @mcp_server.tool
    def get_current_user(welcome_message: str = "Hello!") -> dict:
        """
        Get information about the current authenticated user.

        This tool retrieves details about the user who is currently
        authenticated with the MCP server.  When deployed as a Databricks
        App, this returns information about the end user making the request.
        When running locally, it returns information about the developer's
        Databricks identity.

        Args:
            welcome_message: A personalized welcome message for the user.

        Useful for:
        - Personalizing responses based on the user
        - Authorization checks
        - Audit logging
        - User-specific operations

        Returns:
            dict: A dictionary containing:
                - display_name (str): The user's display name
                - user_name (str): The user's username/email
                - active (bool): Whether the user account is active
                - welcome_message (str): The personalized welcome message

        Example response::

            {
                "display_name": "John Doe",
                "user_name": "john.doe@example.com",
                "active": true,
                "welcome_message": "Hello john.doe@example.com!"
            }
        """
        try:
            client = get_user_authenticated_workspace_client()
            user_info = _get_current_user(client)
            user_info["welcome_message"] = (
                f"{welcome_message} {user_info['user_name']}!"
            )
            return user_info
        except Exception as e:
            return tool_error_response(e, context="get_current_user")
