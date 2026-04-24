"""Helpers for persisted state-file version handling."""

import json

from openstars.engine.models import STATE_VERSION
from openstars.engine.research.costs import FIELDS


class UnsupportedStateVersionError(ValueError):
    """Raised when a persisted state file uses an unsupported schema version."""


def load_state_payload(raw_json: str) -> dict:
    """Parse raw persisted JSON and ensure it is a JSON object."""
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise ValueError("Persisted state payload must be a JSON object")
    return payload


def _validated_state_version(payload: dict) -> int:
    version = payload.get("state_version")

    if version is None:
        raise UnsupportedStateVersionError("Persisted state file is missing required state_version")
    if not isinstance(version, int):
        raise UnsupportedStateVersionError("Persisted state file has invalid state_version")
    if version > STATE_VERSION:
        raise UnsupportedStateVersionError(
            "Persisted state file version "
            f"{version} is newer than supported version {STATE_VERSION}"
        )
    if version < 1:
        raise UnsupportedStateVersionError(
            f"Persisted state file version {version} is not supported"
        )

    return version


def upgrade_global_state_payload(payload: dict) -> dict:
    """Upgrade a global-state payload to the current version."""
    _validated_state_version(payload)
    # Designs were removed from GlobalState; ship designs live only in the per-player registry.
    payload.pop("designs", None)
    game = payload.get("game")
    if isinstance(game, dict) and "combat_ruleset" not in game:
        game["combat_ruleset"] = "altair"
    players = payload.get("players")
    if isinstance(players, list):
        for player in players:
            if not isinstance(player, dict):
                continue
            if "research_state" not in player:
                player["research_state"] = {
                    "levels": {field: 0 for field in FIELDS},
                    "progress": {field: 0 for field in FIELDS},
                    "current_field": "energy",
                    "next_field": None,
                    "allocation_percent": 15,
                }
    planets = payload.get("planets")
    if isinstance(planets, list):
        for planet in planets:
            if not isinstance(planet, dict):
                continue
            planet.setdefault("contribute_only_leftover_to_research", False)
    return payload


def upgrade_player_state_payload(payload: dict) -> dict:
    """Upgrade a player-state payload to the current version."""
    _validated_state_version(payload)
    return payload
