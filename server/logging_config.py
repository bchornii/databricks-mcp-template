"""
Structured logging configuration for the MCP server.

Provides a single ``configure_logging()`` entry-point that should be called
once at application startup (in ``main.py``).  After that, every module
simply uses the stdlib pattern::

    import logging
    logger = logging.getLogger(__name__)

Key design choices:

* **JSON format in production** (when ``DATABRICKS_APP_NAME`` is set) for
  machine-parseable logs that integrate with observability pipelines.
* **Human-readable format in development** for quick local debugging.
* Log level is driven by ``Settings.log_level`` (default ``INFO``),
  overridable via the ``LOG_LEVEL`` environment variable.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from server.config import get_settings


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Merge any extra fields attached via `logger.info("msg", extra={...})`
        for key in ("tool", "request_id", "user", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value
        return json.dumps(log_entry, default=str)


_DEV_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> None:
    """
    Configure the root logger based on application settings.

    Call this **once** from ``main.py`` before the server starts.
    Subsequent calls are safe but have no additional effect.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    # Avoid adding duplicate handlers on repeated calls
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stderr)

    if settings.is_deployed:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_DEV_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))

    root.setLevel(level)
    handler.setLevel(level)
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
