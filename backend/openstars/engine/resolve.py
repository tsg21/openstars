"""Turn resolution engine (PRD 07).

Phase 1 pipeline:
  1. Apply commands (set_waypoints)
  2. Move fleets
  3. Increment turn counter
"""

from openstars.engine.models import (
    Fleet,
    Galaxy,
    GameMeta,
    GlobalState,
    PlayerCommands,
    Position,
)
from openstars.engine.movement import move_fleet


def resolve_turn(
    global_state: GlobalState,
    galaxy: Galaxy,
    all_commands: dict[str, PlayerCommands],
) -> GlobalState:
    """Resolve one turn.

    Args:
        global_state: Current game state.
        galaxy: Galaxy definition (static).
        all_commands: Mapping of username → PlayerCommands.

    Returns:
        New GlobalState for the next turn.
    """
    # Build fleet lookup (mutable copies)
    fleets_by_id: dict[str, Fleet] = {f.id: f.model_copy() for f in global_state.fleets}

    # Build design speed lookup
    design_speeds: dict[str, int] = {d.id: d.speed for d in global_state.designs}

    # Galaxy bounds for validation
    max_coord = _galaxy_max_coord(galaxy)

    # --- Step 1: Apply commands ---
    # Process players alphabetically for determinism
    for username in sorted(all_commands.keys()):
        commands = all_commands[username]
        for cmd in commands.commands:
            if cmd.type == "set_waypoints":
                fleet = fleets_by_id.get(cmd.fleet_id)
                if fleet is None:
                    continue  # Unknown fleet — skip
                if fleet.owner != username:
                    continue  # Not owned by this player — skip

                # Validate waypoint coordinates
                valid_waypoints = []
                for wp in cmd.waypoints:
                    if 0 <= wp.x <= max_coord and 0 <= wp.y <= max_coord:
                        valid_waypoints.append(Position(x=wp.x, y=wp.y))

                # Replace fleet waypoints
                fleets_by_id[cmd.fleet_id] = Fleet(
                    id=fleet.id,
                    owner=fleet.owner,
                    position=fleet.position,
                    composition=fleet.composition,
                    waypoints=valid_waypoints,
                )

    # --- Step 2: Move fleets ---
    # Process fleets sorted by ID for determinism
    moved_fleets = []
    for fleet_id in sorted(fleets_by_id.keys()):
        fleet = fleets_by_id[fleet_id]
        moved = move_fleet(fleet, design_speeds)
        moved_fleets.append(moved)

    # --- Step 3: Increment turn counter ---
    new_turn = global_state.game.turn + 1

    return GlobalState(
        game=GameMeta(
            seed=global_state.game.seed,
            turn=new_turn,
            next_id=global_state.game.next_id,
        ),
        players=global_state.players,
        designs=global_state.designs,
        planets=global_state.planets,
        fleets=moved_fleets,
    )


def _galaxy_max_coord(galaxy: Galaxy) -> int:
    """Get the maximum coordinate value for a galaxy size."""
    from openstars.engine.galaxy import GALAXY_SIZES

    bits = GALAXY_SIZES.get(galaxy.galaxy.size, 40)
    return (1 << bits) - 1
