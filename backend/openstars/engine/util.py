"""Shared engine utilities."""

import math


def isqrt(n: int) -> int:
    """Integer square root — largest r such that r² ≤ n.

    Newton's method on integers. Deterministic and platform-independent.
    """
    if n < 0:
        raise ValueError("isqrt requires non-negative input")
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def compute_bearing(fleet_x: int, fleet_y: int, wp_x: int, wp_y: int) -> float:
    """Compute bearing in degrees (0=north/up, clockwise) from fleet to waypoint."""
    dx = wp_x - fleet_x
    dy = wp_y - fleet_y
    angle = math.degrees(math.atan2(dx, -dy))
    if angle < 0:
        angle += 360.0
    return round(angle, 1)
