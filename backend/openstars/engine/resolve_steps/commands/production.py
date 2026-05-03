"""Apply production queue commands."""

from typing import Any

from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    MoveProductionItemCommand,
    PlanetState,
    ProductionQueueItem,
    RemoveProductionItemCommand,
)
from openstars.engine.resolve_steps.commands.parsing import (
    CommandParseContext,
    register_command_parser,
)
from openstars.engine.resolve_steps.production import remove_queue_item_quantity
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError

SUPPORTED_PRODUCTION_ITEM_TYPES = {"mine", "factory", "starbase", "ship", "planetary_scanner"}
SUPPORTED_STARBASE_TARGET_TYPES = {"orbital_fort", "space_station"}


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


def _parse_planet_id(
    cmd_dict: dict[str, Any],
    username: str,
    owned_planets: dict[str, PlanetState],
) -> str:
    planet_id = cmd_dict.get("planet_id")
    if not planet_id:
        raise GameError(400, "MISSING_PLANET_ID", "Command missing planet_id")
    if planet_id not in owned_planets:
        raise GameError(
            400,
            "PLANET_NOT_OWNED",
            f"Planet {planet_id} is not owned by player {username}",
        )
    return planet_id


def parse_production_command(
    cmd_dict: dict[str, Any],
    ctx: CommandParseContext,
) -> (
    AddProductionItemCommand
    | MoveProductionItemCommand
    | RemoveProductionItemCommand
    | ClearProductionQueueCommand
):
    cmd_type = cmd_dict.get("type")
    planet_id = _parse_planet_id(cmd_dict, ctx.username, ctx.owned_planets)
    queue_state = ctx.queue_state_by_planet[planet_id]

    if cmd_type == "add_production_item":
        item_type = cmd_dict.get("item_type")
        target_type = cmd_dict.get("target_type")
        design_id = cmd_dict.get("design_id")
        quantity = cmd_dict.get("quantity")
        insert_after_item_id = cmd_dict.get("insert_after_item_id")

        if item_type not in SUPPORTED_PRODUCTION_ITEM_TYPES:
            raise GameError(
                400,
                "UNSUPPORTED_PRODUCTION_ITEM",
                f"Unsupported production item type: {item_type}",
            )
        if not isinstance(quantity, int) or quantity <= 0:
            raise GameError(
                400,
                "INVALID_QUANTITY",
                "Production quantity must be a positive integer",
            )
        if item_type == "starbase":
            if target_type not in SUPPORTED_STARBASE_TARGET_TYPES:
                raise GameError(
                    400,
                    "INVALID_STARBASE_TARGET_TYPE",
                    f"Unsupported starbase target type: {target_type}",
                )
            if quantity != 1:
                raise GameError(
                    400,
                    "INVALID_QUANTITY",
                    "Starbase production quantity must be exactly 1",
                )
            if any(item.item_type == "starbase" for item in queue_state):
                raise GameError(
                    400,
                    "DUPLICATE_STARBASE_QUEUE_ITEM",
                    f"Planet {planet_id} already has an unfinished starbase queue item",
                )
            if (
                ctx.owned_planets[planet_id].starbase is not None
                and ctx.owned_planets[planet_id].starbase.type == target_type
            ):
                raise GameError(
                    400,
                    "INVALID_STARBASE_TARGET_TYPE",
                    f"Planet {planet_id} already has starbase type {target_type}",
                )
        elif target_type is not None:
            raise GameError(
                400,
                "INVALID_TARGET_TYPE",
                "target_type is only valid for starbase production items",
            )
        if item_type == "planetary_scanner":
            if quantity != 1:
                raise GameError(
                    400,
                    "INVALID_QUANTITY",
                    "Planetary scanner production quantity must be exactly 1",
                )
            if ctx.owned_planets[planet_id].has_scanner:
                raise GameError(
                    400,
                    "SCANNER_ALREADY_INSTALLED",
                    f"Planet {planet_id} already has a planetary scanner installed",
                )
            if any(item.item_type == "planetary_scanner" for item in queue_state):
                raise GameError(
                    400,
                    "DUPLICATE_SCANNER_QUEUE_ITEM",
                    f"Planet {planet_id} already has an unfinished planetary scanner queue item",
                )
        if item_type == "ship":
            if not isinstance(design_id, str) or len(design_id) == 0:
                raise GameError(
                    400,
                    "MISSING_DESIGN_ID",
                    "Ship production items require a design_id",
                )
            if design_id not in ctx.player_design_ids:
                raise GameError(
                    400,
                    "DESIGN_NOT_OWNED",
                    f"Ship design {design_id} is not owned by player {ctx.username}",
                )
            starbase = ctx.owned_planets[planet_id].starbase
            if starbase is None:
                raise GameError(
                    400,
                    "STARBASE_REQUIRED",
                    f"Planet {planet_id} requires a starbase to build ships",
                )
            if not starbase.can_build_ships:
                raise GameError(
                    400,
                    "STARBASE_CANNOT_BUILD_SHIPS",
                    f"Planet {planet_id} starbase cannot build ships",
                )
        elif design_id is not None:
            raise GameError(
                400,
                "INVALID_DESIGN_ID",
                "design_id is only valid for ship production items",
            )
        if (
            insert_after_item_id is not None
            and _queue_index(queue_state, insert_after_item_id) is None
        ):
            raise GameError(
                400,
                "QUEUE_ITEM_NOT_FOUND",
                f"Queue item {insert_after_item_id} was not found on planet {planet_id}",
            )

        command = AddProductionItemCommand(
            planet_id=planet_id,
            item_type=item_type,
            target_type=target_type,
            design_id=design_id,
            quantity=quantity,
            insert_after_item_id=insert_after_item_id,
        )
        queue_item_id = f"draft-{len(queue_state)}"
        updated_queue_state = _insert_queue_item(
            queue_state,
            ProductionQueueItem(
                id=queue_item_id,
                item_type=item_type,
                target_type=target_type,
                design_id=design_id,
                quantity=quantity,
            ),
            insert_after_item_id,
        )
        assert updated_queue_state is not None
        ctx.queue_state_by_planet[planet_id] = updated_queue_state
        return command

    if cmd_type == "move_production_item":
        item_id = cmd_dict.get("item_id")
        insert_after_item_id = cmd_dict.get("insert_after_item_id")
        item_index = _queue_index(queue_state, item_id) if item_id else None

        if item_index is None:
            raise GameError(
                400,
                "QUEUE_ITEM_NOT_FOUND",
                f"Queue item {item_id} was not found on planet {planet_id}",
            )
        if (
            insert_after_item_id is not None
            and insert_after_item_id != item_id
            and _queue_index(queue_state, insert_after_item_id) is None
        ):
            raise GameError(
                400,
                "QUEUE_ITEM_NOT_FOUND",
                f"Queue item {insert_after_item_id} was not found on planet {planet_id}",
            )

        command = MoveProductionItemCommand(
            planet_id=planet_id,
            item_id=item_id,
            insert_after_item_id=insert_after_item_id,
        )
        item = queue_state.pop(item_index)
        if insert_after_item_id is None or insert_after_item_id == item_id:
            queue_state.insert(0, item)
        else:
            insert_after_index = _queue_index(queue_state, insert_after_item_id)
            assert insert_after_index is not None
            queue_state.insert(insert_after_index + 1, item)
        return command

    if cmd_type == "remove_production_item":
        item_id = cmd_dict.get("item_id")
        quantity = cmd_dict.get("quantity")
        item_index = _queue_index(queue_state, item_id) if item_id else None

        if item_index is None:
            raise GameError(
                400,
                "QUEUE_ITEM_NOT_FOUND",
                f"Queue item {item_id} was not found on planet {planet_id}",
            )
        if not isinstance(quantity, int) or quantity <= 0:
            raise GameError(
                400,
                "INVALID_QUANTITY",
                "Production quantity must be a positive integer",
            )

        command = RemoveProductionItemCommand(
            planet_id=planet_id,
            item_id=item_id,
            quantity=quantity,
        )
        current_item = queue_state[item_index]
        if quantity >= current_item.quantity:
            queue_state.pop(item_index)
        else:
            queue_state[item_index] = current_item.model_copy(
                update={"quantity": current_item.quantity - quantity}
            )
        return command

    if cmd_type == "clear_production_queue":
        queue_state.clear()
        return ClearProductionQueueCommand(planet_id=planet_id)

    raise GameError(400, "UNKNOWN_COMMAND", f"Unknown command type: {cmd_type}")


for _command_type in (
    "add_production_item",
    "move_production_item",
    "remove_production_item",
    "clear_production_queue",
):
    register_command_parser(_command_type, parse_production_command)


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

    if cmd.item_type == "starbase":
        has_unfinished_starbase = any(
            item.item_type == "starbase" for item in planet.production_queue
        )
        if has_unfinished_starbase:
            return
        if planet.starbase is not None and planet.starbase.type == cmd.target_type:
            return
    if cmd.item_type == "planetary_scanner":
        if planet.has_scanner:
            return
        if any(item.item_type == "planetary_scanner" for item in planet.production_queue):
            return
    if cmd.item_type == "ship":
        if planet.starbase is None or not planet.starbase.can_build_ships:
            return
        if cmd.design_id is None:
            return
        design = ctx.designs_by_id.get(cmd.design_id)
        if design is None or design.owner != username:
            return
    queue_item_id = ctx.allocate_id("PQ")
    updated_queue = _insert_queue_item(
        planet.production_queue,
        ProductionQueueItem(
            id=queue_item_id,
            item_type=cmd.item_type,
            target_type=cmd.target_type,
            design_id=cmd.design_id,
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
