"""Altair geometry helpers — distance and range checks.

Uses ``isqrt`` from the shared engine utilities (PRD 10).
"""

from __future__ import annotations

from openstars.engine.util import isqrt


def distance(ax: int, ay: int, bx: int, by: int) -> int:
    """Integer Euclidean distance between two arena positions.

    ``isqrt(dx² + dy²)`` — deterministic, no floats.
    """
    dx = ax - bx
    dy = ay - by
    return isqrt(dx * dx + dy * dy)


def in_range(
    dist: int,
    R_classic: int,
    S: int,
    starbase_bonus: bool = False,
) -> bool:
    """Return True if *dist* is within weapon range.

    Range threshold is ``R_classic * S`` plus an optional ``+S`` for
    starbases with the classic +1 range bonus (PRD 82 §Distance).
    """
    threshold = R_classic * S
    if starbase_bonus:
        threshold += S
    return dist <= threshold
