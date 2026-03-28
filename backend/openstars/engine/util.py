"""Shared engine utilities."""


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
