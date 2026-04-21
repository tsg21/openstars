"""Shared path validation helpers for storage adapters."""

import re

# Only allow safe characters in path segments (alphanumeric, hyphens, underscores, dots)
SAFE_SEGMENT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def validate_segment(value: str, label: str) -> None:
    """Reject path segments that could escape a storage namespace."""
    if not SAFE_SEGMENT_RE.match(value) or ".." in value or "/" in value:
        raise ValueError(f"Unsafe {label}: {value!r}")


def game_object_name(game_id: str, *parts: str) -> str:
    """Build a validated object/file path inside a single game's namespace."""
    validate_segment(game_id, "game_id")
    return "/".join((game_id, *parts))
