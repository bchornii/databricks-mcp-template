# Architecture Blueprint

This document is the canonical architecture blueprint for this repository.
It describes how the current implementation is structured, how boundaries are
enforced, and how to extend the system without introducing architectural drift.

Generated and refreshed: 2026-03-03

## 1) Scope and Intent

- Project type: Python MCP server template (`FastMCP` + `FastAPI`).
- Primary pattern: Layered architecture with thin tool adapters.
- Runtime target: local development and Databricks Apps deployment.
- Canonical layering: `tools -> application (optional) -> infrastructure -> auth/config`.

## 2) Project Structure

```text
mcp-server-hello-world/
├── server/                        # Core MCP server code
│   ├── app.py                     # Composition root — FastAPI + FastMCP wiring
│   ├── main.py                    # Entry point (uvicorn runner, logging init)
│   ├── config.py                  # Centralized settings (Pydantic BaseSettings)
│   ├── logging_config.py          # Structured logging (JSON prod, readable dev)
│   ├── auth.py                    # Databricks auth client factories
│   ├── errors.py                  # Standardized error-response helper
│   ├── utils.py                   # Backwards-compat shim → re-exports from auth.py
│   ├── application/               # Workflow orchestration layer
│   │   └── calculations_workflow.py
│   ├── infrastructure/            # External integrations (Databricks SDK, HTTP, SQL)
│   │   ├── workspace.py
│   │   ├── sql.py
│   │   └── http.py
│   └── tools/                     # Thin MCP tool adapters (one per domain)
│       ├── __init__.py            # register_all_tools()
│       ├── system.py              # health
│       ├── calculations.py        # fetch_api_status, execute_calculations
│       ├── user.py                # get_current_user
│       ├── workspace.py           # list_workspace_files, get_cluster_info, get_workspace_info
│       └── sql.py                 # run_sql_query
├── scripts/
│   └── dev/                       # Local and remote testing utilities
├── tests/                         # Unit and integration test suite
├── docs/                          # Canonical engineering references
├── app.yaml                       # Databricks Apps deployment config
├── pyproject.toml                 # Dependencies and build config
└── README.md
```

## 3) Architecture Overview

### 3.1 Layered Flow (Runtime)

```text
┌───────────────────────────────────────────────┐
│ MCP Client / AI Agent                         │
└───────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ combined_app (FastAPI)                        │
└───────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ capture_headers middleware                    │
└───────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ FastMCP HTTP app                              │
└───────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ Tool Adapter (server/tools/*)                 │
└───────────────────────────────────────────────┘
                │                       │
                ▼                       ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ Application Workflow         │  │ Infrastructure               │
│ (server/application/*)       │  │ (server/infrastructure/*)    │
└──────────────────────────────┘  └──────────────────────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
┌───────────────────────────────────────────────┐
│ External providers (Databricks APIs / HTTP /  │
│ SQL)                                          │
└───────────────────────────────────────────────┘
```

### 3.2 Component Map

Component groups and relationships:

- Composition/runtime layer
    - `server/app.py` creates the FastMCP/FastAPI runtime and registers tool modules.
    - `server/config.py` provides settings used across runtime/auth.
    - `server/auth.py` provides app-level and user-level client factories.
    - `server/errors.py` provides standardized tool error responses.

- Tool adapter layer
    - `server/tools/system.py`
    - `server/tools/calculations.py`
    - `server/tools/user.py`
    - `server/tools/workspace.py`
    - `server/tools/sql.py`
    - Role: expose MCP contracts, choose auth client, delegate execution, normalize errors.

- Application workflow layer
    - `server/application/calculations_workflow.py`
    - Role: orchestrate steps and rule evaluation when simple adapter-to-infra delegation is not enough.

- Infrastructure layer
    - `server/infrastructure/http.py`
    - `server/infrastructure/workspace.py`
    - `server/infrastructure/sql.py`
    - Role: execute external I/O and provider-specific logic.

