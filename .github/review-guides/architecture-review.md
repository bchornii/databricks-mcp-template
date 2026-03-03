# Architecture Review Guide (for PR agents)

Use this guide to perform architecture-focused pull request reviews for this repository.

Primary reference: `docs/architecture.md`

## Scope

- Review only code changed in the pull request.
- Focus on architectural integrity, dependency direction, and contract safety.
- Do not request unrelated refactors.

## Severity Model

- **High**: Breaks non-negotiable rules or can cause production/runtime failures.
- **Medium**: Architectural drift, maintainability risk, boundary leakage.
- **Low**: Readability/consistency improvements with low risk.

## Required Checks

### 1) Layering and Boundaries

- Enforce layer direction: `tools -> application (optional) -> infrastructure -> auth/config`.
- `server/tools/*` should remain thin adapters:
  - argument handling
  - auth client selection
  - delegation to workflow/infrastructure
  - standardized error handling
- `server/application/*` should contain orchestration/mapping/rules.
- `server/infrastructure/*` should contain external I/O only.

Flag as **High** when:
- business orchestration is added in tool adapters
- transport concerns (MCP/FastAPI) appear in application/infrastructure

### 2) Auth and Dependency Injection

- `server/infrastructure/*` must not import auth helpers.
- Integration clients must be passed explicitly to infrastructure functions.
- User-context operations should use user-authenticated client factories from adapter layer.

Flag as **High** when:
- infrastructure imports `server.auth`
- request-header/token handling appears outside auth/middleware

### 3) Error Handling Contract

- Tool adapter errors should be normalized using `tool_error_response`.
- Avoid ad-hoc string responses from tools; return structured payloads.

Flag as **Medium** when:
- tool errors are returned with inconsistent shape
- exception handling leaks lower-level details to clients

### 4) Public Tool Contract Stability

- Treat tool names, parameters, and response keys as public contracts.
- Prefer additive changes.

Flag as **Medium** when:
- response fields are removed/renamed without compatibility handling
- existing tool semantics are changed without explicit migration notes

### 5) Runtime Invariants

- `/mcp` endpoint path must remain unchanged.
- Header capture middleware in `server/app.py` for user auth context must remain intact.

Flag as **High** when:
- `/mcp` route behavior/path is altered
- middleware-based header propagation is removed or bypassed

### 6) Testing Alignment

- New workflow/infrastructure behavior should have unit tests under `tests/unit/`.
- Integration behavior changes should be reflected in `tests/integration/` when relevant.

Flag as **Medium** when:
- meaningful logic changes lack nearby test updates

## Expected Review Output Format

Return findings as concise bullets grouped by severity:

1. **High**
   - `[path]`: issue, impact, and exact suggested fix
2. **Medium**
   - `[path]`: issue, impact, and exact suggested fix
3. **Low**
   - `[path]`: issue and optional improvement
4. **No issues found** if all checks pass

For each finding include:
- impacted file path
- why it violates this guide
- concrete remediation suggestion

## Non-Goals

- Do not rewrite style-only code unless it blocks architecture intent.
- Do not propose unrelated framework migrations.
- Do not suggest changing repository non-negotiable rules.
