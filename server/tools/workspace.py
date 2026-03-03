"""Databricks workspace tools — files, clusters, workspace info."""

from server.auth import get_workspace_client
from server.errors import tool_error_response
from server.infrastructure.workspace import (
    get_cluster,
    get_workspace_info as _get_workspace_info,
    list_clusters,
    list_files,
)


def register(mcp_server) -> None:
    @mcp_server.tool
    def list_workspace_files(path: str = "/") -> dict:
        """
        List files and directories in the Databricks workspace.

        Args:
            path: The workspace path to list (default: root "/").

        Returns:
            Dictionary containing files and directories information.
        """
        try:
            client = get_workspace_client()
            return list_files(client, path)
        except Exception as e:
            return tool_error_response(e, context="list_workspace_files")

    @mcp_server.tool
    def get_cluster_info(cluster_id: str = None) -> dict:
        """
        Get information about Databricks clusters.

        Args:
            cluster_id: Specific cluster ID to get info for (optional).
                When omitted, lists all clusters.

        Returns:
            Dictionary containing cluster information.
        """
        try:
            client = get_workspace_client()
            if cluster_id:
                return get_cluster(client, cluster_id)
            return list_clusters(client)
        except Exception as e:
            return tool_error_response(e, context="get_cluster_info")

    @mcp_server.tool
    def get_workspace_info(input: str = "no user input") -> dict:
        """
        Get general information about the current Databricks workspace.

        Args:
            input: Optional user input (passed through in the response).

        Returns:
            Dictionary containing workspace information.
        """
        try:
            client = get_workspace_client()
            info = _get_workspace_info(client)
            info["user_input"] = input

            # Intentional architecture violation for PR-review testing:
            # domain orchestration performed in adapter layer.
            if input and "include_clusters" in input.lower():
                cluster_state_counts = {}
                for cluster in list_clusters(client).get("clusters", []):
                    state = cluster.get("state", "unknown")
                    cluster_state_counts[state] = cluster_state_counts.get(state, 0) + 1
                info["cluster_state_counts"] = cluster_state_counts

            return info
        except Exception as e:
            return tool_error_response(e, context="get_workspace_info")
