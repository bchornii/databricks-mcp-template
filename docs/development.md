# Development

This document is the canonical reference for local setup and day-to-day development.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

### Option 1: Using uv (recommended)

```bash
uv sync
```

### Option 2: Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Editable install (optional, useful when iterating on package metadata/entrypoints):

```bash
pip install -e .
```

### Optional Databricks Dependencies

Install when you need Databricks-backed tools:

```bash
uv sync --extra databricks
# or
pip install -e ".[databricks]"
```

## Run the Server

Quick start script:

```bash
./scripts/dev/start_server.sh
```

Alternative commands:

```bash
uv run custom-mcp-server
uv run custom-mcp-server --port 8080
custom-mcp-server --port 3000
```

Default endpoint: `http://localhost:8000/mcp`

### Run Modes

- **Scripted local dev**: `./scripts/dev/start_server.sh` (recommended for repeatable startup).
- **Direct uv command**: `uv run custom-mcp-server` (simple interactive loop).
- **Installed entrypoint**: `custom-mcp-server --port <port>` after editable install.

### Verify Server is Reachable

- MCP endpoint should respond at `http://localhost:8000/mcp`.
- If you changed port, use `http://localhost:<port>/mcp`.

For complete test flows, see [Testing](./testing.md).

## Typical Task: Add a New Tool

Use the layered pattern: adapter (`tools`) → workflow (`application`, optional) → integration (`infrastructure`).

### 1) Add integration logic

Create `server/infrastructure/<domain>.py`:

```python
def do_something(client, param: str) -> dict:
    """External I/O logic only."""
    result = client.some_api.call(param)
    return {"data": result}
```

### 2) Add workflow orchestration (recommended)

Create `server/application/<workflow>.py`:

```python
from server.infrastructure.<domain> import do_something


def run_workflow(client, param: str) -> dict:
    raw = do_something(client, param)
    mapped = {"value": raw["data"]}
    return {"status": "ok", "result": mapped}
```

### 3) Add MCP tool adapter

Create `server/tools/<domain>.py`:

```python
from server.auth import get_workspace_client
from server.application.<workflow> import run_workflow
from server.errors import tool_error_response


def register(mcp_server) -> None:
    @mcp_server.tool
    def your_tool_name(param: str) -> dict:
        """Clear, task-oriented docstring describing when to call this tool."""
        try:
            client = get_workspace_client()
            return run_workflow(client, param)
        except Exception as e:
            return tool_error_response(e, context="your_tool_name")
```

### 4) Register the tool domain

Update `server/tools/__init__.py`:

```python
from server.tools import <domain>


def register_all_tools(mcp_server) -> None:
    # existing registrations...
    <domain>.register(mcp_server)
```

### 5) Add tests and validate

- Add unit tests under `tests/unit/`.
- Run `uv run pytest tests/unit/ -v`.
- Restart server and verify tool appears in `list_tools()`.

## MCP Tool Quality Standards (Team Reference)

Use this section as a quality bar before merging a new or changed tool.

### 1) Tool naming and intent

- Use action-oriented names: `get_*`, `list_*`, `run_*`, `fetch_*`, `execute_*`.
- Keep tool name specific to the user intent, not implementation details.
- Prefer one clear job per tool; split tools when responsibilities become mixed.

### 2) Docstring requirements (critical)

MCP clients and AI assistants rely on docstrings to decide when to call tools.
Every tool docstring should include:

- **What** the tool does in one sentence.
- **When** to use it.
- **Args** with parameter meaning, expected format, and constraints.
- **Returns** with stable response shape.
- **Failure behavior** at a high level (for example: standardized error response).

Recommended template:

```python
@mcp_server.tool
def run_sql_query(statement: str, warehouse_id: str | None = None) -> dict:
    """
    Execute a SQL query against a Databricks SQL warehouse.

    Use when you need tabular results from Databricks SQL.

    Args:
        statement: SQL statement to execute.
        warehouse_id: Optional warehouse override. If omitted, default resolution is used.

    Returns:
        A structured response containing query metadata and rows.

    Notes:
        Errors are normalized via tool_error_response.
    """
```

### 3) Code comments guidance

Prefer readable code first, then add comments where intent would otherwise be ambiguous.

Good places for comments:

