"""Shared logging context for request- and turn-scoped fields."""

import contextvars
import logging
import time
from contextlib import contextmanager

game_id = contextvars.ContextVar("game_id", default=None)
turn = contextvars.ContextVar("turn", default=None)


@contextmanager
def log_duration(logger: logging.Logger, phase: str):
    """Log how long a block of code took, at INFO level.

    game_id/turn are picked up automatically via the contextvars above and
    ContextFilter — no need to pass them in explicitly.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("%s done in %.1fms", phase, elapsed_ms)
