"""Fog of war — derive player-visible state from global state (PRD 03/08)."""

from openstars.engine.models import (
    Galaxy,
    GlobalState,
    PlayerFleet,
    PlayerPlanet,
    PlayerState,
)

# 1 parsec = 2^29 coordinate units (PRD 07)
PARSEC = 1 << 29


def _scanner_positions(global_state: GlobalState, username: str) -> list[tuple[int, int, int]]:
    """Get all scanner positions and ranges for a player.

    Returns list of (x, y, range_coord_units) from the player's fleets.
    """
    # Build a lookup for design scanner ranges
    design_ranges: dict[str, int] = {}
    for d in global_state.designs:
        if d.owner == username:
            design_ranges[d.id] = d.scanner_range * PARSEC

    scanners = []
    for fleet in global_state.fleets:
        if fleet.owner != username:
            continue
        # Fleet scanner range = max scanner range of any design in composition
        max_range = 0
        for comp in fleet.composition:
            if comp.design_id in design_ranges:
                r = design_ranges[comp.design_id]
                if r > max_range:
                    max_range = r
        if max_range > 0:
            scanners.append((fleet.position.x, fleet.position.y, max_range))

    return scanners


def _in_scanner_range(x: int, y: int, scanners: list[tuple[int, int, int]]) -> bool:
    """Check if a position is within any scanner's range."""
    for sx, sy, sr in scanners:
        dx = x - sx
        dy = y - sy
        dist_sq = dx * dx + dy * dy
        if dist_sq <= sr * sr:
            return True
    return False


def derive_player_state(global_state: GlobalState, galaxy: Galaxy, username: str) -> PlayerState:
    """Create a fog-of-war-filtered player state.

    Rules:
    - Own planets: always visible with full detail
    - Other planets in scanner range: visible (limited detail)
    - Own fleets: full detail (composition + waypoints)
    - Enemy fleets in scanner range: limited (no composition/waypoints)
    - Everything else: invisible
    """
    # Build galaxy planet lookup
    galaxy_planets = {gp.id: gp for gp in galaxy.planets}
    {ps.id: ps for ps in global_state.planets}

    scanners = _scanner_positions(global_state, username)

    # Determine visible planets
    visible_planets: list[PlayerPlanet] = []
    for ps in global_state.planets:
        gp = galaxy_planets.get(ps.id)
        if gp is None:
            continue

        is_own = ps.owner == username
        in_range = _in_scanner_range(gp.x, gp.y, scanners)

        if is_own:
            # Full detail for own planets
            visible_planets.append(
                PlayerPlanet(
                    id=gp.id,
                    name=gp.name,
                    x=gp.x,
                    y=gp.y,
                    owner=ps.owner,
                    population=ps.population,
                )
            )
        elif in_range:
            # Visible but limited — show owner and population
            visible_planets.append(
                PlayerPlanet(
                    id=gp.id,
                    name=gp.name,
                    x=gp.x,
                    y=gp.y,
                    owner=ps.owner,
                    population=ps.population if ps.owner else None,
                )
            )

    # Determine visible fleets
    visible_fleets: list[PlayerFleet] = []
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
                )
            )
        elif _in_scanner_range(fleet.position.x, fleet.position.y, scanners):
            # Enemy fleet in range: limited info (no composition/waypoints)
            visible_fleets.append(
                PlayerFleet(
                    id=fleet.id,
                    owner=fleet.owner,
                    position=fleet.position,
                    composition=None,
                    waypoints=None,
                )
            )

    # Own designs only
    visible_designs = [d for d in global_state.designs if d.owner == username]

    return PlayerState(
        player=username,
        turn=global_state.game.turn,
        planets=visible_planets,
        fleets=visible_fleets,
        designs=visible_designs,
        events=[],  # Events are populated during turn resolution
    )
