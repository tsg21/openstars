"""Shared logging context for request- and turn-scoped fields."""

import contextvars

game_id = contextvars.ContextVar("game_id", default=None)
turn = contextvars.ContextVar("turn", default=None)
