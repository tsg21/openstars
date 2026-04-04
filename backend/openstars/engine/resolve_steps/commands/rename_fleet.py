"""Apply rename-fleet command."""

import logging

from openstars.engine.models import Fleet, RenameFleetCommand

log = logging.getLogger(__name__)


def apply_rename_fleet_command(
    fleets_by_id: dict[str, Fleet],
    username: str,
    cmd: RenameFleetCommand,
) -> None:
    fleet = fleets_by_id.get(cmd.fleet_id)
    if fleet is None or fleet.owner != username:
        return

    log.debug("cmd rename_fleet: fleet=%s owner=%s name=%r", cmd.fleet_id, username, cmd.name)
    fleets_by_id[cmd.fleet_id] = fleet.model_copy(update={"name": cmd.name})
