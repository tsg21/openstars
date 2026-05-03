"""Integration tests for turn-0 race selection over the HTTP API."""

from __future__ import annotations

import pytest
from client import GameAPIError, GameClient

from openstars.engine.models import SelectRaceCommand, SetResearchCommand

PLAYER_1 = "race_alice"
PLAYER_2 = "race_bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()


def _assert_turn_zero_planet_is_public_shell(planet) -> None:
    assert planet.id
    assert planet.name
    assert isinstance(planet.x, int)
    assert isinstance(planet.y, int)
    assert planet.scan_level == "none"
    assert planet.scan_age == 0
    assert planet.owner is None
    assert planet.population is None
    assert planet.mines is None
    assert planet.factories is None
    assert planet.minerals is None
    assert planet.concentrations is None
    assert planet.resources is None
    assert planet.mining_rate is None
    assert planet.production_queue is None
    assert planet.habitability is None
    assert planet.max_population is None
    assert planet.pop_growth is None
    assert planet.starbase is None
    assert planet.scanner is None
    assert planet.contribute_only_leftover_to_research is None


def _base_race(**overrides) -> dict:
    race = {
        "name": "Pragmatist",
        "plural_name": "Pragmatists",
        "emblem": 1,
        "prt": "JOAT",
        "lrts": [],
        "habitability": {
            "gravity": {"immune": False, "range": [15, 85]},
            "temperature": {"immune": False, "range": [15, 85]},
            "radiation": {"immune": False, "range": [15, 85]},
        },
        "max_growth_rate": 15,
        "economy": {
            "colonists_per_resource": 1000,
            "factory_output_per_10": 10,
            "factory_cost_resources": 10,
            "factories_per_10k_colonists": 10,
            "factories_save_germanium": False,
            "mine_output_per_10": 10,
            "mine_cost_resources": 5,
            "mines_per_10k_colonists": 10,
            "ar_resource_divisor": 10,
        },
        "research": {
            "field_profile": {
                "energy": "standard",
                "weapons": "standard",
                "propulsion": "standard",
                "construction": "standard",
                "electronics": "standard",
                "biotechnology": "standard",
            },
            "start_at_tech_3": False,
        },
        "leftover_bonus": None,
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(race.get(key), dict):
            race[key] = {**race[key], **value}
        else:
            race[key] = value
    return race


def _overspent_race() -> dict:
    return _base_race(
        name="Extravagant",
        plural_name="Extravagants",
        habitability={
            "gravity": {"immune": True, "range": [15, 85]},
            "temperature": {"immune": True, "range": [15, 85]},
            "radiation": {"immune": True, "range": [15, 85]},
        },
        max_growth_rate=20,
        economy={
            "colonists_per_resource": 700,
            "factory_output_per_10": 15,
            "factory_cost_resources": 5,
            "mine_output_per_10": 25,
            "mine_cost_resources": 2,
        },
        research={
            "field_profile": {
                "energy": "cheap",
                "weapons": "cheap",
                "propulsion": "cheap",
                "construction": "cheap",
                "electronics": "cheap",
                "biotechnology": "cheap",
            },
            "start_at_tech_3": False,
        },
    )


class TestRaceSelection:
    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()

    def test_preset_selection_flow(self):
        game = client_anon.create_game(
            name="Race Preset Integration Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        game_id = game.game_id

        assert game.turn == 0

        for client, player in ((client1, PLAYER_1), (client2, PLAYER_2)):
            state = client.get_state(game_id)
            assert state.turn == 0
            assert state.player == player
            assert state.race is None
            assert state.fleets == []
            assert state.designs == []
            assert state.research is None
            assert len(state.planets) > 0
            for planet in state.planets:
                _assert_turn_zero_planet_is_public_shell(planet)

        assert client1.select_humanoid_race(game_id).command_count == 1
        assert client2.select_humanoid_race(game_id).command_count == 1

        saved = client1.get_race(game_id)
        assert saved["race"]["name"] == "Humanoid"
        assert saved["race"]["prt"] == "JOAT"
        assert saved["cost_breakdown"]["points_left"] == 1650

        resolved = client1.resolve(game_id)
        assert resolved.turn == 1
        assert resolved.status == "resolved"

        for client, player in ((client1, PLAYER_1), (client2, PLAYER_2)):
            state = client.get_state(game_id)
            home = next(planet for planet in state.planets if planet.owner == player)
            assert home.population == 25_000
            assert home.mines == 10
            assert home.factories == 10
            assert home.starbase is not None
            assert home.habitability.gravity == 50
            assert home.habitability.temperature == 50
            assert home.habitability.radiation == 50
            assert any(event.code == "race.saved" for event in state.events)

    def test_custom_race_round_trip(self):
        game = client_anon.create_game(
            name="Race Custom Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        game_id = game.game_id

        with pytest.raises(GameAPIError) as exc_info:
            client1.preview_race(_overspent_race())
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "RACE_OVERSPENT"

        valid_race = _base_race(
            economy={
                "colonists_per_resource": 900,
                "factory_output_per_10": 9,
                "factory_cost_resources": 11,
                "mine_output_per_10": 9,
            }
        )
        preview = client1.preview_race(valid_race)
        assert preview["points_left"] >= 0

        client1.submit_commands(
            game_id,
            turn=0,
            commands=[SelectRaceCommand(race=valid_race)],
        )
        saved = client1.get_race(game_id)
        assert saved["race"]["name"] == "Pragmatist"
        assert saved["race"]["economy"]["colonists_per_resource"] == 900
        assert saved["cost_breakdown"]["points_left"] >= 0

        client1.resolve(game_id)
        state = client1.get_state(game_id)
        home = next(planet for planet in state.planets if planet.owner == PLAYER_1)
        assert home.population == 25_000
        assert state.race.name == "Pragmatist"
        assert state.race.economy.colonists_per_resource == 900

    def test_phase_enforcement(self):
        game = client_anon.create_game(
            name="Race Phase Integration Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        game_id = game.game_id

        client1.select_humanoid_race(game_id)

        with pytest.raises(GameAPIError) as exc_info:
            client1.submit_commands(
                game_id,
                turn=0,
                commands=[SetResearchCommand(current_field="energy")],
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "COMMAND_TURN_ZERO_RACE_ONLY"

        with pytest.raises(GameAPIError) as exc_info:
            client1.resolve(game_id)
        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "TURN_ZERO_INCOMPLETE"
        assert PLAYER_2 in exc_info.value.message

        client2.select_humanoid_race(game_id)
        assert client1.resolve(game_id).turn == 1

        with pytest.raises(GameAPIError) as exc_info:
            client1.submit_commands(
                game_id,
                turn=1,
                commands=[SelectRaceCommand(predefined_id="humanoid")],
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "COMMAND_NOT_VALID_AT_THIS_TURN"

    def test_economy_plumbing_uses_custom_factory_output(self):
        game = client_anon.create_game(
            name="Race Economy Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        game_id = game.game_id

        race = _base_race(
            economy={
                "factory_output_per_10": 12,
            }
        )
        client1.submit_commands(
            game_id,
            turn=0,
            commands=[SelectRaceCommand(race=race)],
        )
        client1.resolve(game_id)
        client1.submit_commands(game_id, turn=1, commands=[])
        client1.resolve(game_id)

        state = client1.get_state(game_id)
        assert state.race.economy.factory_output_per_10 == 12
        home = next(planet for planet in state.planets if planet.owner == PLAYER_1)
        # The state endpoint exposes the production budget after the default
        # 15% research reservation: total 37, reserved 5, budget 32.
        assert home.resources == 32
