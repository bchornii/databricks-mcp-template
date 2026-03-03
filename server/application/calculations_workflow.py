"""Calculations workflow orchestration use-cases."""

from collections.abc import Callable

from server.infrastructure.http import fetch_url_status


def execute_calculations_workflow(
    url: str,
    timeout_seconds: int = 10,
    expect_json: bool = False,
    fetcher: Callable[[str, int], dict] | None = None,
) -> dict:
    """
    Run an end-to-end API calculation workflow.

    Workflow steps:
    1. Execute HTTP GET via infrastructure integration.
    2. Map and reshape the raw response into a normalized structure.
    3. Evaluate rule checks and compute an overall verdict.

    Args:
        url: Endpoint to execute calculations for.
        timeout_seconds: Request timeout in seconds.
        expect_json: Whether the endpoint is expected to return JSON.
        fetcher: Optional injected fetch function for tests.

    Returns:
        A structured calculation payload for agent consumption.
    """
    fetch_fn = fetcher or fetch_url_status
    raw_response = fetch_fn(url, timeout_seconds)
    normalized = _normalize_response(url, raw_response)
    rules = _evaluate_rules(normalized, expect_json=expect_json)
    verdict = _derive_verdict(rules)

    return {
        "endpoint": url,
        "verdict": verdict,
        "normalized_response": normalized,
        "rules": rules,
        "summary": _build_summary(verdict, rules),
    }


def _normalize_response(url: str, raw: dict) -> dict:
    """Map raw HTTP integration output into a stable shape."""
    status_code = raw.get("status_code")
    payload_type = "none"
    payload = None

    if "json" in raw:
        payload_type = "json"
        payload = raw.get("json")
    elif "body_preview" in raw:
        payload_type = "text"
        payload = raw.get("body_preview")

    return {
        "url": url,
        "ok": bool(raw.get("ok", False)),
        "status_code": status_code,
        "content_type": raw.get("content_type"),
        "payload_type": payload_type,
        "payload": payload,
        "warning": raw.get("warning"),
        "error": raw.get("error"),
    }


def _evaluate_rules(normalized: dict, *, expect_json: bool) -> list[dict]:
    """Run deterministic rule checks over normalized data."""
    status_code = normalized.get("status_code")
    ok = normalized.get("ok", False)
    payload_type = normalized.get("payload_type")

    rules: list[dict] = []
    rules.append(
        {
            "name": "availability",
            "status": "pass" if ok else "fail",
            "message": "Endpoint returned success status"
            if ok
            else "Endpoint did not return success status",
        }
    )

    if isinstance(status_code, int) and 500 <= status_code <= 599:
        rules.append(
            {
                "name": "server_error",
                "status": "fail",
                "message": f"Server error status code: {status_code}",
            }
        )
    elif isinstance(status_code, int) and 400 <= status_code <= 499:
        rules.append(
            {
                "name": "client_error",
                "status": "warn",
                "message": f"Client error status code: {status_code}",
            }
        )

    if expect_json:
        rules.append(
            {
                "name": "expected_json",
                "status": "pass" if payload_type == "json" else "warn",
                "message": "Endpoint returned JSON payload"
                if payload_type == "json"
                else "Endpoint did not return JSON payload",
            }
        )

    if normalized.get("warning"):
        rules.append(
            {
                "name": "response_warning",
                "status": "warn",
                "message": normalized["warning"],
            }
        )

    return rules


def _derive_verdict(rules: list[dict]) -> str:
    """Collapse rule statuses into a single verdict."""
    statuses = {rule["status"] for rule in rules}
    if "fail" in statuses:
        return "unhealthy"
    if "warn" in statuses:
        return "degraded"
    return "healthy"


def _build_summary(verdict: str, rules: list[dict]) -> str:
    """Create a compact natural-language summary."""
    failed = [rule["name"] for rule in rules if rule["status"] == "fail"]
    warned = [rule["name"] for rule in rules if rule["status"] == "warn"]

    if verdict == "healthy":
        return "All checks passed."
    if verdict == "degraded":
        return f"Checks completed with warnings: {', '.join(warned)}."
    details = failed + warned
    return f"Checks failed: {', '.join(details)}."
