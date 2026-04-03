"""Apply player commands."""

import logging

from openstars.engine.ids import allocate_id
from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    Fleet,
    Galaxy,
    JettisonCargoCommand,
    MoveProductionItemCommand,
    PlanetState,
    PlayerCommands,
    ProductionQueueItem,
    RemoveProductionItemCommand,
    RenameFleetCommand,
    SetWaypointsCommand,
    Waypoint,
)
from openstars.engine.resolve_steps.production import remove_queue_item_quantity

log = logging.getLogger(__name__)


def apply_commands(
    fleets_by_id: dict[str, Fleet],
    planets_by_id: dict[str, PlanetState],
    planet_coords: set[tuple[int, int]],
    all_commands: dict[str, PlayerCommands],
    max_coord: int,
    game_seed: int,
    next_id: int,
) -> int:
    """Apply commands in-place and return the updated next-id counter.

    Processes players alphabetically for determinism.
    """
    for username in sorted(all_commands.keys()):
        for cmd in all_commands[username].commands:
            if isinstance(cmd, SetWaypointsCommand):
                _apply_set_waypoints_command(fleets_by_id, username, cmd, max_coord)
            elif isinstance(cmd, RenameFleetCommand):
                _apply_rename_fleet_command(fleets_by_id, username, cmd)
            elif isinstance(cmd, AddProductionItemCommand):
                next_id = _apply_add_production_item_command(
                    planets_by_id=planets_by_id,
                    username=username,
                    cmd=cmd,
                    game_seed=game_seed,
                    next_id=next_id,
                )
            elif isinstance(cmd, MoveProductionItemCommand):
                _apply_move_production_item_command(planets_by_id, username, cmd)
            elif isinstance(cmd, RemoveProductionItemCommand):
                _apply_remove_production_item_command(planets_by_id, username, cmd)
            elif isinstance(cmd, ClearProductionQueueCommand):
                _apply_clear_production_queue_command(planets_by_id, username, cmd)
            elif isinstance(cmd, JettisonCargoCommand):
                _apply_jettison_cargo_command(fleets_by_id, planet_coords, username, cmd)

    return next_id


def _apply_set_waypoints_command(
    fleets_by_id: dict[str, Fleet],
    username: str,
    cmd: SetWaypointsCommand,
    max_coord: int,
) -> None:
    fleet = fleets_by_id.get(cmd.fleet_id)
    if fleet is None or fleet.owner != username:
        return

    valid_waypoints = [
        Waypoint(x=wp.x, y=wp.y, task=wp.task)
        for wp in cmd.waypoints
        if 0 <= wp.x <= max_coord and 0 <= wp.y <= max_coord
    ]

    wp_summary = [(wp.x, wp.y, wp.task.type if wp.task else None) for wp in valid_waypoints]
    log.debug(
        "cmd set_waypoints: fleet=%s owner=%s waypoints=%s", cmd.fleet_id, username, wp_summary
    )

    fleets_by_id[cmd.fleet_id] = Fleet(
        id=fleet.id,
        name=fleet.name,
        owner=fleet.owner,
        position=fleet.position,
        composition=fleet.composition,
        cargo=fleet.cargo,
        repeat=fleet.repeat if cmd.repeat is None else cmd.repeat,
        waypoints=valid_waypoints,
    )


def _apply_rename_fleet_command(
    fleets_by_id: dict[str, Fleet],
    username: str,
    cmd: RenameFleetCommand,
) -> None:
    fleet = fleets_by_id.get(cmd.fleet_id)
    if fleet is None or fleet.owner != username:
        return

    log.debug("cmd rename_fleet: fleet=%s owner=%s name=%r", cmd.fleet_id, username, cmd.name)
    fleets_by_id[cmd.fleet_id] = fleet.model_copy(update={"name": cmd.name})


def _apply_jettison_cargo_command(
    fleets_by_id: dict[str, Fleet],
    planet_coords: set[tuple[int, int]],
    username: str,
    cmd: JettisonCargoCommand,
) -> None:
    fleet = fleets_by_id.get(cmd.fleet_id)
    if fleet is None or fleet.owner != username:
        return

    in_orbit = (fleet.position.x, fleet.position.y) in planet_coords
    if in_orbit:
        return

    updated_cargo = fleet.cargo.model_copy()
    for cargo_type in ("ironium", "boranium", "germanium", "colonists"):
        amount = getattr(cmd.cargo, cargo_type)
        if amount <= 0:
            continue
        held = getattr(updated_cargo, cargo_type)
        setattr(updated_cargo, cargo_type, max(held - amount, 0))

    fleets_by_id[fleet.id] = fleet.model_copy(update={"cargo": updated_cargo})
    log.debug("cmd jettison_cargo: fleet=%s owner=%s cargo=%s", fleet.id, username, cmd.cargo)