Cross-cutting dependencies used by adapters:

- auth + config: `server/auth.py` -> `server/config.py`
- standardized tool error shaping: `server/errors.py`

Dependency index (by adapter):

- `tools/system.py`
    - no workflow
    - no infrastructure dependency

- `tools/calculations.py`
    - `application/calculations_workflow.py`
    - `infrastructure/http.py`
    - `server/errors.py`

- `tools/user.py`
    - `server/auth.py`
    - `server/errors.py`

- `tools/workspace.py`
    - `infrastructure/workspace.py`
    - `server/auth.py`
    - `server/errors.py`

- `tools/sql.py`
    - `infrastructure/sql.py`
    - `server/auth.py`
    - `server/errors.py`

## 4) Layer Responsibilities and Contracts

| Layer | Responsibilities | Allowed Dependencies | Must Not Do |
|---|---|---|---|
| Tool Adapter (`server/tools/*`) | MCP tool contract, argument shaping, auth client selection, error normalization | `server.auth`, `server.errors`, `server.application`, `server.infrastructure` | Complex orchestration, hidden retries/business rules, direct auth internals in infra |
| Application Workflow (`server/application/*`) | Multi-step orchestration, mapping, rule evaluation, response shaping | `server.infrastructure`, pure Python helpers | MCP registration, transport wiring, request-context handling |
| Infrastructure (`server/infrastructure/*`) | External I/O and provider integration details | External SDK clients passed in by caller | Importing auth factories, request-header access, tool error formatting |
| Auth/Config (`server/auth.py`, `server/config.py`) | Auth client creation, request token extraction, settings resolution | Databricks SDK, Pydantic settings | Domain orchestration and tool response shaping |

### What each layer does in practice

#### Tool Adapter (`server/tools/*`)

- Purpose: expose a stable MCP tool API to clients.
- Typical work:
    - read/validate tool arguments,
    - choose the correct auth client (`get_workspace_client` vs `get_user_authenticated_workspace_client`),
    - call workflow/infrastructure,
    - convert exceptions to `tool_error_response`.
- Good examples: `tools/sql.py`, `tools/user.py`, `tools/workspace.py`.
- Keep out of this layer: loops across multiple backend calls, business policy checks, provider-specific SDK details.

#### Application Workflow (`server/application/*`)

- Purpose: coordinate steps and apply domain rules.
- Typical work:
    - combine multiple integration calls,
    - normalize/reshape data for tool responses,
    - evaluate rules and produce verdict-style outputs.
- Good example: `application/calculations_workflow.py`.
- Keep out of this layer: `@mcp_server.tool` decorators, request header handling, direct transport concerns.

#### Infrastructure (`server/infrastructure/*`)

- Purpose: perform external I/O and isolate provider details.
- Typical work:
    - call Databricks SDK methods,
    - execute SQL statements,
    - perform HTTP requests,
    - return raw/minimally-shaped integration results.
- Good examples: `infrastructure/sql.py`, `infrastructure/workspace.py`, `infrastructure/http.py`.
- Keep out of this layer: auth factory imports, context-var/header logic, tool-level error payload formatting.

#### Auth/Config (`server/auth.py`, `server/config.py`)

- Purpose: provide environment-aware auth clients and centralized settings.
- Typical work:
    - resolve deployed vs local mode,
    - read forwarded user token from request context,
    - construct app-level or user-level `WorkspaceClient`.
- Keep out of this layer: feature orchestration and tool response shaping.

### Quick decision guide: “where should this code go?”

- “I need to parse params and return MCP-friendly errors” → `server/tools/*`.
- “I need to combine two service calls and apply a rule” → `server/application/*`.
- “I need to call Databricks/HTTP/SQL” → `server/infrastructure/*`.
- “I need credentials/token/settings resolution” → `server/auth.py` or `server/config.py`.

### Ownership Boundaries

