"""Design derivation and construction helpers shared across engine and server layers."""

from __future__ import annotations

from collections.abc import Mapping

from openstars.engine.component_catalogue import (
    ComponentCatalogue,
    ComponentCatalogueEntry,
    ComponentType,
    DesignDomain,
)
from openstars.engine.models import Design, DesignComponent, DesignCost, Minerals, Scanner
from openstars.engine.research.costs import FIELDS


class DesignValidationError(Exception):
    """Raised when a design payload fails validation."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _slot_accepts_component(slot_categories: list[str], component_type: ComponentType) -> bool:
    if component_type in slot_categories:
        return True
    if "general_purpose" in slot_categories and component_type in {
        "scanner",
        "weapon",
        "shield",
        "armour",
        "electrical",
        "mechanical",
    }:
        return True
    return False


def _validate_assignments(
    hull: ComponentCatalogueEntry,
    components: list[dict],
    catalogue: ComponentCatalogue,
) -> list[DesignComponent]:
    if hull.hull is None:
        raise DesignValidationError("UNKNOWN_HULL", f"Unknown hull {hull.id!r}")

    slots_by_number = {slot.slot_number: slot for slot in hull.hull.slots}
    assignments_by_slot: dict[int, DesignComponent] = {}

    for index, assignment in enumerate(components):
        if not isinstance(assignment, dict):
            raise DesignValidationError(
                "INVALID_COMPONENT_ASSIGNMENT",
                f"components[{index}] must be an object",
            )
        slot_number = assignment.get("slot_number")
        component_id = assignment.get("component_id")
        component_count = assignment.get("component_count")
        if (
            not isinstance(slot_number, int)
            or slot_number < 1
            or slot_number not in slots_by_number
        ):
            raise DesignValidationError(
                "UNKNOWN_SLOT",
                f"components[{index}] references unknown slot {slot_number!r}",
            )
        if not isinstance(component_id, str) or component_id not in catalogue.by_id:
            raise DesignValidationError(
                "UNKNOWN_COMPONENT",
                f"components[{index}] references unknown component {component_id!r}",
            )
        if not isinstance(component_count, int):
            raise DesignValidationError(
                "INVALID_COMPONENT_COUNT",
                f"components[{index}] component_count must be an integer",
            )
        if slot_number in assignments_by_slot:
            raise DesignValidationError(
                "DUPLICATE_SLOT_ASSIGNMENT",
                f"slot {slot_number!r} assigned more than once",
            )
        slot = slots_by_number[slot_number]
        component = catalogue.by_id[component_id]
        if not _slot_accepts_component(slot.slot_categories, component.component_type):
            raise DesignValidationError(
                "SLOT_INCOMPATIBLE_COMPONENT",
                f"slot {slot_number!r} does not accept component {component_id!r}",
            )
        if component_count > slot.capacity:
            raise DesignValidationError(
                "COMPONENT_COUNT_EXCEEDS_SLOT_CAPACITY",
                f"component_count for {slot_number!r} exceeds slot capacity {slot.capacity}",
            )
        assignments_by_slot[slot_number] = DesignComponent(
            slot_number=slot_number,
            component_id=component_id,
            component_count=component_count,
        )

    missing_required = [
        slot.slot_number
        for slot in hull.hull.slots
        if slot.required and slot.slot_number not in assignments_by_slot
    ]
    if missing_required:
        raise DesignValidationError(
            "REQUIRED_SLOT_MISSING",
            "Required slots are missing assignments: "
            f"{', '.join(str(slot_number) for slot_number in sorted(missing_required))}",
        )

    return [assignments_by_slot[key] for key in sorted(assignments_by_slot)]


def _compute_derived_stats(
    hull: ComponentCatalogueEntry,
    assignments: list[DesignComponent],
    catalogue: ComponentCatalogue,
) -> tuple[int, list[int], int, int, Scanner, DesignCost]:
    assert hull.hull is not None

    mass = hull.mass
    fuel_usage: list[int] | None = None
    cargo_capacity = hull.hull.cargo_capacity
    scanner_normal = 0
    scanner_penetrating = 0
    resources = hull.cost.resources
    ironium = hull.cost.ironium
    boranium = hull.cost.boranium
    germanium = hull.cost.germanium

    for assignment in assignments:
        component = catalogue.by_id[assignment.component_id]
        count = assignment.component_count
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

    return (
        mass,
        fuel_usage if fuel_usage is not None else [0] * 10,
        hull.hull.fuel_capacity,
        cargo_capacity,
        Scanner(normal=scanner_normal, penetrating=scanner_penetrating),
        DesignCost(
            resources=resources,
            minerals=Minerals(ironium=ironium, boranium=boranium, germanium=germanium),
        ),
    )


def _first_unmet_tech_requirement(
    entry: ComponentCatalogueEntry,
    player_levels: Mapping[str, int],
) -> tuple[str, int, int] | None:
    requirements = entry.tech_requirements.model_dump()
    for field in FIELDS:
        required = requirements.get(field, 0)
        level = player_levels.get(field, 0)
        if level < required:
            return field, required, level
    return None


def build_design(
    *,
    design_id: str,
    owner: str,
    name: str,
    hull_id: str,
    components: list[dict],
    catalogue: ComponentCatalogue,
    player_levels: Mapping[str, int],
    domain: DesignDomain = "ship",
) -> Design:
    """Validate a design payload and build a fully-derived ``Design``.

    Raises ``DesignValidationError`` with a stable ``code`` on any failure.
    """
    stripped_name = name.strip() if isinstance(name, str) else ""
    if not isinstance(name, str) or not stripped_name or len(stripped_name) > 64:
        raise DesignValidationError("INVALID_NAME", "Design name must be 1-64 non-space characters")

    hull_entry = catalogue.by_id.get(hull_id) if isinstance(hull_id, str) else None
    if (
        hull_entry is None
        or hull_entry.hull is None
        or hull_entry.component_type != "hull"
        or hull_entry.hull.domain != domain
    ):
        raise DesignValidationError("UNKNOWN_HULL", f"Unknown hull {hull_id!r}")

    if not isinstance(components, list):
        raise DesignValidationError("INVALID_COMPONENTS", "components must be a list")

    assignments = _validate_assignments(hull_entry, components, catalogue)
    hull_unmet = _first_unmet_tech_requirement(hull_entry, player_levels)
    if hull_unmet is not None:
        field, required, level = hull_unmet
        raise DesignValidationError(
            "TECH_LOCKED",
            f"Hull {hull_entry.name} requires {field} {required}, current level is {level}",
        )
    for assignment in assignments:
        component = catalogue.by_id[assignment.component_id]
        unmet = _first_unmet_tech_requirement(component, player_levels)
        if unmet is not None:
            field, required, level = unmet
            raise DesignValidationError(
                "TECH_LOCKED",
                f"Component {component.name} requires {field} {required}, current level is {level}",
            )

    mass, fuel_usage, fuel_capacity, cargo_capacity, scanner, cost = _compute_derived_stats(
        hull_entry, assignments, catalogue
    )
    if sum(fuel_usage) <= 0:
        raise DesignValidationError(
            "MISSING_ENGINE",
            "Design must include at least one engine assignment",
        )

    return Design(
        id=design_id,
        owner=owner,
        name=stripped_name,
        hull=hull_entry.id,
        components=assignments,
        mass=mass,
        fuel_usage=fuel_usage,
        fuel_capacity=fuel_capacity,
        scanner=scanner,
        cargo_capacity=cargo_capacity,
        cost=cost,
    )
