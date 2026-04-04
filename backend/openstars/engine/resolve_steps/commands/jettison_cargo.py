"""Apply jettison-cargo command."""

import logging

from openstars.engine.models import Fleet, JettisonCargoCommand

log = logging.getLogger(__name__)


def apply_jettison_cargo_command(
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
