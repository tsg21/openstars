"""Fog of war — derive player-visible state from global state (PRD 03/11)."""

from openstars.engine.galaxy import LIGHT_YEAR
from openstars.engine.models import (
    Design,
    Galaxy,
    GlobalState,
    PlayerFleet,
    PlayerPlanet,
    PlayerPlanetScannerState,
    PlayerPlanetScannerSummary,
    PlayerPlanetStarbaseState,
    PlayerPlanetStarbaseSummary,
    PlayerProductionQueueItem,
    PlayerState,
)
from openstars.engine.research.costs import level_up_cost, total_levels
from openstars.engine.resolve_steps import economy
from openstars.engine.resolve_steps.freight import fleet_cargo_capacity, fleet_fuel_capacity
from openstars.engine.resolve_steps.population import max_population
from openstars.engine.resolve_steps.production import resolve_planetary_scanner_tier
from openstars.engine.util import compute_bearing


def _scanner_positions(
    global_state: GlobalState,
    username: str,
    designs: list[Design],
    galaxy: Galaxy,
) -> list[tuple[int, int, int, int]]:
    """Get all scanner positions and ranges for a player.

    Returns list of (x, y, normal_range_coord, pen_range_coord) from the
    player's fleets and planetary scanner installations.
    """
    # Build a lookup for design scanner ranges
    design_scanners: dict[str, tuple[int, int]] = {}
    for d in designs:
        if d.owner == username:
            design_scanners[d.id] = (
                d.scanner.normal * LIGHT_YEAR,
                d.scanner.penetrating * LIGHT_YEAR,
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

    scanner_tier = resolve_planetary_scanner_tier(electronics=0, biotechnology=0)
    normal_range_coord = scanner_tier[1] * LIGHT_YEAR
    penetrating_range_coord = scanner_tier[2] * LIGHT_YEAR
    galaxy_planets = {planet.id: planet for planet in galaxy.planets}
    for planet in global_state.planets:
        if planet.owner != username or not planet.has_scanner:
            continue
        static_planet = galaxy_planets.get(planet.id)
        if static_planet is None:
            continue
        scanners.append(
            (
                static_planet.x,
                static_planet.y,
                normal_range_coord,
                penetrating_range_coord,
            )
        )

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


def derive_player_state(
    global_state: GlobalState,
    galaxy: Galaxy,
    username: str,
    designs: list[Design],
    previous_player_state: PlayerState | None = None,
) -> PlayerState:
    """Create a fog-of-war-filtered player state.

    ``designs`` must list every ship design relevant to this game (typically the
    merged per-player design registry), not data from ``global_state``.

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
    prev_planets = (
        {planet.id: planet for planet in previous_player_state.planets}
        if previous_player_state is not None
        else {}
    )

    scanners = _scanner_positions(global_state, username, designs, galaxy)
    scanner_tier_name, scanner_normal, scanner_penetrating = resolve_planetary_scanner_tier(
        electronics=0,
        biotechnology=0,
    )

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
                            target_type=item.target_type,
                            design_id=item.design_id,
                            quantity=item.quantity,
                            progress=item.progress.model_copy(deep=True),
                        )
                        for item in ps.production_queue
                    ],
                    habitability=ps.habitability,
                    max_population=max_population(ps.habitability),
                    pop_growth=global_state.pop_growth.get(ps.id),
                    starbase=(
                        PlayerPlanetStarbaseState(
                            type=ps.starbase.type,
                            can_build_ships=ps.starbase.can_build_ships,
                        )
                        if ps.starbase is not None
                        else None
                    ),
                    scanner=(
                        PlayerPlanetScannerState(
                            installed=True,
                            name=scanner_tier_name,
                            normal=scanner_normal,
                            penetrating=scanner_penetrating,
                        )
                        if ps.has_scanner
                        else None
                    ),
                    contribute_only_leftover_to_research=ps.contribute_only_leftover_to_research,
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
                        starbase=(
                            PlayerPlanetStarbaseSummary(
                                present=True,
                                type=ps.starbase.type,
                                can_build_ships=ps.starbase.can_build_ships,
                            )
                            if ps.starbase is not None
                            else None
                        ),
                        scanner=(
                            PlayerPlanetScannerSummary(installed=True) if ps.has_scanner else None
                        ),
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
                        starbase=PlayerPlanetStarbaseSummary(present=ps.starbase is not None),
                        production_queue=None,
                    )
                )
            else:
                # Outside scanner range — name and position only
                previous_planet = prev_planets.get(gp.id)
                if previous_planet is not None and previous_planet.scan_level in {
                    "basic",
                    "detailed",
                }:
                    prev_age = previous_planet.scan_age
                    visible_planets.append(
                        previous_planet.model_copy(
                            update={
                                "scan_age": prev_age + 1,
                            },
                            deep=True,
                        )
                    )
                    continue
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
    designs_by_id = {d.id: d for d in designs}
    for fleet in global_state.fleets:
        if fleet.owner == username:
            # Full detail for own fleets
            visible_fleets.append(
                PlayerFleet(
                    id=fleet.id,
                    name=fleet.name,
                    owner=fleet.owner,
                    position=fleet.position,
                    composition=fleet.composition,
                    waypoints=fleet.waypoints,
                    cargo=fleet.cargo,
                    cargo_capacity=fleet_cargo_capacity(fleet, designs_by_id),
                    fuel=fleet.fuel,
                    fuel_capacity=fleet_fuel_capacity(fleet, designs_by_id),
                    bearing=fleet.bearing,
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
                        bearing = compute_bearing(fleet.position.x, fleet.position.y, wp.x, wp.y)
                visible_fleets.append(
                    PlayerFleet(
                        id=fleet.id,
                        owner=fleet.owner,
                        position=fleet.position,
                        bearing=bearing,
                    )
                )

    # Own designs only
    visible_designs = [d for d in designs if d.owner == username]

    player_events = list(global_state.events.get(username, []))

    player_obj = next(
        (player for player in global_state.players if player.username == username),
        None,
    )
    if player_obj is None:
        raise ValueError(f"unknown player {username}")
    research_state = player_obj.research_state
    current_level = research_state.levels[research_state.current_field]
    current_total_levels = total_levels(research_state.levels)
    estimated_resources_this_turn = 0
    for planet in global_state.planets:
        if planet.owner != username:
            continue
        total_resources = global_state.planet_resources.get(planet.id, 0)
        estimated_resources_this_turn += (
            total_resources * research_state.allocation_percent
        ) // 100

    return PlayerState(
        player=username,
        turn=global_state.game.turn,
        planets=visible_planets,
        fleets=visible_fleets,
        designs=visible_designs,
        events=player_events,
        research={
            "levels": research_state.levels,
            "progress": research_state.progress,
            "current_field": research_state.current_field,
            "next_field": research_state.next_field,
            "allocation_percent": research_state.allocation_percent,
            "current_field_remaining_cost": (
                0
                if current_level >= 26
                else max(
                    0,
                    level_up_cost(current_level, current_total_levels)
                    - research_state.progress[research_state.current_field],
                )
            ),
            "estimated_resources_this_turn": estimated_resources_this_turn,
        },
    )
