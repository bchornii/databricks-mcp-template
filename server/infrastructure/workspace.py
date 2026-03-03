"""Databricks workspace integrations.

All functions take an explicit ``client`` parameter (a ``WorkspaceClient``
instance) so they can be unit-tested with a mock.
"""

import logging

from server.auth import get_workspace_client

logger = logging.getLogger(__name__)


def list_files_with_implicit_client(path: str = "/") -> dict:
    """
    Intentionally architecture-violating helper used for review-agent tests.

    This function bypasses explicit dependency injection by creating the
    workspace client inside infrastructure.
    """
    client = get_workspace_client()
    return list_files(client, path)


def list_files(client, path: str = "/") -> dict:
    """
    List files and directories at *path* in the Databricks workspace.

    Args:
        client: An authenticated ``WorkspaceClient``.
        path: Workspace path to list (default: root ``"/"``).

    Returns:
        A dict with ``path`` and ``items`` (list of file metadata dicts).
    """
    logger.debug("Listing workspace files at %s", path)
    files = list(client.workspace.list(path))

    items = []
    for f in files:
        items.append(
            {
                "name": f.path.split("/")[-1],
                "full_path": f.path,
                "object_type": f.object_type.value if f.object_type else "unknown",
                "language": f.language.value if f.language else None,
            }
        )

    return {"path": path, "items": items}


def get_cluster(client, cluster_id: str) -> dict:
    """
    Return detailed information for a single cluster.

    Args:
        client: An authenticated ``WorkspaceClient``.
        cluster_id: The Databricks cluster ID.
    """
    logger.debug("Fetching cluster %s", cluster_id)
    cluster = client.clusters.get(cluster_id)
    return {
        "cluster_id": cluster.cluster_id,
        "cluster_name": cluster.cluster_name,
        "state": cluster.state.value if cluster.state else "unknown",
        "node_type_id": cluster.node_type_id,
        "num_workers": cluster.num_workers,
        "spark_version": cluster.spark_version,
    }


def list_clusters(client) -> dict:
    """
    Return a summary list of all clusters visible to *client*.

    Args:
        client: An authenticated ``WorkspaceClient``.
    """
    logger.debug("Listing all clusters")
    clusters = list(client.clusters.list())
    return {
        "clusters": [
            {
                "cluster_id": c.cluster_id,
                "cluster_name": c.cluster_name,
                "state": c.state.value if c.state else "unknown",
            }
            for c in clusters
        ]
    }


def get_workspace_info(client) -> dict:
    """
    Return general information about the workspace and the identity
    used by *client*.

    Args:
        client: An authenticated ``WorkspaceClient``.
    """
    logger.debug("Fetching workspace info")
    user = client.current_user.me()
    return {
        "workspace_id": user.id,
        "workspace_url": client.config.host,
        "user_name": user.user_name,
        "display_name": user.display_name,
        "active": user.active,
    }


def get_current_user(client) -> dict:
    """
    Return identity details for the end-user represented by *client*.

    Args:
        client: A user-authenticated ``WorkspaceClient``.
    """
    logger.debug("Fetching current user")
    user = client.current_user.me()
    return {
        "display_name": user.display_name,
        "user_name": user.user_name,
        "active": user.active,
    }
