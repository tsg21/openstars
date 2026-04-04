"""Apply production queue commands."""

from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    MoveProductionItemCommand,
    PlanetState,
    ProductionQueueItem,
    RemoveProductionItemCommand,
)
from openstars.engine.resolve_steps.production import remove_queue_item_quantity
from openstars.engine.turn_context import TurnContext


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


def apply_add_production_item_command(
    planets_by_id: dict[str, PlanetState],
    username: str,
    cmd: AddProductionItemCommand,
    ctx: TurnContext,
) -> None:
    planet = _owned_planet(planets_by_id, username, cmd.planet_id)
    if planet is None:
        return

    if cmd.insert_after_item_id is not None and (
        _queue_index(planet.production_queue, cmd.insert_after_item_id) is None
    ):
        return

    queue_item_id = ctx.allocate_id("PQ")
    updated_queue = _insert_queue_item(
        planet.production_queue,
        ProductionQueueItem(
            id=queue_item_id,
            item_type=cmd.item_type,
            quantity=cmd.quantity,
        ),
        cmd.insert_after_item_id,
    )
    planets_by_id[planet.id] = planet.model_copy(update={"production_queue": updated_queue})


def apply_move_production_item_command(
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


def apply_remove_production_item_command(
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


def apply_clear_production_queue_command(
    planets_by_id: dict[str, PlanetState],
    username: str,
    cmd: ClearProductionQueueCommand,
) -> None:
    planet = _owned_planet(planets_by_id, username, cmd.planet_id)
    if planet is None:
        return

    planets_by_id[planet.id] = planet.model_copy(update={"production_queue": []})
