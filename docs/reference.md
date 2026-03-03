# Reference

This document is the canonical reference for tool inventory, auth behavior, and settings.

## Tool Catalog

- `health`: health check (no auth).
- `fetch_api_status`: HTTP GET status for a URL (no auth).
- `execute_calculations`: example workflow execution.
- `get_current_user`: current user details (user auth).
- `list_workspace_files`: workspace file listing (app auth).
- `get_cluster_info`: cluster details (app auth).
- `get_workspace_info`: workspace metadata (app auth).
- `run_sql_query`: SQL execution (user auth).

Tool modules live in `server/tools/`, and all domains are wired in `server/tools/__init__.py`.

## Authentication Behavior

Primary helpers (in `server/auth.py`):

- `get_workspace_client()`: app-level auth when deployed; local developer auth in local runs.
- `get_user_authenticated_workspace_client()`: end-user auth when deployed (requires configured user token header), local developer auth in local runs.

Deployment behavior:

- `DATABRICKS_APP_NAME` present → deployed mode.
- user token header defaults to `x-forwarded-access-token`.

## Configuration

Settings are defined in `server/config.py` (`BaseSettings`).

| Setting | Env Variable | Default |
|---|---|---|
| Server name | `SERVER_NAME` | `custom-mcp-server` |
| Host | `SERVER_HOST` | `0.0.0.0` |
| Port | `SERVER_PORT` | `8000` |
| Log level | `LOG_LEVEL` | `INFO` |
| Databricks app name | `DATABRICKS_APP_NAME` | *(unset = local dev)* |
| User token header | `USER_TOKEN_HEADER` | `x-forwarded-access-token` |

CLI `--port` overrides `SERVER_PORT`.

## Dependencies

Core:

- `fastmcp`
- `fastapi`
- `uvicorn`
- `pydantic`
- `pydantic-settings`

Optional Databricks support:

- `databricks-sdk`
- `databricks-mcp` (testing/dev use)

Testing:

- `pytest`

## AI-Assistant Constraints Source

AI-assistant-specific repository constraints are maintained in the root `Claude.md` file.
