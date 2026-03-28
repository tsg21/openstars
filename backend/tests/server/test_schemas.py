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


def test_create_game_rejects_single_player():
    with pytest.raises(ValidationError):
        CreateGameRequest(
            name="Test Game",
            galaxy_size="small",
            players=["tim"],
        )


def test_submit_commands_request():
    req = SubmitCommandsRequest(
        turn=3,
        commands=[{"type": "set_waypoints", "fleet_id": "FL123456", "waypoints": []}],
    )
    assert req.turn == 3


def test_error_response():
    err = ErrorResponse(error={"code": "NOT_FOUND", "message": "Game not found"})  # type: ignore[arg-type]
    assert err.error.code == "NOT_FOUND"
