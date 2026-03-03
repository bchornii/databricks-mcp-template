"""Shared pytest fixtures for both unit and integration tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# --------------------------------------------------------------------------- #
# Mock Databricks objects
# --------------------------------------------------------------------------- #


def _make_mock_user():
    """Return a mock object that looks like a Databricks ``User``."""
    user = MagicMock()
    user.id = "12345"
    user.display_name = "Test User"
    user.user_name = "test.user@example.com"
    user.active = True
    return user


def _make_mock_cluster(cluster_id="abc-123", name="test-cluster", state="RUNNING"):
    """Return a mock object that looks like a Databricks ``ClusterDetails``."""
    cluster = MagicMock()
    cluster.cluster_id = cluster_id
    cluster.cluster_name = name
    cluster.state = MagicMock()
    cluster.state.value = state
    cluster.node_type_id = "Standard_DS3_v2"
    cluster.num_workers = 2
    cluster.spark_version = "14.3.x-scala2.12"
    return cluster


def _make_mock_workspace_object(path="/test/notebook", obj_type="NOTEBOOK", lang="PYTHON"):
    """Return a mock object that looks like a Databricks ``ObjectInfo``."""
    obj = MagicMock()
    obj.path = path
    obj.object_type = MagicMock()
    obj.object_type.value = obj_type
    obj.language = MagicMock()
    obj.language.value = lang
    return obj


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def mock_workspace_client():
    """
    A ``WorkspaceClient`` mock pre-configured with sensible defaults.

    The mock supports:
    - ``current_user.me()`` → mock user
    - ``workspace.list(path)`` → list of mock workspace objects
    - ``clusters.list()`` → list of mock clusters
    - ``clusters.get(id)`` → single mock cluster
    - ``config.host`` → workspace URL string

    Override any behaviour in your test by further configuring the mock.
    """
    client = MagicMock()

    # current_user.me()
    client.current_user.me.return_value = _make_mock_user()

    # workspace.list()
    client.workspace.list.return_value = [
        _make_mock_workspace_object("/test/notebook1", "NOTEBOOK", "PYTHON"),
        _make_mock_workspace_object("/test/folder", "DIRECTORY", None),
    ]

    # clusters
    mock_cluster = _make_mock_cluster()
    client.clusters.list.return_value = [mock_cluster]
    client.clusters.get.return_value = mock_cluster

    # config
    client.config.host = "https://test-workspace.cloud.databricks.com"

    return client


@pytest.fixture
def mock_user_client(mock_workspace_client):
    """Alias — same shape, but semantically represents a user-authenticated client."""
    return mock_workspace_client


@pytest.fixture
def patch_app_auth(mock_workspace_client):
    """Patch ``server.auth.get_workspace_client`` to return the mock."""
    with patch(
        "server.auth.get_workspace_client", return_value=mock_workspace_client
    ) as m:
        yield m


@pytest.fixture
def patch_user_auth(mock_user_client):
    """Patch ``server.auth.get_user_authenticated_workspace_client`` to return the mock."""
    with patch(
        "server.auth.get_user_authenticated_workspace_client",
        return_value=mock_user_client,
    ) as m:
        yield m
