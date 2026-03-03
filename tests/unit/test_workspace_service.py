"""Unit tests for ``server.infrastructure.workspace``."""

from server.infrastructure.workspace import (
    get_cluster,
    get_current_user,
    get_workspace_info,
    list_clusters,
    list_files,
)


class TestListFiles:
    def test_returns_items(self, mock_workspace_client):
        result = list_files(mock_workspace_client, "/test")

        assert result["path"] == "/test"
        assert len(result["items"]) == 2

    def test_item_structure(self, mock_workspace_client):
        result = list_files(mock_workspace_client, "/test")
        item = result["items"][0]

        assert "name" in item
        assert "full_path" in item
        assert "object_type" in item
        assert "language" in item

    def test_extracts_name_from_path(self, mock_workspace_client):
        result = list_files(mock_workspace_client, "/test")
        assert result["items"][0]["name"] == "notebook1"


class TestGetCluster:
    def test_returns_cluster_details(self, mock_workspace_client):
        result = get_cluster(mock_workspace_client, "abc-123")

        assert result["cluster_id"] == "abc-123"
        assert result["cluster_name"] == "test-cluster"
        assert result["state"] == "RUNNING"
        assert "spark_version" in result


class TestListClusters:
    def test_returns_cluster_list(self, mock_workspace_client):
        result = list_clusters(mock_workspace_client)

        assert "clusters" in result
        assert len(result["clusters"]) == 1
        assert result["clusters"][0]["cluster_id"] == "abc-123"

    def test_cluster_summary_keys(self, mock_workspace_client):
        result = list_clusters(mock_workspace_client)
        cluster = result["clusters"][0]

        assert set(cluster.keys()) == {"cluster_id", "cluster_name", "state"}


class TestGetWorkspaceInfo:
    def test_returns_workspace_metadata(self, mock_workspace_client):
        result = get_workspace_info(mock_workspace_client)

        assert result["workspace_id"] == "12345"
        assert result["workspace_url"] == "https://test-workspace.cloud.databricks.com"
        assert result["user_name"] == "test.user@example.com"
        assert result["active"] is True


class TestGetCurrentUser:
    def test_returns_user_info(self, mock_workspace_client):
        result = get_current_user(mock_workspace_client)

        assert result["display_name"] == "Test User"
        assert result["user_name"] == "test.user@example.com"
        assert result["active"] is True
