"""Altair geometry helpers — distance, range, and dissipation checks.

Uses ``isqrt`` from the shared engine utilities (PRD 10).
"""

from __future__ import annotations

from math import gcd

from openstars.engine.util import isqrt

_TRIG_SCALE = 1_000_000
_SIN_COS_8TH_TURN: tuple[tuple[int, int], ...] = (
    (0, _TRIG_SCALE),
    (707107, 707107),
    (_TRIG_SCALE, 0),
    (707107, -707107),
    (0, -_TRIG_SCALE),
    (-707107, -707107),
    (-_TRIG_SCALE, 0),
    (-707107, 707107),
)


def scaled_sin_cos(index: int, total: int) -> tuple[int, int]:
    """Return deterministic integer ``(sin, cos)`` for ``2π * index / total``.

    Supports exact lookup for octants and nearest-octant fallback otherwise.
    """
    if total <= 0:
        raise ValueError("total must be positive")
    if total == 1:
        return (0, _TRIG_SCALE)
    normalised = index % total
    if total % 8 == 0:
        slot = (normalised * 8) // total
        return _SIN_COS_8TH_TURN[slot]
    slot = (normalised * 8 + (total // 2)) // total
    return _SIN_COS_8TH_TURN[slot % 8]


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
