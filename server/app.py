"""
FastAPI application configuration for the MCP server.

This module is the **composition root** — it wires together configuration,
authentication, tool registration, and HTTP transport.  Business logic lives
in ``server.infrastructure``; tool adapters live in ``server.tools``.

Responsibilities:
1. Create and configure the FastMCP server instance
2. Register all MCP tools (via ``server.tools.register_all_tools``)
3. Set up middleware for request-header propagation (auth)
4. Combine MCP routes with standard FastAPI routes
5. Optionally serve a static landing page
"""

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastmcp import FastMCP

from server.auth import header_store
from server.config import get_settings
from server.tools import register_all_tools

# --------------------------------------------------------------------------- #
# Settings (single source of truth)
# --------------------------------------------------------------------------- #

settings = get_settings()

# --------------------------------------------------------------------------- #
# MCP server
# --------------------------------------------------------------------------- #

mcp_server = FastMCP(name=settings.server_name)

# Register all tool domains (system, http, user, workspace, sql)
register_all_tools(mcp_server)

# Convert the MCP server to a streamable HTTP application
mcp_app = mcp_server.http_app()

# --------------------------------------------------------------------------- #
# FastAPI application
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="Custom MCP Server",
    description="Custom MCP Server for the app",
    version="0.1.0",
    lifespan=mcp_app.lifespan,
)


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the static landing page or a JSON health response."""
    index = settings.static_dir / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Custom Open API Spec MCP Server is running", "status": "healthy"}


# --------------------------------------------------------------------------- #
# Combined application (what uvicorn serves)
# --------------------------------------------------------------------------- #

combined_app = FastAPI(
    title="Combined MCP App",
    routes=[
        *mcp_app.routes,  # MCP protocol routes (tools, resources, etc.)
        *app.routes,       # Custom API routes (landing page, etc.)
    ],
    lifespan=mcp_app.lifespan,
)


@combined_app.middleware("http")
async def capture_headers(request: Request, call_next):
    """Store request headers so ``server.auth`` can read the user token."""
    header_store.set(dict(request.headers))
    return await call_next(request)
