"""Structured JSON logging for Cloud Run.

Call ``setup_logging()`` at application startup to switch all loggers
(including uvicorn's access and error loggers) to JSON output.

Cloud Run parses the ``severity`` and ``message`` fields automatically,
so logs show up at the correct level in Cloud Logging.
"""

import logging
import os

from pythonjsonlogger.json import JsonFormatter  # python-json-logger 4.x


class _CloudRunFormatter(JsonFormatter):
    """JSON formatter that uses Cloud Run's expected field names."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "time", "levelname": "severity"},
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    def add_fields(
        self,
        log_record: dict,
        record: logging.LogRecord,
        message_dict: dict,
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        # Uvicorn adds color_message — useless in structured logs
        log_record.pop("color_message", None)


class _HealthCheckFilter(logging.Filter):
    """Drop uvicorn access-log entries for the health endpoint."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/v1/health" not in record.getMessage()


def setup_logging() -> None:
    """Configure structured JSON logging for all loggers."""
    use_json = os.environ.get("LOG_FORMAT", "json").lower() == "json"

    handler = logging.StreamHandler()

    if use_json:
        handler.setFormatter(_CloudRunFormatter())

    # Root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Uvicorn loggers — override their handlers so they use ours
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False

    # Suppress health check noise
    logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())
