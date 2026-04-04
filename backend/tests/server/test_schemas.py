"""Tests for API schemas."""

import pytest
from pydantic import ValidationError

from openstars.server.schemas import (
    CreateGameRequest,
    ErrorResponse,
    SubmitCommandsRequest,
)


def test_create_game_request():
    req = CreateGameRequest(
        name="Test Game",
        galaxy_size="small",
        players=["tim", "matt"],
    )
    assert req.name == "Test Game"
    assert len(req.players) == 2


def test_create_game_allows_single_player():
    req = CreateGameRequest(
        name="Test Game",
        galaxy_size="small",
        players=["tim"],
    )
    assert req.players == ["tim"]


def test_create_game_rejects_no_players():
    with pytest.raises(ValidationError):
        CreateGameRequest(name="Test Game", galaxy_size="small", players=[])


def test_submit_commands_request():
    req = SubmitCommandsRequest(
        turn=3,
        commands=[{"type": "set_waypoints", "fleet_id": "FL123456", "waypoints": []}],
    )
    assert req.turn == 3


def test_rename_fleet_command_schema():
    from openstars.engine.models import PlayerCommands, RenameFleetCommand

    cmds = PlayerCommands(
        commands=[{"type": "rename_fleet", "fleet_id": "FL123456", "name": "Vanguard"}]
    )
    assert isinstance(cmds.commands[0], RenameFleetCommand)
    assert cmds.commands[0].name == "Vanguard"


def test_rename_fleet_command_empty_name_rejected():
    from pydantic import ValidationError

    from openstars.engine.models import PlayerCommands

    with pytest.raises(ValidationError):
        PlayerCommands(commands=[{"type": "rename_fleet", "fleet_id": "FL123456", "name": ""}])


def test_rename_fleet_command_long_name_rejected():
    from pydantic import ValidationError

    from openstars.engine.models import PlayerCommands

    with pytest.raises(ValidationError):
        PlayerCommands(
            commands=[{"type": "rename_fleet", "fleet_id": "FL123456", "name": "x" * 65}]
        )


def test_error_response():
    err = ErrorResponse(error={"code": "NOT_FOUND", "message": "Game not found"})  # type: ignore[arg-type]
    assert err.error.code == "NOT_FOUND"
