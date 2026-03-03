# MCP Server - Hello World

A production-ready template for building Model Context Protocol (MCP) servers with FastMCP and FastAPI.

It supports a balanced workflow:

- Provider-agnostic local development for generic MCP use cases.
- Databricks-ready deployment and user-authenticated tool execution.

## Quick Start

Prerequisites:

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

Install and run:

```bash
uv sync
./scripts/dev/start_server.sh
```

Or run directly:

```bash
uv run custom-mcp-server --port 8000
```

Default local endpoint: `http://localhost:8000/mcp`

## Documentation Map

Canonical docs are split by ownership:

- [Architecture](./docs/architecture.md)
- [Development](./docs/development.md)
- [Testing](./docs/testing.md)
- [Deployment](./docs/deployment.md)
- [Reference (tools, auth, config)](./docs/reference.md)

AI-assistant-specific constraints are in [Claude.md](./Claude.md).

## Common Commands

```bash
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/ -v
uv run ruff format .
uv run ruff check .
```

## Resources

- [Databricks MCP Documentation](https://docs.databricks.com/aws/en/generative-ai/mcp/custom-mcp)
- [Databricks Apps Deployment](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy#deploy-the-app)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [FastAPI Documentation](https://fastapi.tiangolo.com)


