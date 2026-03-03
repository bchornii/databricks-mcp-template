# Development Scripts

Scripts for testing and developing the MCP server.

## Quick Reference

| Script | Purpose | Environment |
|--------|---------|-------------|
| `query_remote.sh` | Test deployed app (interactive OAuth) | Databricks App |
| `start_server.sh` | Start local dev server | `localhost:8000` |
| `generate_oauth_token.py` | Generate OAuth tokens | Any |

## Script Usage

### Local Testing
```bash
./scripts/dev/start_server.sh  # Terminal 1
```

```python
from databricks_mcp import DatabricksMCPClient
mcp_client = DatabricksMCPClient(
    server_url="http://localhost:8000"
)
# List available MCP tools
print(mcp_client.list_tools())
```

### Remote Testing
```bash
# Interactive (walks you through OAuth)
./scripts/dev/query_remote.sh
```

Tests all discovered tools with user-level OAuth authentication.

## Development Workflow

1. Add tool adapter in `server/tools/<domain>.py` and register it in `server/tools/__init__.py`.
2. Test locally (above) or run integration tests.
3. Deploy to Databricks Apps.
4. Validate deployed behavior with `./scripts/dev/query_remote.sh`.

## Canonical Documentation

This file stays script-focused. For full docs, use:

- `docs/development.md`
- `docs/testing.md`
- `docs/deployment.md`
- `docs/reference.md`

