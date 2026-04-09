"""Player gameplay endpoints (PRD 09)."""

from fastapi import APIRouter, Depends, Header

from openstars.engine.fog import derive_player_state
from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    JettisonCargoCommand,
    MoveProductionItemCommand,
    PlayerCommands,
    ProductionQueueItem,
    RemoveProductionItemCommand,
    RenameFleetCommand,
    SetWaypointsCommand,
    Waypoint,
)
from openstars.engine.resolve import resolve_turn
from openstars.server.deps import get_storage
from openstars.server.errors import error_response
from openstars.server.game_designs import list_all_designs_for_players
from openstars.server.log_context import game_id as game_id_log_context
from openstars.server.schemas import (
    ResolveResponse,
    SubmitCommandsRequest,
    SubmitCommandsResponse,
    TurnStatusResponse,
)
from openstars.server.turns import get_current_turn
from openstars.storage.base import GameStorage

router = APIRouter(prefix="/api/v1/games/{game_id}", tags=["play"])

SUPPORTED_PRODUCTION_ITEM_TYPES = {"mine", "factory", "starbase", "ship"}
SUPPORTED_STARBASE_TARGET_TYPES = {"orbital_fort", "space_station"}


def _validate_player(storage: GameStorage, game_id: str, username: str):
    """Check game exists and player is a participant. Returns (meta, error_response)."""
    try:
        meta = storage.load_game_meta(game_id)
    except FileNotFoundError:
        return None, error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")

    if username not in meta.get("players", []):
        return None, error_response(
            403, "NOT_PARTICIPANT", "You are not a participant in this game"
        )

    return meta, None


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