- Tool adapters are the boundary that owns `tool_error_response` payload shape.
- Application workflows own orchestration and domain rules.
- Infrastructure functions receive dependencies explicitly (`client`, URLs, query text).
- Middleware in `server/app.py` is the only request-header capture source for user auth context.

## 5) Dependency Rules and Violation Checks

### Rules

1. `server/infrastructure/*` must not import from `server.auth`.
2. `server/tools/*` should not contain integration-specific business logic.
3. `server/application/*` should not depend on MCP decorators or transport APIs.
4. `/mcp` path must remain unchanged as the protocol endpoint.
5. `server/app.py` header-capture middleware must remain intact.

### Practical Checks for Reviews

- If a tool function is longer than typical adapter glue, move logic into workflow/infra.
- If an infrastructure function touches request headers or env auth context, move that to adapters/auth.
- If an application module imports `fastapi`/`fastmcp`, layering is likely violated.

## 6) Request and Tool Execution Sequences

### 6.1 User-authenticated sequence (`get_current_user`, `run_sql_query`)

```text
┌──────────────┬──────────────────────┬──────────────────────┬──────────────────────────┬──────────────────────┐
│ Client       │ combined_app + MW    │ Tool Adapter         │ Auth Helper              │ Infrastructure + API │
├──────────────┼──────────────────────┼──────────────────────┼──────────────────────────┼──────────────────────┤
│ POST /mcp tool call ───────────────>│                      │                          │                      │
│              │ set header_store     │                      │                          │                      │
│              │─────────────────────>│ get_user_client()    │                          │                      │
│              │                      │─────────────────────>│ read configured          │                      │
│              │                      │                      │ token header             │                      │
│              │                      │<─────────────────────│ WorkspaceClient(...)     │                      │
│              │                      │ call integration     │                          │                      │
│              │                      │────────────────────────────────────────────────>│ SDK request          │
│              │                      │<────────────────────────────────────────────────│ structured result    │
│              │                      │ normalize response / tool_error_response        │                      │
│<────────────────────────────────────│ tool response        │                          │                      │
└──────────────┴──────────────────────┴──────────────────────┴──────────────────────────┴──────────────────────┘
```

### 6.2 App-authenticated sequence (`list_workspace_files`, `get_cluster_info`, `get_workspace_info`)

- Tool adapter chooses `get_workspace_client()`.
- Infrastructure executes SDK call with injected client.
- Tool adapter returns normalized dict.

## 7) Data Architecture

### 7.1 Data Shape Strategy

- Tool contract outputs are structured payloads (`dict` / model-like dict), not ad-hoc strings.
- Infrastructure returns raw or minimally shaped provider data.
- Application workflow performs normalization and verdict/rule mapping where applicable.

### 7.2 Transformation Boundaries

- Input validation and defaulting: tool adapters.
- Domain-level reshaping/rule evaluation: application workflows.
- Provider object-to-dict extraction: infrastructure.

### 7.3 Validation and Error Shape

- Adapter-level failures are converted to a consistent error payload via `tool_error_response`.
- Provider errors remain contextualized but should not expose secrets or raw token values.

## 8) Cross-Cutting Concerns

### Authentication and Authorization

- App context: `get_workspace_client()`.
- User context: `get_user_authenticated_workspace_client()` with request token header (default `x-forwarded-access-token`).
- Deployed mode detection is settings-based (`DATABRICKS_APP_NAME`).

### Error Handling and Resilience

- Centralized adapter formatting through `tool_error_response`.
- Integration-specific failures are surfaced as deterministic dict responses where possible (for example SQL execution status payloads).

### Logging and Observability

- `server/logging_config.py` controls environment-appropriate formatting.
- Structured logs should prioritize operation context while avoiding sensitive data.

### Configuration Management

- `server/config.py` is the single settings entry point.
- Environment overrides use `BaseSettings` semantics.
- CLI `--port` can override `SERVER_PORT`.

## 9) Testing Architecture

Test strategy mirrors layering:

