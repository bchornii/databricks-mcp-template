"""Manual MCP debugging script.

This script is intended for ad-hoc local debugging:
- Connect to an MCP server
- List all tools
- Execute a configurable subset of tools

Examples:
    python tests/manual_test.py
    python tests/manual_test.py --server-url http://localhost:8080/mcp
    python tests/manual_test.py --include-dbx
    python tests/manual_test.py --tool health --tool execute_calculations
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from databricks_mcp import DatabricksMCPClient

DEFAULT_SERVER_URL = "http://localhost:8080/mcp"

TOOL_ARGS: dict[str, dict[str, Any]] = {
    "health": {},
    "execute_calculations": {
        "url": "https://httpbin.org/get",
        "timeout_seconds": 10,
        "expect_json": True,
    },
    "list_workspace_files": {"path": "/"},
    "get_cluster_info": {},
    "get_workspace_info": {},
    "get_current_user": {},
    "run_sql_query": {"query": "SELECT 1"},
}

DATABRICKS_TOOLS = {
    "list_workspace_files",
    "get_cluster_info",
    "get_workspace_info",
    "get_current_user",
    "run_sql_query",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual MCP server debugging tool")
    parser.add_argument(
        "--server-url",
        default=DEFAULT_SERVER_URL,
        help=f"MCP server URL (default: {DEFAULT_SERVER_URL})",
    )
    parser.add_argument(
        "--tool",
        action="append",
        help="Tool name to run. Repeat to run multiple tools. If omitted, runs defaults.",
    )
    parser.add_argument(
        "--include-dbx",
        action="store_true",
        help="Include Databricks-backed tools in default run.",
    )
    return parser.parse_args()


def _pretty_print(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str))


def main() -> int:
    args = _parse_args()
    client = DatabricksMCPClient(server_url=args.server_url)

    print(f"Connecting to: {args.server_url}")
    tools = client.list_tools()
    tool_names = [tool.name for tool in tools]

    print("\nAvailable tools:")
    for name in tool_names:
        print(f"- {name}")

    if args.tool:
        selected = args.tool
    else:
        selected = ["health", "execute_calculations"]
        if args.include_dbx:
            selected.extend(sorted(DATABRICKS_TOOLS))

    print("\nExecuting tools:")
    for tool_name in selected:
        if tool_name not in tool_names:
            print(f"\n[{tool_name}] skipped: not registered")
            continue

        if tool_name in DATABRICKS_TOOLS and not args.include_dbx and not args.tool:
            print(f"\n[{tool_name}] skipped: Databricks-backed tool (use --include-dbx)")
            continue

        payload = TOOL_ARGS.get(tool_name, {})
        print(f"\n[{tool_name}] args: {payload}")
        try:
            result = client.call_tool(tool_name, payload)
            print(f"[{tool_name}] result:")
            _pretty_print(result)
        except Exception as exc:
            print(f"[{tool_name}] error: {type(exc).__name__}: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
