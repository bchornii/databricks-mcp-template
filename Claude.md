# Claude.md - AI Assistant Contract

This file is the AI-assistant contract for this repository.

Operational details are intentionally centralized in `docs/` to avoid duplication drift:

- Architecture: `docs/architecture.md`
- Development: `docs/development.md`
- Testing: `docs/testing.md`
- Deployment: `docs/deployment.md`
- Tools/Auth/Config reference: `docs/reference.md`

## Purpose

This repository is an MCP server template built with FastMCP and FastAPI, designed for local development and Databricks Apps deployment.

## Non-Negotiable Rules

1. Never modify `server/app.py` middleware that populates request header context for user auth.
2. Follow layered design: `tools -> application (optional) -> infrastructure -> auth/config`.
3. Keep `server/tools` thin: argument handling, auth client selection, delegation, standardized error handling.
4. Place orchestration/mapping/rules in `server/application`.
5. Keep external I/O in `server/infrastructure`.
6. Infrastructure modules must not import auth helpers; pass `client` explicitly.
7. Use `tool_error_response` for tool adapter errors.
8. Keep `/mcp` endpoint path unchanged.
9. Type hints and clear docstrings are required for tool functions.
10. Return structured data (`dict`/models), not ad-hoc plain strings.

## Tool Extension Pattern

When adding a tool:

1. Add integration logic in `server/infrastructure/<domain>.py`.
2. Add orchestration logic in `server/application/<workflow>.py` (optional but preferred for shaping/rules).
3. Add MCP adapter in `server/tools/<domain>.py`.
4. Register domain in `server/tools/__init__.py`.
5. Add unit tests under `tests/unit/`.

## Auth Expectations

- App-level operations should use `get_workspace_client()`.
- User-context operations should use `get_user_authenticated_workspace_client()`.
- Deployed mode relies on configured user token header (`USER_TOKEN_HEADER`, default `x-forwarded-access-token`).

For canonical auth details and tool inventory, use `docs/reference.md`.

## Validation Expectation

After modifying workflows/integration/tool adapters, run unit tests:

```bash
uv run pytest tests/unit/ -v
```

Use additional test flows from `docs/testing.md` when needed.