def _owned_planet(
    planets_by_id: dict[str, PlanetState],
    username: str,
    planet_id: str,
) -> PlanetState | None:
    planet = planets_by_id.get(planet_id)
    if planet is None or planet.owner != username:
        return None
    return planet


def _queue_index(queue: list[ProductionQueueItem], item_id: str) -> int | None:
    for index, item in enumerate(queue):
        if item.id == item_id:
            return index
    return None


def _insert_queue_item(
    queue: list[ProductionQueueItem],
    item: ProductionQueueItem,
    insert_after_item_id: str | None,
) -> list[ProductionQueueItem] | None:
    updated_queue = list(queue)
    if insert_after_item_id is None:
        updated_queue.insert(0, item)
        return updated_queue

    insert_after_index = _queue_index(updated_queue, insert_after_item_id)
    if insert_after_index is None:
        return None

    updated_queue.insert(insert_after_index + 1, item)
    return updated_queue


def _apply_add_production_item_command(
    planets_by_id: dict[str, PlanetState],
    username: str,
    cmd: AddProductionItemCommand,
    game_seed: int,
    next_id: int,
) -> int:
    planet = _owned_planet(planets_by_id, username, cmd.planet_id)
    if planet is None:
        return next_id

    queue_item_id, next_id = allocate_id(next_id, game_seed, "PQ")
    updated_queue = _insert_queue_item(
        planet.production_queue,
        ProductionQueueItem(
            id=queue_item_id,
            item_type=cmd.item_type,
            quantity=cmd.quantity,
        ),
        cmd.insert_after_item_id,
    )
    if updated_queue is None:
        return next_id - 1

    planets_by_id[planet.id] = planet.model_copy(update={"production_queue": updated_queue})
    return next_id


def _apply_move_production_item_command(
    planets_by_id: dict[str, PlanetState],
    username: str,
    cmd: MoveProductionItemCommand,
) -> None:
    planet = _owned_planet(planets_by_id, username, cmd.planet_id)
    if planet is None:
        return

    current_index = _queue_index(planet.production_queue, cmd.item_id)
    if current_index is None or cmd.insert_after_item_id == cmd.item_id:
        return

    updated_queue = list(planet.production_queue)
    item = updated_queue.pop(current_index)
    reinserted_queue = _insert_queue_item(updated_queue, item, cmd.insert_after_item_id)
    if reinserted_queue is None:
        return

    planets_by_id[planet.id] = planet.model_copy(update={"production_queue": reinserted_queue})


def _apply_remove_production_item_command(
    planets_by_id: dict[str, PlanetState],
    username: str,
    cmd: RemoveProductionItemCommand,
) -> None:
    planet = _owned_planet(planets_by_id, username, cmd.planet_id)
    if planet is None:
        return

    item_index = _queue_index(planet.production_queue, cmd.item_id)
    if item_index is None:
        return

    updated_queue = list(planet.production_queue)
    updated_item = remove_queue_item_quantity(
        updated_queue[item_index],
        cmd.quantity,
        discard_in_progress_unit=cmd.quantity >= updated_queue[item_index].quantity,
    )
    if updated_item is None:
        updated_queue.pop(item_index)
    else:
        updated_queue[item_index] = updated_item

    planets_by_id[planet.id] = planet.model_copy(update={"production_queue": updated_queue})


def _apply_clear_production_queue_command(
    planets_by_id: dict[str, PlanetState],
    username: str,
    cmd: ClearProductionQueueCommand,
) -> None:
    planet = _owned_planet(planets_by_id, username, cmd.planet_id)
    if planet is None:
        return

    planets_by_id[planet.id] = planet.model_copy(update={"production_queue": []})


def galaxy_max_coord(galaxy: Galaxy) -> int:
    """Return the maximum coordinate value for a galaxy size."""
    from openstars.engine.galaxy import GALAXY_SIZES

    bits = GALAXY_SIZES.get(galaxy.galaxy.size, 40)
    return (1 << bits) - 1
