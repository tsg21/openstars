"""Miniaturisation helpers used at ship build time."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Protocol

from openstars.engine.component_catalogue import ComponentCatalogue
from openstars.engine.models import Design, Minerals
from openstars.engine.research.costs import FIELDS


class CostLike(Protocol):
    resources: int
    ironium: int
    boranium: int
    germanium: int


@dataclass(frozen=True)
class BuildCost:
    resources: int
    minerals: Minerals


def miniaturisation_discount(tech_req: Mapping[str, int], levels: Mapping[str, int]) -> float:
    requirements = {field: int(tech_req.get(field, 0)) for field in FIELDS}
    for field in FIELDS:
        if levels.get(field, 0) < requirements[field]:
            return 0.0
    excess = min(levels.get(field, 0) - requirements[field] for field in FIELDS)
    req_cap = 26 - max(requirements.values(), default=0)
    return min(excess, req_cap, 19) * 0.04


def _round_half_even(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def miniaturise_cost(base: CostLike, discount: float) -> BuildCost:
    def apply(value: int) -> int:
        if value == 0:
            return 0
        discounted = _round_half_even(value * (1 - discount))
        return max(discounted, 1)

    return BuildCost(
        resources=apply(base.resources),
        minerals=Minerals(
            ironium=apply(base.ironium),
            boranium=apply(base.boranium),
            germanium=apply(base.germanium),
        ),
    )


def design_build_cost(
    design: Design,
    catalogue: ComponentCatalogue,
    levels: Mapping[str, int],
) -> BuildCost:
    hull = catalogue.by_id[design.hull]
    hull_cost = miniaturise_cost(
        hull.cost,
        miniaturisation_discount(hull.tech_requirements.model_dump(), levels),
    )
    total_resources = hull_cost.resources
    minerals = hull_cost.minerals.model_copy(deep=True)

    for assignment in design.components:
        component = catalogue.by_id[assignment.component_id]
        discounted = miniaturise_cost(
            component.cost,
            miniaturisation_discount(component.tech_requirements.model_dump(), levels),
        )
        total_resources += discounted.resources * assignment.component_count
        minerals.ironium += discounted.minerals.ironium * assignment.component_count
        minerals.boranium += discounted.minerals.boranium * assignment.component_count
        minerals.germanium += discounted.minerals.germanium * assignment.component_count

    return BuildCost(resources=total_resources, minerals=minerals)
