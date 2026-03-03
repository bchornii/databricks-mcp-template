"""Unit tests for ``server.application.calculations_workflow``."""

from server.application.calculations_workflow import execute_calculations_workflow


def test_execute_calculations_healthy_json_response():
    def fake_fetcher(url: str, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "ok": True,
            "status_code": 200,
            "content_type": "application/json",
            "json": {"status": "ok"},
        }

    result = execute_calculations_workflow(
        url="https://api.example.com/health",
        timeout_seconds=5,
        expect_json=True,
        fetcher=fake_fetcher,
    )

    assert result["verdict"] == "healthy"
    assert result["normalized_response"]["payload_type"] == "json"
    assert result["summary"] == "All checks passed."


def test_execute_calculations_unhealthy_on_server_error():
    def fake_fetcher(url: str, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "ok": False,
            "status_code": 503,
            "content_type": "text/plain",
            "body_preview": "Service unavailable",
            "error": "HTTP error: Service Unavailable",
        }

    result = execute_calculations_workflow(
        url="https://api.example.com/down",
        fetcher=fake_fetcher,
    )

    assert result["verdict"] == "unhealthy"
    rule_names = {rule["name"] for rule in result["rules"]}
    assert "availability" in rule_names
    assert "server_error" in rule_names


def test_execute_calculations_degraded_when_json_expected_but_text_returned():
    def fake_fetcher(url: str, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "ok": True,
            "status_code": 200,
            "content_type": "text/html",
            "body_preview": "<html>ok</html>",
        }

    result = execute_calculations_workflow(
        url="https://api.example.com/html",
        expect_json=True,
        fetcher=fake_fetcher,
    )

    assert result["verdict"] == "degraded"
    json_rule = next(rule for rule in result["rules"] if rule["name"] == "expected_json")
    assert json_rule["status"] == "warn"
