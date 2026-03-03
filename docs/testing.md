# Testing

This document is the canonical reference for testing workflows.

## Unit Tests

Fast, mocked tests for integration/workflow modules:

```bash
uv run pytest tests/unit/ -v
```

## Integration Tests

Full-stack tests that start the real server:

```bash
uv run pytest tests/integration/ -v
```

## Run All Tests

```bash
uv run pytest tests/ -v
```

## Local Manual MCP Smoke Test

Start server:

```bash
./scripts/dev/start_server.sh
```

Minimal local client check:

```python
from databricks_mcp import DatabricksMCPClient

mcp_client = DatabricksMCPClient(server_url="http://localhost:8000")
print(mcp_client.list_tools())
```

## Remote Deployed Test (OAuth)

Use interactive script:

```bash
./scripts/dev/query_remote.sh
```

Or pass arguments directly:

```bash
python scripts/dev/query_remote.py \
  --host "https://your-workspace.cloud.databricks.com" \
  --token "eyJ..." \
  --app-url "https://your-workspace.cloud.databricks.com/serving-endpoints/your-app"
```

Remote test flow validates:

- MCP connectivity and tool discovery.
- Health tool behavior.
- User-authenticated tool behavior (for example `get_current_user`).

## Related Docs

- [Development](./development.md)
- [Deployment](./deployment.md)
- [Reference](./reference.md)
