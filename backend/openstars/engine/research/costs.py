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


def _build_base_cost() -> tuple[int, ...]:
    values = [50, 80]
    while len(values) < MAX_LEVEL:
        values.append(values[-1] + values[-2])
    return tuple(values)


BASE_COST: tuple[int, ...] = _build_base_cost()


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
