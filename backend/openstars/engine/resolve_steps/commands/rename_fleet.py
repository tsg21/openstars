"""Apply rename-fleet command."""

import logging
from typing import Any

from openstars.engine.models import Fleet, RenameFleetCommand
from openstars.server.errors import GameError

log = logging.getLogger(__name__)


def parse_rename_fleet_command(
    cmd_dict: dict[str, Any],
    username: str,
    owned_fleet_ids: set[str],
    declared_tmp_fleet_ids: set[str],
) -> RenameFleetCommand:
    fleet_id = cmd_dict.get("fleet_id")
    if not fleet_id:
        raise GameError(400, "MISSING_FLEET_ID", "Command missing fleet_id")
    if fleet_id not in owned_fleet_ids and fleet_id not in declared_tmp_fleet_ids:
        raise GameError(
            400,
            "FLEET_NOT_OWNED",
            f"Fleet {fleet_id} is not owned by player {username}",
        )

    name = cmd_dict.get("name", "")
    if not name or not isinstance(name, str) or len(name) > 64:
        raise GameError(
            400,
            "INVALID_FLEET_NAME",
            "Fleet name must be a non-empty string of at most 64 characters",
        )

    return RenameFleetCommand(fleet_id=fleet_id, name=name)


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
