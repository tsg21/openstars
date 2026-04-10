"""Design derivation helpers shared across engine and server layers."""

from openstars.engine.component_catalogue import ComponentCatalogueEntry
from openstars.engine.hull_definitions import HullDefinition, hull_mass_for_id
from openstars.engine.models import DesignCost, Minerals, Scanner

FUEL_CAPACITY_BY_HULL: dict[str, int] = {
    "scout": 50,
    "destroyer": 120,
    "small_freighter": 130,
    "colony_ship": 200,
}


def compute_design_derived_stats(
    hull: HullDefinition,
    assignments: list[dict],
    component_by_id: dict[str, ComponentCatalogueEntry],
) -> tuple[int, list[int], int, int, Scanner, DesignCost]:
    mass = hull_mass_for_id(hull.id)
    fuel_usage: list[int] | None = None
    cargo_capacity = 0
    scanner_normal = 0
    scanner_penetrating = 0
    resources = 0
    ironium = 0
    boranium = 0
    germanium = 0

    for assignment in assignments:
        component = component_by_id[assignment["component_id"]]
        count = assignment["component_count"]
        cost = component.cost
        resources += cost.resources * count
        ironium += cost.ironium * count
        boranium += cost.boranium * count
        germanium += cost.germanium * count
        mass += component.mass * count
        if component.engine is not None:
            fuel_usage = list(component.engine.fuel_usage)
        if component.scanner is not None:
            scanner_normal = max(scanner_normal, component.scanner.normal)
            scanner_penetrating = max(scanner_penetrating, component.scanner.penetrating)

    # Minimal hull baseline costs for the MVP.
    hull_resource_cost = 10 if hull.id == "scout" else 20
    hull_ironium_cost = 2 if hull.id == "scout" else 4
    resources += hull_resource_cost
    ironium += hull_ironium_cost

    return (
        mass,
        fuel_usage if fuel_usage is not None else [0] * 10,
        FUEL_CAPACITY_BY_HULL.get(hull.id, 0),
        cargo_capacity,
        Scanner(normal=scanner_normal, penetrating=scanner_penetrating),
        DesignCost(
            resources=resources,
            minerals=Minerals(
                ironium=ironium,
                boranium=boranium,
                germanium=germanium,
            ),
        ),
    )