@router.get("/turn-status")
async def get_turn_status(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the current turn number using lightweight metadata."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    return TurnStatusResponse(turn=get_current_turn(storage, game_id, meta))


@router.get("/galaxy")
async def get_galaxy(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the static galaxy definition."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    try:
        galaxy = storage.load_galaxy(game_id)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", "Galaxy data not found")

    return galaxy.model_dump()


@router.get("/state")
async def get_state(
    game_id: str,
    turn: int | None = None,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the player's state for a given turn (default: current)."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    if turn is None:
        turn = get_current_turn(storage, game_id, meta)

    try:
        ps = storage.load_player_state(game_id, x_player, turn)
    except FileNotFoundError:
        return error_response(404, "TURN_NOT_FOUND", f"State for turn {turn} not found")

    return ps.model_dump()


@router.post("/commands")
async def submit_commands(
    game_id: str,
    req: SubmitCommandsRequest,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Submit commands for the current turn."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(storage, game_id, meta)
    if req.turn != current_turn:
        return error_response(
            409,
            "TURN_MISMATCH",
            f"Submitted turn {req.turn} but current turn is {current_turn}",
        )

    # Parse and validate commands
    try:
        global_state = storage.load_global_state(game_id, current_turn)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", "Game state not found")

    # Load galaxy for bounds checking
    galaxy = storage.load_galaxy(game_id)
    from openstars.engine.galaxy import GALAXY_SIZES

    max_coord = (1 << GALAXY_SIZES.get(galaxy.galaxy.size, 40)) - 1

    # Build owned entity lookups for command validation.
    owned_fleets = {f.id for f in global_state.fleets if f.owner == x_player}
    owned_planets = {p.id: p for p in global_state.planets if p.owner == x_player}
    queue_state_by_planet = {
        planet_id: [item.model_copy(deep=True) for item in planet.production_queue]
        for planet_id, planet in owned_planets.items()
    }

    parsed_commands = []
    for cmd_dict in req.commands:
        cmd_type = cmd_dict.get("type")
        if cmd_type == "set_waypoints":
            fleet_id = cmd_dict.get("fleet_id")
            if not fleet_id:
                return error_response(400, "MISSING_FLEET_ID", "Command missing fleet_id")
            if fleet_id not in owned_fleets:
                return error_response(
                    400,
                    "FLEET_NOT_OWNED",
                    f"Fleet {fleet_id} is not owned by player {x_player}",
                )

            waypoints_raw = cmd_dict.get("waypoints", [])
            waypoints = []
            for wp in waypoints_raw:
                if not isinstance(wp, dict) or "x" not in wp or "y" not in wp:
                    return error_response(400, "INVALID_WAYPOINT", "Waypoints must have x and y")
                wx, wy = wp["x"], wp["y"]
                if not isinstance(wx, int) or not isinstance(wy, int):
                    return error_response(
                        400,
                        "INVALID_WAYPOINT",
                        "Waypoint coordinates must be integers",
                    )
                if not (0 <= wx <= max_coord and 0 <= wy <= max_coord):
                    return error_response(
                        400,
                        "WAYPOINT_OUT_OF_BOUNDS",
                        f"Waypoint ({wx}, {wy}) is outside galaxy bounds (0-{max_coord})",
                    )
                waypoints.append(Waypoint.model_validate(wp))

            parsed_commands.append(SetWaypointsCommand(fleet_id=fleet_id, waypoints=waypoints))
            continue

        if cmd_type == "jettison_cargo":
            fleet_id = cmd_dict.get("fleet_id")
            if not fleet_id:
                return error_response(400, "MISSING_FLEET_ID", "Command missing fleet_id")
            if fleet_id not in owned_fleets:
                return error_response(
                    400,
                    "FLEET_NOT_OWNED",
                    f"Fleet {fleet_id} is not owned by player {x_player}",
                )

            parsed_commands.append(JettisonCargoCommand.model_validate(cmd_dict))
            continue

        if cmd_type == "rename_fleet":
            fleet_id = cmd_dict.get("fleet_id")
            if not fleet_id:
                return error_response(400, "MISSING_FLEET_ID", "Command missing fleet_id")
            if fleet_id not in owned_fleets:
                return error_response(
                    400,
                    "FLEET_NOT_OWNED",
                    f"Fleet {fleet_id} is not owned by player {x_player}",
                )
            name = cmd_dict.get("name", "")
            if not name or not isinstance(name, str) or len(name) > 64:
                return error_response(
                    400,
                    "INVALID_FLEET_NAME",
                    "Fleet name must be a non-empty string of at most 64 characters",
                )

            parsed_commands.append(RenameFleetCommand(fleet_id=fleet_id, name=name))
            continue

        planet_id = cmd_dict.get("planet_id")
        if not planet_id:
            return error_response(400, "MISSING_PLANET_ID", "Command missing planet_id")
        if planet_id not in owned_planets:
            return error_response(
                400,
                "PLANET_NOT_OWNED",
                f"Planet {planet_id} is not owned by player {x_player}",
            )

        queue_state = queue_state_by_planet[planet_id]

        if cmd_type == "add_production_item":
            item_type = cmd_dict.get("item_type")
            target_type = cmd_dict.get("target_type")
            design_id = cmd_dict.get("design_id")
            quantity = cmd_dict.get("quantity")
            insert_after_item_id = cmd_dict.get("insert_after_item_id")

            if item_type not in SUPPORTED_PRODUCTION_ITEM_TYPES:
                return error_response(
                    400,
                    "UNSUPPORTED_PRODUCTION_ITEM",
                    f"Unsupported production item type: {item_type}",
                )
            if not isinstance(quantity, int) or quantity <= 0:
                return error_response(
                    400,
                    "INVALID_QUANTITY",
                    "Production quantity must be a positive integer",
                )
            if item_type == "starbase":
                if target_type not in SUPPORTED_STARBASE_TARGET_TYPES:
                    return error_response(
                        400,
                        "INVALID_STARBASE_TARGET_TYPE",
                        f"Unsupported starbase target type: {target_type}",
                    )
                if quantity != 1:
                    return error_response(
                        400,
                        "INVALID_QUANTITY",
                        "Starbase production quantity must be exactly 1",
                    )
                if any(item.item_type == "starbase" for item in queue_state):
                    return error_response(
                        400,
                        "DUPLICATE_STARBASE_QUEUE_ITEM",
                        f"Planet {planet_id} already has an unfinished starbase queue item",
                    )
                if (
                    owned_planets[planet_id].starbase is not None
                    and owned_planets[planet_id].starbase.type == target_type
                ):
                    return error_response(
                        400,
                        "INVALID_STARBASE_TARGET_TYPE",
                        f"Planet {planet_id} already has starbase type {target_type}",
                    )
            elif target_type is not None:
                return error_response(
                    400,
                    "INVALID_TARGET_TYPE",
                    "target_type is only valid for starbase production items",
                )
            if item_type == "ship":
                if not isinstance(design_id, str) or len(design_id) == 0:
                    return error_response(
                        400,
                        "MISSING_DESIGN_ID",
                        "Ship production items require a design_id",
                    )
                player_design_ids = {
                    design.id for design in storage.list_designs(game_id, x_player)
                }
                if design_id not in player_design_ids:
                    return error_response(
                        400,
                        "DESIGN_NOT_OWNED",
                        f"Ship design {design_id} is not owned by player {x_player}",
                    )
                starbase = owned_planets[planet_id].starbase
                if starbase is None:
                    return error_response(
                        400,
                        "STARBASE_REQUIRED",
                        f"Planet {planet_id} requires a starbase to build ships",
                    )
                if not starbase.can_build_ships:
                    return error_response(
                        400,
                        "STARBASE_CANNOT_BUILD_SHIPS",
                        f"Planet {planet_id} starbase cannot build ships",
                    )
            elif design_id is not None:
                return error_response(
                    400,
                    "INVALID_DESIGN_ID",
                    "design_id is only valid for ship production items",
                )
            if (
                insert_after_item_id is not None
                and _queue_index(queue_state, insert_after_item_id) is None
            ):
                return error_response(
                    400,
                    "QUEUE_ITEM_NOT_FOUND",
                    f"Queue item {insert_after_item_id} was not found on planet {planet_id}",
                )

            parsed_commands.append(
                AddProductionItemCommand(
                    planet_id=planet_id,
                    item_type=item_type,
                    target_type=target_type,
                    design_id=design_id,
                    quantity=quantity,
                    insert_after_item_id=insert_after_item_id,
                )
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
            queue_state_by_planet[planet_id] = updated_queue_state
            continue

        if cmd_type == "move_production_item":
            item_id = cmd_dict.get("item_id")
            insert_after_item_id = cmd_dict.get("insert_after_item_id")
            item_index = _queue_index(queue_state, item_id) if item_id else None

            if item_index is None:
                return error_response(
                    400,
                    "QUEUE_ITEM_NOT_FOUND",
                    f"Queue item {item_id} was not found on planet {planet_id}",
                )
            if (
                insert_after_item_id is not None
                and insert_after_item_id != item_id
                and _queue_index(queue_state, insert_after_item_id) is None
            ):
                return error_response(
                    400,
                    "QUEUE_ITEM_NOT_FOUND",
                    f"Queue item {insert_after_item_id} was not found on planet {planet_id}",
                )

            parsed_commands.append(
                MoveProductionItemCommand(
                    planet_id=planet_id,
                    item_id=item_id,
                    insert_after_item_id=insert_after_item_id,
                )
            )
            item = queue_state.pop(item_index)
            if insert_after_item_id is None or insert_after_item_id == item_id:
                queue_state.insert(0, item)
            else:
                insert_after_index = _queue_index(queue_state, insert_after_item_id)
                assert insert_after_index is not None
                queue_state.insert(insert_after_index + 1, item)
            continue

        if cmd_type == "remove_production_item":
            item_id = cmd_dict.get("item_id")
            quantity = cmd_dict.get("quantity")
            item_index = _queue_index(queue_state, item_id) if item_id else None

            if item_index is None:
                return error_response(
                    400,
                    "QUEUE_ITEM_NOT_FOUND",
                    f"Queue item {item_id} was not found on planet {planet_id}",
                )
            if not isinstance(quantity, int) or quantity <= 0:
                return error_response(
                    400,
                    "INVALID_QUANTITY",
                    "Production quantity must be a positive integer",
                )

            parsed_commands.append(
                RemoveProductionItemCommand(
                    planet_id=planet_id,
                    item_id=item_id,
                    quantity=quantity,
                )
            )
            current_item = queue_state[item_index]
            if quantity >= current_item.quantity:
                queue_state.pop(item_index)
            else:
                queue_state[item_index] = current_item.model_copy(
                    update={"quantity": current_item.quantity - quantity}
                )
            continue

        if cmd_type == "clear_production_queue":
            parsed_commands.append(ClearProductionQueueCommand(planet_id=planet_id))
            queue_state.clear()
            continue

        return error_response(400, "UNKNOWN_COMMAND", f"Unknown command type: {cmd_type}")

    player_commands = PlayerCommands(commands=parsed_commands)
    storage.save_commands(game_id, x_player, current_turn, player_commands)

    return SubmitCommandsResponse(
        turn=current_turn,
        command_count=len(parsed_commands),
    )


@router.get("/commands")
async def get_commands(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the player's submitted commands for the current turn."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(storage, game_id, meta)

    try:
        cmds = storage.load_commands(game_id, x_player, current_turn)
    except FileNotFoundError:
        return {"turn": current_turn, "commands": []}

    return {"turn": current_turn, "commands": [c.model_dump() for c in cmds.commands]}


@router.post("/resolve")
async def resolve(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    token = game_id_log_context.set(game_id)
    try:
        """Trigger turn resolution."""
        meta, err = _validate_player(storage, game_id, x_player)
        if err:
            return err

        current_turn = get_current_turn(storage, game_id, meta)
        players = meta.get("players", [])

        # Check all players have submitted
        for p in players:
            if not storage.has_commands(game_id, p, current_turn):
                return error_response(
                    409,
                    "NOT_ALL_SUBMITTED",
                    f"Not all players have submitted commands (waiting for: {p})",
                )

        # Load current state and all commands
        global_state = storage.load_global_state(game_id, current_turn)
        galaxy = storage.load_galaxy(game_id)
        designs = list_all_designs_for_players(storage, game_id, players)

        all_commands = {}
        for p in players:
            all_commands[p] = storage.load_commands(game_id, p, current_turn)

        # Resolve
        new_state = resolve_turn(global_state, galaxy, all_commands, designs)
        new_turn = new_state.game.turn

        # Save new state. If another resolver already persisted this turn,
        # treat it as an expected race and return success idempotently.
        try:
            storage.save_global_state(game_id, new_turn, new_state)
        except FileExistsError:
            current_meta = storage.load_game_meta(game_id)
            if int(current_meta.get("current_turn", 0)) < new_turn:
                current_meta["current_turn"] = new_turn
                storage.save_game_meta(game_id, current_meta)
            return ResolveResponse(turn=new_turn)

        # Derive and save player states
        for p in players:
            ps = derive_player_state(new_state, galaxy, p, designs)
            storage.save_player_state(game_id, p, new_turn, ps)

        meta["current_turn"] = new_turn
        storage.save_game_meta(game_id, meta)

        return ResolveResponse(turn=new_turn)
    finally:
        game_id_log_context.reset(token)
