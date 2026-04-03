"""Structured JSON logging for Cloud Run.

Call ``setup_logging()`` at application startup to switch all loggers
(including uvicorn's access and error loggers) to JSON output.

Cloud Run parses the ``severity`` and ``message`` fields automatically,
so logs show up at the correct level in Cloud Logging.
"""

import logging
import os

from pythonjsonlogger.json import JsonFormatter  # python-json-logger 4.x

from openstars.server.log_context import game_id, turn


class ContextFilter(logging.Filter):
    def filter(self, record):
        current_game_id = game_id.get()
        current_turn = turn.get()
        if current_game_id is not None:
            record.game_id = current_game_id
        if current_turn is not None:
            record.turn = current_turn
        return True


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
        if hasattr(record, "game_id"):
            log_record["game_id"] = record.game_id
        if hasattr(record, "turn"):
            log_record["turn"] = record.turn


class _TextFormatter(logging.Formatter):
    """Text formatter that appends context only when present."""

    def __init__(self) -> None:
        super().__init__("[%(levelname)s] %(message)s%(context_suffix)s")

    def format(self, record: logging.LogRecord) -> str:
        context_parts: list[str] = []
        if hasattr(record, "game_id"):
            context_parts.append(f"game={record.game_id}")
        if hasattr(record, "turn"):
            context_parts.append(f"turn={record.turn}")
        record.context_suffix = f" ({' '.join(context_parts)})" if context_parts else ""
        return super().format(record)


class _HealthCheckFilter(logging.Filter):
    """Drop uvicorn access-log entries for the health endpoint."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/v1/health" not in record.getMessage()


def setup_logging() -> None:
    """Configure structured JSON logging for all loggers.

    Set LOG_LEVEL=DEBUG to enable engine trace logging.
    """
    use_json = os.environ.get("LOG_FORMAT", "text").lower() == "json"
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.addFilter(ContextFilter())

    if use_json:
        handler.setFormatter(_CloudRunFormatter())
    else:
        handler.setFormatter(_TextFormatter())

    # Root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Uvicorn loggers — override their handlers so they use ours
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False

    # Suppress health check noise
    logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())