- Why a non-obvious auth client is chosen.
- Why a mapping/transformation exists (business rule context).
- Why a fallback/default behavior is required.

Avoid comments that restate obvious code behavior.

Example:

```python
def register(mcp_server) -> None:
    @mcp_server.tool
    def get_current_user() -> dict:
        """Return profile details for the authenticated user."""
        try:
            # User-authenticated client is required because this tool acts on behalf of caller.
            client = get_user_authenticated_workspace_client()
            return get_current_user_profile(client)
        except Exception as e:
            return tool_error_response(e, context="get_current_user")
```

### 4) Tool adapter boundaries

Tool adapters should:

- Parse/validate incoming parameters via type hints.
- Select correct auth client.
- Delegate domain logic to workflow/infrastructure modules.
- Normalize failures with `tool_error_response`.

Tool adapters should not:

- Perform heavy business orchestration.
- Contain complex data-mapping pipelines.
- Implement direct external I/O beyond very small glue behavior.

### 5) Response contract stability

- Always return structured data (`dict`/model), not ad-hoc strings.
- Keep top-level keys stable once published (for example `success`, `data`, `error`).
- Add new fields in backward-compatible ways (do not silently rename/remove keys).
- Keep error shape standardized through `tool_error_response`.

### 6) Validation checklist for tool changes

Before opening a PR:

1. Tool name is action-oriented and unambiguous.
2. Tool docstring explains when to use it and what it returns.
3. Type hints are complete for all parameters and return type.
4. Auth client choice is correct for the operation.
5. Tool adapter delegates orchestration/I-O to lower layers.
6. Error handling uses `tool_error_response`.
7. Unit tests cover success path and at least one failure path.
8. `uv run pytest tests/unit/ -v` passes.

## Typical Task: Choose the Right Auth Client

Use auth helpers from `server/auth.py`:

- `get_workspace_client()` for app-level operations (workspace metadata, admin/service operations).
- `get_user_authenticated_workspace_client()` for user-context operations (actions executed as the calling user).

Example:

```python
from server.auth import get_workspace_client, get_user_authenticated_workspace_client

app_client = get_workspace_client()
user_client = get_user_authenticated_workspace_client()
```

Auth behavior differs by environment:

- **Local**: both methods use local developer credentials.
- **Deployed Databricks App**: app method uses service principal, user method uses forwarded user token header.

See [Reference](./reference.md) for canonical auth details.

### Auth decision quick guide

- Use `get_workspace_client()` when operation is app-scoped or service-principal-safe.
- Use `get_user_authenticated_workspace_client()` when operation must reflect caller identity/permissions.
- If uncertain, default to least-privilege behavior and document rationale in tool docstring.

## Typical Task: Add a Custom FastAPI Endpoint

Add route handlers to `server/app.py` (outside MCP tools), for example:

```python
@app.get("/custom-endpoint")
def custom_endpoint():
    return {"message": "Hello from custom endpoint"}
```

Do not modify middleware that sets per-request header context for user auth.

## Typical Task: Rename the Project

1. Update `name` in `pyproject.toml`.
2. Update server name default/environment config in `server/config.py`.
3. Update `[project.scripts]` command name in `pyproject.toml`.
4. Update references in docs.

## Formatting and Linting

```bash
uv run ruff format .
uv run ruff check .
```

Recommended pre-PR commands:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest tests/unit/ -v
```

## Troubleshooting

### Port already in use

- Run with another port: `uv run custom-mcp-server --port 8080`.
- Or set `SERVER_PORT` and start normally.

### Import or dependency errors

```bash
uv sync
# or
pip install -r requirements.txt
```

### Databricks-backed tools unavailable

Install optional dependencies:

```bash
uv sync --extra databricks
# or
pip install -e ".[databricks]"
```

### Tool appears missing in MCP client

- Confirm tool module is imported and registered in `server/tools/__init__.py`.
- Restart the server after registration changes.
- Verify no import error occurs during startup.

### User-authenticated tool fails when deployed

- Verify user token header configuration (`USER_TOKEN_HEADER`).
- Confirm app requests required user scopes.
- Check middleware header propagation remains unchanged in `server/app.py`.

## Related Docs

- [Project Overview](../README.md)
- [Architecture](./architecture.md)
- [Testing](./testing.md)
- [Deployment](./deployment.md)
- [Reference](./reference.md)
