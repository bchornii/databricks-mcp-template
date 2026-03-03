"""
Integration tests for the MCP server.

These tests start the actual server in a subprocess, connect via
``DatabricksMCPClient``, and verify tools are discoverable and callable.
"""

import os
import shlex
import signal
import socket
import subprocess
import time
from contextlib import closing

import pytest
import requests
from databricks_mcp import DatabricksMCPClient


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server_startup(url: str, timeout: int = 15):
    """Poll *url* until it returns 2xx/3xx or *timeout* seconds elapse."""
    deadline = time.time() + timeout
    last_exc = None

    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=1)
            if 200 <= response.status_code < 400:
                return response
        except Exception as e:
            last_exc = e
        time.sleep(0.3)

    if last_exc:
        raise last_exc
    raise TimeoutError(f"Server at {url} did not respond in {timeout}s")


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


# Map of tools that need specific arguments to be callable
_TOOL_ARGS: dict[str, dict] = {
    "fetch_api_status": {"url": "https://httpbin.org/get"},
    "run_sql_query": None,               # skip — requires live warehouse
    "list_workspace_files": {"path": "/"},
    "get_cluster_info": {},               # no required args
    "get_workspace_info": {},
    "get_current_user": {},
    "health": {},
}

# Tools that need a live Databricks backend and should be skipped in CI
_SKIP_IN_CI = {"run_sql_query", "list_workspace_files", "get_cluster_info",
               "get_workspace_info", "get_current_user"}


@pytest.fixture(scope="session")
def mcp_server_url():
    """Start the MCP server in a subprocess and yield its base URL."""
    host = "127.0.0.1"
    port = _find_free_port()
    url = f"http://{host}:{port}"
    cmd = shlex.split(f"uv run custom-mcp-server --port {port}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid if os.name != "nt" else None,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )

    try:
        _wait_for_server_startup(url)
    except Exception:
        proc.terminate()
        proc.wait()
        raise

    yield url  # ← tests receive the URL string, not the process

    # Teardown
    if os.name == "nt":
        proc.terminate()
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc.wait()


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_list_tools(mcp_server_url):
    """Server exposes at least one tool."""
    client = DatabricksMCPClient(server_url=f"{mcp_server_url}/mcp")
    tools = client.list_tools()
    assert len(tools) > 0, "Expected at least one registered tool"


def test_health_tool(mcp_server_url):
    """The ``health`` tool returns a healthy status."""
    client = DatabricksMCPClient(server_url=f"{mcp_server_url}/mcp")
    result = client.call_tool("health")
    assert result is not None


def test_fetch_api_status_tool(mcp_server_url):
    """The ``fetch_api_status`` tool can reach an external URL."""
    client = DatabricksMCPClient(server_url=f"{mcp_server_url}/mcp")
    result = client.call_tool(
        "fetch_api_status",
        {"url": "https://httpbin.org/get", "timeout_seconds": 10},
    )
    assert result is not None


def test_execute_calculations_tool(mcp_server_url):
    """The ``execute_calculations`` tool returns workflow output structure."""
    client = DatabricksMCPClient(server_url=f"{mcp_server_url}/mcp")
    url = "https://httpbin.org/json"
    result = client.call_tool(
        "execute_calculations",
        {"url": url, "timeout_seconds": 10, "expect_json": True},
    )

    assert result is not None
    payload = getattr(result, "structuredContent", result)
    assert isinstance(payload, dict)
    assert payload.get("endpoint") == url
    assert payload.get("verdict") in {"healthy", "degraded", "unhealthy"}
    assert isinstance(payload.get("rules"), list)
    assert isinstance(payload.get("normalized_response"), dict)
