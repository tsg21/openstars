"""Fog of war — derive player-visible state from global state (PRD 03/11)."""

import math

from openstars.engine.galaxy import PARSEC
from openstars.engine.models import (
    Galaxy,
    GlobalState,
    PlayerFleet,
    PlayerPlanet,
    PlayerProductionQueueItem,
    PlayerState,
)
from openstars.engine.resolve_steps import economy
from openstars.engine.resolve_steps.freight import fleet_cargo_capacity
from openstars.engine.resolve_steps.population import max_population


def _scanner_positions(global_state: GlobalState, username: str) -> list[tuple[int, int, int, int]]:
    """Get all scanner positions and ranges for a player.

    Returns list of (x, y, normal_range_coord, pen_range_coord) from the
    player's fleets.
    """
    # Build a lookup for design scanner ranges
    design_scanners: dict[str, tuple[int, int]] = {}
    for d in global_state.designs:
        if d.owner == username:
            design_scanners[d.id] = (
                d.scanner.normal * PARSEC,
                d.scanner.penetrating * PARSEC,
            )

    scanners: list[tuple[int, int, int, int]] = []
    for fleet in global_state.fleets:
        if fleet.owner != username:
            continue
        # Fleet scanner range = max of any design in composition (for each type)
        max_normal = 0
        max_pen = 0
        for comp in fleet.composition:
            if comp.design_id in design_scanners:
                n, p = design_scanners[comp.design_id]
                if n > max_normal:
                    max_normal = n
                if p > max_pen:
                    max_pen = p
        if max_normal > 0:
            scanners.append((fleet.position.x, fleet.position.y, max_normal, max_pen))

    return scanners


def _scan_level(x: int, y: int, scanners: list[tuple[int, int, int, int]]) -> str:
    """Determine the scan level for a position.

    Returns "detailed" if within any penetrating scanner range,
    "basic" if within any normal scanner range, or "none" otherwise.
    """
    best = "none"
    for sx, sy, sr_normal, sr_pen in scanners:
        dx = x - sx
        dy = y - sy
        dist_sq = dx * dx + dy * dy
        if sr_pen > 0 and dist_sq <= sr_pen * sr_pen:
            return "detailed"  # Can't do better than this
        if dist_sq <= sr_normal * sr_normal:
            best = "basic"
    return best


def _compute_bearing(fleet_x: int, fleet_y: int, wp_x: int, wp_y: int) -> float:
    """Compute bearing in degrees (0=north/up, clockwise) from fleet to waypoint."""
    dx = wp_x - fleet_x
    dy = wp_y - fleet_y
    # Screen coordinates: y increases downward, so north is -y
    # atan2 with (dx, -dy) gives 0=north, clockwise
    angle = math.degrees(math.atan2(dx, -dy))
    if angle < 0:
        angle += 360.0
    return round(angle, 1)


