"""External HTTP request integration.

Uses only the Python standard library (``urllib``) so there is no extra
runtime dependency.  The module is provider-agnostic — it can call any
HTTP endpoint, not just Databricks APIs.
"""

import json
import logging
from urllib import error, request

logger = logging.getLogger(__name__)

#: Maximum number of characters returned in ``body_preview``.
_BODY_PREVIEW_LIMIT = 1000


def fetch_url_status(url: str, timeout_seconds: int = 10) -> dict:
    """
    Perform an HTTP GET and return a structured summary of the response.

    Args:
        url: The HTTP/HTTPS endpoint to call.
        timeout_seconds: Request timeout in seconds (default: 10).

    Returns:
        A dict that always contains ``url`` and ``ok``.  On success it
        also includes ``status_code``, ``content_type``, and either
        ``json`` (parsed) or ``body_preview`` (truncated text).  On
        failure it includes ``error`` with a human-readable message.
    """
    logger.debug("GET %s (timeout=%ds)", url, timeout_seconds)
    try:
        req = request.Request(url=url, method="GET")
        with request.urlopen(req, timeout=timeout_seconds) as response:
            return _parse_success_response(url, response)
    except error.HTTPError as e:
        return _handle_http_error(url, e)
    except error.URLError as e:
        return {"url": url, "ok": False, "error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"url": url, "ok": False, "error": f"Unexpected error: {str(e)}"}


def _parse_success_response(url: str, response) -> dict:
    """Build the result dict from a successful ``urlopen`` response."""
    content_type = response.headers.get("Content-Type", "")
    payload_text = response.read().decode("utf-8", errors="replace")

    result: dict = {
        "url": url,
        "status_code": response.status,
        "ok": 200 <= response.status < 300,
        "content_type": content_type,
    }

    if "application/json" in content_type.lower():
        try:
            result["json"] = json.loads(payload_text)
        except json.JSONDecodeError:
            result["body_preview"] = payload_text[:_BODY_PREVIEW_LIMIT]
            result["warning"] = "Response declared JSON but parsing failed"
    else:
        result["body_preview"] = payload_text[:_BODY_PREVIEW_LIMIT]

    return result


def _handle_http_error(url: str, exc: error.HTTPError) -> dict:
    """Build the result dict from an ``HTTPError``."""
    body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
    return {
        "url": url,
        "status_code": exc.code,
        "ok": False,
        "error": f"HTTP error: {exc.reason}",
        "body_preview": body[:_BODY_PREVIEW_LIMIT],
    }
