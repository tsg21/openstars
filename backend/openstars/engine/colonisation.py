"""Shared colonisation constants and helpers."""

from openstars.engine.models import Minerals

COLONY_SHIP_HULL = "colony_ship"
DISMANTLE_RECOVERY = 0.333
COLONY_SHIP_CONSTRUCTION_COST = Minerals(ironium=5, boranium=5, germanium=15)
# Use the explicit PRD table for recovered minerals. The documented 0.333
# recovery ratio rounds 15 germanium to 5 kT in the predefined colony ship.
COLONY_SHIP_RECOVERED_MINERALS = Minerals(
    ironium=1,
    boranium=1,
    germanium=5,
)


def recovered_minerals_for_colony_ships(count: int) -> Minerals:
    """Return dismantle recovery for ``count`` colony ships."""
    return Minerals(
        ironium=COLONY_SHIP_RECOVERED_MINERALS.ironium * count,
        boranium=COLONY_SHIP_RECOVERED_MINERALS.boranium * count,
        germanium=COLONY_SHIP_RECOVERED_MINERALS.germanium * count,
    )