def derive_player_state(global_state: GlobalState, galaxy: Galaxy, username: str) -> PlayerState:
    """Create a fog-of-war-filtered player state.

    Rules (PRD 11):
    - All planets are always visible (name + position). Detail varies:
      - Own planets: "detailed" (full info)
      - Within penetrating scanner range: "detailed"
      - Within normal scanner range: "basic" (owner only)
      - Outside all scanner range: "none" (name + position only)
    - Own fleets: full detail (composition + waypoints)
    - Enemy fleets in normal scanner range: limited (owner, position, bearing)
    - Everything else: invisible
    """
    # Build galaxy planet lookup
    galaxy_planets = {gp.id: gp for gp in galaxy.planets}

    scanners = _scanner_positions(global_state, username)

    # All planets are always visible — determine detail level per planet
    visible_planets: list[PlayerPlanet] = []
    for ps in global_state.planets:
        gp = galaxy_planets.get(ps.id)
        if gp is None:
            continue

        is_own = ps.owner == username

        if is_own:
            mines_op = economy.mines_operated(ps.mines, ps.population)
            visible_planets.append(
                PlayerPlanet(
                    id=gp.id,
                    name=gp.name,
                    x=gp.x,
                    y=gp.y,
                    owner=ps.owner,
                    population=ps.population,
                    scan_level="detailed",
                    mines=ps.mines,
                    factories=ps.factories,
                    minerals=ps.minerals,
                    concentrations=ps.concentrations,
                    resources=global_state.planet_resources.get(ps.id),
                    mining_rate=economy.mining_rate(mines_op, ps.concentrations),
                    production_queue=[
                        PlayerProductionQueueItem(
                            id=item.id,
                            item_type=item.item_type,
                            quantity=item.quantity,
                            progress=item.progress.model_copy(deep=True),
                        )
                        for item in ps.production_queue
                    ],
                    habitability=ps.habitability,
                    max_population=max_population(ps.habitability),
                    pop_growth=global_state.pop_growth.get(ps.id),
                )
            )
        else:
            level = _scan_level(gp.x, gp.y, scanners)
            if level == "detailed":
                mines_op = economy.mines_operated(ps.mines, ps.population)
                visible_planets.append(
                    PlayerPlanet(
                        id=gp.id,
                        name=gp.name,
                        x=gp.x,
                        y=gp.y,
                        owner=ps.owner,
                        population=ps.population if ps.owner else None,
                        scan_level="detailed",
                        mines=ps.mines,
                        factories=ps.factories,
                        minerals=ps.minerals,
                        concentrations=ps.concentrations,
                        resources=global_state.planet_resources.get(ps.id),
                        mining_rate=economy.mining_rate(mines_op, ps.concentrations),
                        production_queue=None,
                        habitability=ps.habitability,
                    )
                )
            elif level == "basic":
                # Owner visible, no population detail
                visible_planets.append(
                    PlayerPlanet(
                        id=gp.id,
                        name=gp.name,
                        x=gp.x,
                        y=gp.y,
                        owner=ps.owner,
                        scan_level="basic",
                        production_queue=None,
                    )
                )
            else:
                # Outside scanner range — name and position only
                visible_planets.append(
                    PlayerPlanet(
                        id=gp.id,
                        name=gp.name,
                        x=gp.x,
                        y=gp.y,
                        scan_level="none",
                        production_queue=None,
                    )
                )

    # Determine visible fleets
    visible_fleets: list[PlayerFleet] = []
    designs_by_id = {d.id: d for d in global_state.designs}
    for fleet in global_state.fleets:
        if fleet.owner == username:
            # Full detail for own fleets
            visible_fleets.append(
                PlayerFleet(
                    id=fleet.id,
                    owner=fleet.owner,
                    position=fleet.position,
                    composition=fleet.composition,
                    waypoints=fleet.waypoints,
                    cargo=fleet.cargo,
                    cargo_capacity=fleet_cargo_capacity(fleet, designs_by_id),
                )
            )
        else:
            # Check if within normal scanner range
            level = _scan_level(fleet.position.x, fleet.position.y, scanners)
            if level != "none":
                # Compute bearing from fleet's first waypoint
                bearing = None
                if fleet.waypoints:
                    wp = fleet.waypoints[0]
                    if wp.x != fleet.position.x or wp.y != fleet.position.y:
                        bearing = _compute_bearing(fleet.position.x, fleet.position.y, wp.x, wp.y)
                visible_fleets.append(
                    PlayerFleet(
                        id=fleet.id,
                        owner=fleet.owner,
                        position=fleet.position,
                        bearing=bearing,
                    )
                )

    # Own designs only
    visible_designs = [d for d in global_state.designs if d.owner == username]

    player_events = list(global_state.events.get(username, []))

    return PlayerState(
        player=username,
        turn=global_state.game.turn,
        planets=visible_planets,
        fleets=visible_fleets,
        designs=visible_designs,
        events=player_events,
    )
