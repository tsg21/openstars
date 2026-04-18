"""Apply jettison-cargo command."""

import logging
from typing import Any

from openstars.engine.models import Cargo, Fleet, JettisonCargoCommand
from openstars.server.errors import GameError

log = logging.getLogger(__name__)


def parse_jettison_cargo_command(
    cmd_dict: dict[str, Any],
    username: str,
    owned_fleet_ids: set[str],
    declared_tmp_fleet_ids: set[str],
) -> JettisonCargoCommand:
    fleet_id = cmd_dict.get("fleet_id")
    if not fleet_id:
        raise GameError(400, "MISSING_FLEET_ID", "Command missing fleet_id")
    if fleet_id not in owned_fleet_ids and fleet_id not in declared_tmp_fleet_ids:
        raise GameError(
            400,
            "FLEET_NOT_OWNED",
            f"Fleet {fleet_id} is not owned by player {username}",
        )

    return JettisonCargoCommand(
        fleet_id=fleet_id,
        cargo=Cargo.model_validate(cmd_dict.get("cargo", {})),
    )


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
