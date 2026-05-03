"""Command parser registry used by the server command-submission path."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from openstars.engine.models import PlanetState, PlayerCommand, ProductionQueueItem
from openstars.server.errors import GameError


@dataclass
class CommandParseContext:
    """Shared state needed while parsing one player's submitted command list."""

    username: str
    owned_fleet_ids: set[str]
    declared_tmp_fleet_ids: set[str]
    max_coord: int
    owned_planets: dict[str, PlanetState]
    queue_state_by_planet: dict[str, list[ProductionQueueItem]]
    player_design_ids: set[str]


CommandParser = Callable[[dict[str, Any], CommandParseContext], PlayerCommand]

COMMAND_PARSERS: dict[str, CommandParser] = {}


def register_command_parser(command_type: str, parser: CommandParser) -> None:
    """Register a parser for a submitted player command type."""
    existing = COMMAND_PARSERS.get(command_type)
    if existing is not None and existing is not parser:
        raise ValueError(f"Command parser already registered for {command_type!r}")
    COMMAND_PARSERS[command_type] = parser


def parse_registered_command(
    cmd_dict: dict[str, Any],
    ctx: CommandParseContext,
) -> PlayerCommand:
    """Parse one submitted command using the registered command-specific parser."""
    cmd_type = cmd_dict.get("type")
    if not isinstance(cmd_type, str):
        raise GameError(400, "UNKNOWN_COMMAND", f"Unknown command type: {cmd_type}")
    parser = COMMAND_PARSERS.get(cmd_type)
    if parser is None:
        raise GameError(400, "UNKNOWN_COMMAND", f"Unknown command type: {cmd_type}")
    return parser(cmd_dict, ctx)
