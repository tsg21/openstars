"""Design derivation helpers shared across engine and server layers."""

from openstars.engine.component_catalogue import ComponentCatalogueEntry
from openstars.engine.models import DesignCost, Minerals, Scanner


def compute_design_derived_stats(
    hull: ComponentCatalogueEntry,
    assignments: list[dict],
    component_by_id: dict[str, ComponentCatalogueEntry],
) -> tuple[int, list[int], int, int, Scanner, DesignCost]:
    hull_entry = component_by_id[hull.id]
    if hull_entry.hull is None:
        raise ValueError(f"hull {hull.id!r} is missing hull stats in component catalogue")

    mass = hull_entry.mass
    fuel_usage: list[int] | None = None
    cargo_capacity = hull_entry.hull.cargo_capacity
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
        hull_entry.hull.fuel_capacity,
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
