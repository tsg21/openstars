"""Fleet movement using integer arithmetic (PRD 07).

1 parsec = 2^29 coordinate units.
All computation is integer-only — no floating point.
"""

from openstars.engine.models import Fleet, Position
from openstars.engine.util import isqrt

# 1 parsec = 2^29 coordinate units (PRD 07)
PARSEC = 1 << 29


def move_fleet(fleet: Fleet, designs_speed: dict[str, int]) -> Fleet:
    """Move a fleet toward its waypoints for one turn.

    Args:
        fleet: The fleet to move.
        designs_speed: Mapping of design_id → speed in parsecs.

    Returns:
        Updated fleet with new position and consumed waypoints.
    """
    if not fleet.waypoints:
        return fleet

    # Fleet speed = slowest design in composition (parsecs/turn)
    speed = min(designs_speed.get(comp.design_id, 0) for comp in fleet.composition)
    if speed <= 0:
        return fleet

    # Movement budget in coordinate units
    budget = speed * PARSEC

    # Current position (mutable copy)
    fx = fleet.position.x
    fy = fleet.position.y
    waypoints = list(fleet.waypoints)

    while budget > 0 and waypoints:
        wp = waypoints[0]
        dx = wp.x - fx
        dy = wp.y - fy
        dist_sq = dx * dx + dy * dy

        if dist_sq == 0:
            # Already at waypoint
            waypoints.pop(0)
            continue

        dist = isqrt(dist_sq)

        if dist <= budget:
            # Fleet arrives at waypoint
            fx = wp.x
            fy = wp.y
            budget -= dist
            waypoints.pop(0)
        else:
            # Fleet moves toward waypoint (doesn't reach it)
            fx = fx + (dx * budget) // dist
            fy = fy + (dy * budget) // dist
            budget = 0

    return Fleet(
        id=fleet.id,
        owner=fleet.owner,
        position=Position(x=fx, y=fy),
        composition=fleet.composition,
        waypoints=[Position(x=wp.x, y=wp.y) for wp in waypoints],
    )
