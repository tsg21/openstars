"""Altair geometry helpers — distance, range, and dissipation checks.

Uses ``isqrt`` from the shared engine utilities (PRD 10).
"""

from __future__ import annotations

from math import gcd

from openstars.engine.util import isqrt


def distance(ax: int, ay: int, bx: int, by: int) -> int:
    """Integer Euclidean distance between two arena positions.

    ``isqrt(dx² + dy²)`` — deterministic, no floats.
    """
    dx = ax - bx
    dy = ay - by
    return isqrt(dx * dx + dy * dy)


def effective_weapon_range(
    R_classic: int,
    S: int,
    starbase_bonus: bool = False,
) -> int:
    """Return effective range in arena units."""
    effective_range = R_classic * S
    if starbase_bonus:
        effective_range += S
    return effective_range


def beam_flat_zone_threshold(effective_range: int) -> int:
    """Return the no-dissipation beam threshold in arena units.

    Altair keeps full beam damage through the first 20% of effective range.
    """
    return effective_range // 5


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
    return dist <= effective_weapon_range(R_classic, S, starbase_bonus)


def beam_dissipation_multiplier(
    dist: int,
    R_classic: int,
    S: int,
    starbase_bonus: bool = False,
) -> tuple[int, int]:
    """Return the Altair beam damage multiplier as ``(numerator, denominator)``.

    The multiplier is flat at 100% up to ``R_eff // 5``, then drops linearly
    to 90% at ``R_eff``. Range-0 weapons stay at full damage when they can hit.
    """
    effective_range = effective_weapon_range(R_classic, S, starbase_bonus)
    threshold = beam_flat_zone_threshold(effective_range)

    if effective_range == 0 or dist <= threshold:
        return (1, 1)

    span = effective_range - threshold
    denominator = 10 * span
    numerator = denominator - (dist - threshold)
    divisor = gcd(numerator, denominator)
    return (numerator // divisor, denominator // divisor)
