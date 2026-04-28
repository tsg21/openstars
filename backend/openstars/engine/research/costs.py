"""Research cost constants and helpers."""

from collections.abc import Mapping

FIELDS: tuple[str, ...] = (
    "energy",
    "weapons",
    "propulsion",
    "construction",
    "electronics",
    "biotechnology",
)
MAX_LEVEL: int = 26


# Fibonacci through L=11, then near-linear. Source: docs/references/starsfaq/art100.md
BASE_COST: tuple[int, ...] = (
    50,  # L=0  → 1
    80,  # L=1  → 2
    130,  # L=2  → 3
    210,  # L=3  → 4
    340,  # L=4  → 5
    550,  # L=5  → 6
    890,  # L=6  → 7
    1_440,  # L=7  → 8
    2_330,  # L=8  → 9
    3_770,  # L=9  → 10
    6_100,  # L=10 → 11
    9_870,  # L=11 → 12
    13_850,  # L=12 → 13
    18_040,  # L=13 → 14
    22_440,  # L=14 → 15
    27_050,  # L=15 → 16
    31_870,  # L=16 → 17
    36_900,  # L=17 → 18
    42_140,  # L=18 → 19
    47_590,  # L=19 → 20
    53_250,  # L=20 → 21
    59_120,  # L=21 → 22
    65_200,  # L=22 → 23
    71_490,  # L=23 → 24
    77_990,  # L=24 → 25
    84_700,  # L=25 → 26
)


def base_cost(level: int) -> int:
    if level < 0 or level >= MAX_LEVEL:
        raise ValueError("level out of range")
    return BASE_COST[level]


def level_up_cost(current_level: int, total_levels_value: int) -> int:
    if current_level < 0 or current_level >= MAX_LEVEL:
        raise ValueError("current_level out of range")
    return base_cost(current_level) + (10 * total_levels_value)


def total_levels(levels: Mapping[str, int]) -> int:
    return sum(levels.get(field, 0) for field in FIELDS)
