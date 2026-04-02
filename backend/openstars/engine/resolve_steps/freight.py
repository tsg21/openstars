"""Freight task resolution helpers."""

from math import ceil

from openstars.engine.models import Cargo, Design, Fleet, PlanetState, WaypointTask


def fleet_cargo_capacity(fleet: Fleet, designs_by_id: dict[str, Design]) -> int:
    """Return total cargo capacity for a fleet in kT."""
    total = 0
    for comp in fleet.composition:
        design = designs_by_id.get(comp.design_id)
        if design is not None:
            total += design.cargo_capacity * comp.count
    return total


def used_capacity(cargo: Cargo) -> int:
    """Return currently used capacity in kT."""
    return cargo.ironium + cargo.boranium + cargo.germanium + ceil(cargo.colonists / 100)


def remaining_capacity(fleet: Fleet, designs_by_id: dict[str, Design]) -> int:
    """Return free cargo space in kT."""
    return max(fleet_cargo_capacity(fleet, designs_by_id) - used_capacity(fleet.cargo), 0)


def resolve_load(
    action: str,
    amount: int | None,
    available: int,
    held: int,
    remaining_cap: int,
) -> int:
    """Resolve how much cargo should be loaded."""
    if action == "load_all":
        target = available
    elif action == "load_amount":
        target = max(amount or 0, 0)
    elif action == "load_up_to":
        target = max((amount or 0) - held, 0)
    else:
        return 0

    return max(min(target, available, remaining_cap), 0)


def resolve_unload(action: str, amount: int | None, held: int) -> int:
    """Resolve how much cargo should be unloaded."""
    if action == "unload_all":
        return held
    if action == "unload_amount":
        return min(max(amount or 0, 0), held)
    if action == "unload_but":
        return max(held - max(amount or 0, 0), 0)
    return 0


def _get_fleet_cargo_value(fleet: Fleet, cargo_type: str) -> int:
    return getattr(fleet.cargo, cargo_type)


def _get_planet_cargo_value(planet: PlanetState, cargo_type: str) -> int:
    if cargo_type == "colonists":
        return planet.population
    return getattr(planet.minerals, cargo_type)


def _set_fleet_cargo_value(fleet: Fleet, cargo_type: str, value: int) -> Fleet:
    return fleet.model_copy(update={"cargo": fleet.cargo.model_copy(update={cargo_type: value})})


def _set_planet_cargo_value(planet: PlanetState, cargo_type: str, value: int) -> PlanetState:
    if cargo_type == "colonists":
        return planet.model_copy(update={"population": value})
    return planet.model_copy(
        update={"minerals": planet.minerals.model_copy(update={cargo_type: value})}
    )


def _remaining_for_cargo_type(
    fleet: Fleet,
    designs_by_id: dict[str, Design],
    cargo_type: str,
) -> int:
    rem = remaining_capacity(fleet, designs_by_id)
    if cargo_type == "colonists":
        return rem * 100
    return rem


def execute_transport_task(
    fleet: Fleet,
    planet: PlanetState,
    task: WaypointTask,
    designs_by_id: dict[str, Design],
) -> tuple[Fleet, PlanetState]:
    """Apply cargo orders between fleet and planet."""
    updated_fleet = fleet
    updated_planet = planet

    for order in task.orders:
        held = _get_fleet_cargo_value(updated_fleet, order.cargo_type)
        available = _get_planet_cargo_value(updated_planet, order.cargo_type)
        remaining_cap = _remaining_for_cargo_type(updated_fleet, designs_by_id, order.cargo_type)
        if order.action.startswith("load_"):
            delta = resolve_load(order.action, order.amount, available, held, remaining_cap)
            updated_fleet = _set_fleet_cargo_value(updated_fleet, order.cargo_type, held + delta)
            updated_planet = _set_planet_cargo_value(
                updated_planet,
                order.cargo_type,
                available - delta,
            )
        elif order.action.startswith("unload_"):
            delta = resolve_unload(order.action, order.amount, held)
            updated_fleet = _set_fleet_cargo_value(updated_fleet, order.cargo_type, held - delta)
            updated_planet = _set_planet_cargo_value(
                updated_planet,
                order.cargo_type,
                available + delta,
            )

    return updated_fleet, updated_planet


def execute_transfer_task(
    fleet: Fleet,
    target_fleet: Fleet,
    task: WaypointTask,
    designs_by_id: dict[str, Design],
) -> tuple[Fleet, Fleet]:
    """Apply cargo orders between two fleets."""
    source = fleet
    target = target_fleet

    for order in task.orders:
        source_held = _get_fleet_cargo_value(source, order.cargo_type)
        target_held = _get_fleet_cargo_value(target, order.cargo_type)
        remaining_cap = _remaining_for_cargo_type(target, designs_by_id, order.cargo_type)
        if order.action.startswith("load_"):
            delta = resolve_load(
                order.action,
                order.amount,
                source_held,
                target_held,
                remaining_cap,
            )
            source = _set_fleet_cargo_value(source, order.cargo_type, source_held - delta)
            target = _set_fleet_cargo_value(target, order.cargo_type, target_held + delta)
        elif order.action.startswith("unload_"):
            delta = resolve_unload(order.action, order.amount, target_held)
            source = _set_fleet_cargo_value(source, order.cargo_type, source_held + delta)
            target = _set_fleet_cargo_value(target, order.cargo_type, target_held - delta)

    return source, target