- Unit tests (`tests/unit/`): mock workflows/infrastructure boundaries and validate deterministic behavior.
- Integration tests (`tests/integration/`): run server end-to-end and verify tool contracts.
- Manual smoke checks: local script and remote OAuth script in `scripts/dev/`.

Standard commands:

```bash
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/ -v
```

## 10) Deployment Architecture

### Topology

- App configuration: `app.yaml`.
- Deployed endpoint pattern: `https://<workspace>/serving-endpoints/<app-name>/mcp`.
- Databricks Apps proxy forwards user token header consumed by middleware/auth.

### Runtime Modes

- Local mode: uses local developer auth defaults.
- Deployed mode: uses app identity for app-level tools and forwarded token for user-level tools.

## 11) Technology-Specific Patterns (Python)

- Module-oriented layering via package directories.
- Clear function-based adapters/workflows/services instead of deep inheritance.
- Explicit dependency injection for external clients.
- Sync-first implementation style with straightforward call flow.

## 12) Extension Blueprint for New Development

Use this exact sequence when adding a new tool domain.

### 12.1 Feature Addition Workflow

1. Add external integration in `server/infrastructure/<domain>.py`.
2. Add orchestration logic in `server/application/<workflow>.py` when shaping/rules are needed.
3. Add MCP adapter in `server/tools/<domain>.py` with type hints/docstrings.
4. Register adapter in `server/tools/__init__.py`.
5. Add focused tests under `tests/unit/`.

### 12.2 Implementation Template

```text
server/infrastructure/<domain>.py
    - def <action>(client, ...)->dict:  # external I/O only

server/application/<domain>_workflow.py (optional)
    - def <use_case>(...)->dict:  # orchestration + mapping + rule checks

server/tools/<domain>.py
    - def register(mcp_server)->None:
            @mcp_server.tool
            def <tool_name>(...)->dict:
                # parse args, select auth client, delegate, handle errors
```

### 12.3 Common Pitfalls to Avoid

- Putting provider SDK calls directly in tool adapters.
- Importing auth helpers from infrastructure modules.
- Returning unstructured plain strings from tools.
- Catching exceptions in lower layers and hiding actionable context.

## 13) Architectural Decisions (Current State)

### Decision A: Keep tool adapters thin

- Context: MCP contracts are public and should remain stable.
- Decision: adapters only shape inputs, choose auth, delegate, and normalize errors.
- Consequence: testability and maintainability improve; behavior is predictable.

### Decision B: Inject clients into infrastructure

- Context: integrations must be testable without runtime global state.
- Decision: pass `client` explicitly to infrastructure functions.
- Consequence: unit tests are simpler and lower layers remain decoupled from auth mechanics.

### Decision C: Request-scoped header capture in middleware

- Context: user-authenticated Databricks operations require forwarded token access.
- Decision: capture headers once in middleware and read via context var in auth helper.
- Consequence: centralized token handling; preserves separation from tool/infrastructure logic.

## 14) Architecture Governance

### Non-Negotiable Rules

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

### Review Checklist for PRs

- Layer placement is correct for all new logic.
- Auth client selection matches least-privilege intent.
- Tool response contract remains backward compatible.
- Unit tests cover new workflow/infrastructure behavior.
- No changes break `/mcp` or request-header middleware behavior.

## 15) Key Files

- `server/app.py`: composition root, middleware, FastMCP/FastAPI integration.
- `server/config.py`: settings and environment overrides.
- `server/auth.py`: auth factories and request header context usage.
- `server/errors.py`: canonical tool error formatter.
- `server/logging_config.py`: local/dev and production logging formatters.
- `server/tools/__init__.py`: tool registration boundary.

## 16) Maintenance Guidance

- Refresh this blueprint when adding new tool domains, changing auth behavior, or introducing new runtime dependencies.
- Keep diagrams synchronized with actual module dependencies.
- Prefer additive updates to tool contracts and document any contract change in `README.md` and `docs/reference.md`.
