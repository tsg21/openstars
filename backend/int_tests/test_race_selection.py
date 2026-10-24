"""Integration tests for turn-0 race selection over the HTTP API."""

from __future__ import annotations

import pytest
from client import GameAPIError, GameClient

from openstars.engine.models import (
    SelectRaceCommand,
    SetResearchCommand,
    SetWaypointsCommand,
    Waypoint,
)

PLAYER_1 = "race_alice@example.com"
PLAYER_2 = "race_bob@example.com"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)


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
        game = client1.create_game(
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
        assert saved["cost_breakdown"]["points_left"] == 25  # 53 - 28 (JOAT PRT cost)

        state = client1.get_state(game_id)
        assert state.turn == 1

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
        game = client1.create_game(
            name="Race Custom Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        game_id = game.game_id

        overspent_preview = client1.preview_race(_overspent_race())
        assert overspent_preview["points_left"] < 0

        valid_race = _base_race(
            max_growth_rate=10,
            economy={
                "colonists_per_resource": 900,
                "factory_output_per_10": 9,
                "factory_cost_resources": 11,
                "mine_output_per_10": 9,
            },
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

        state = client1.get_state(game_id)
        home = next(planet for planet in state.planets if planet.owner == PLAYER_1)
        assert home.population == 25_000
        assert state.race.name == "Pragmatist"
        assert state.race.economy.colonists_per_resource == 900

    def test_phase_enforcement(self):
        game = client1.create_game(
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

        assert client1.get_game(game_id).turn == 0

        client2.select_humanoid_race(game_id)
        assert client1.get_state(game_id).turn == 1

        with pytest.raises(GameAPIError) as exc_info:
            client1.submit_commands(
                game_id,
                turn=1,
                commands=[SelectRaceCommand(predefined_id="humanoid")],
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "COMMAND_NOT_VALID_AT_THIS_TURN"

    def test_economy_plumbing_uses_custom_factory_output(self):
        game = client1.create_game(
            name="Race Economy Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        game_id = game.game_id

        race = _base_race(
            max_growth_rate=10,
            economy={
                "factory_output_per_10": 12,
            },
        )
        client1.submit_commands(
            game_id,
            turn=0,
            commands=[SelectRaceCommand(race=race)],
        )
        client1.submit_commands(game_id, turn=1, commands=[])

        state = client1.get_state(game_id)
        assert state.race.economy.factory_output_per_10 == 12
        home = next(planet for planet in state.planets if planet.owner == PLAYER_1)
        # The state endpoint exposes the production budget after the default
        # 15% research reservation: total 37, reserved 5, budget 32.
        assert home.resources == 32

    def test_ife_custom_race_round_trip(self):
        game = client1.create_game(
            name="Race IFE Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        game_id = game.game_id

        ife_joat = _base_race(lrts=["IFE"], max_growth_rate=10)
        preview = client1.preview_race(ife_joat)
        assert preview["points_left"] >= 0
        assert preview["lrts"] == 78

        client1.submit_commands(
            game_id,
            turn=0,
            commands=[SelectRaceCommand(race=ife_joat)],
        )
        saved = client1.get_race(game_id)
        assert saved["race"]["lrts"] == ["IFE"]

        state = client1.get_state(game_id)
        assert "IFE" in state.race.lrts
        assert state.research.levels["propulsion"] == 3

        he_game = client1.create_game(
            name="Race HE IFE Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        he_game_id = he_game.game_id
        he_ife = _base_race(
            name="Sparse Expanders",
            plural_name="Sparse Expanders",
            prt="HE",
            lrts=["IFE"],
            max_growth_rate=10,
        )
        client1.submit_commands(
            he_game_id,
            turn=0,
            commands=[SelectRaceCommand(race=he_ife)],
        )
        he_state = client1.get_state(he_game_id)
        assert he_state.research.levels["propulsion"] == 1

    def test_ife_fuel_consumption_observable_end_to_end(self):
        non_ife_game = client1.create_game(
            name="Race Fuel Non IFE Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        ife_game = client1.create_game(
            name="Race Fuel IFE Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )

        non_ife_race = _base_race(max_growth_rate=10)
        ife_race = _base_race(lrts=["IFE"], max_growth_rate=10)
        client1.submit_commands(
            non_ife_game.game_id,
            turn=0,
            commands=[SelectRaceCommand(race=non_ife_race)],
        )
        client1.submit_commands(
            ife_game.game_id,
            turn=0,
            commands=[SelectRaceCommand(race=ife_race)],
        )
        non_ife_state = client1.get_state(non_ife_game.game_id)
        ife_state = client1.get_state(ife_game.game_id)
        non_ife_scout = next(fleet for fleet in non_ife_state.fleets if fleet.name == "Scout")
        ife_scout = next(fleet for fleet in ife_state.fleets if fleet.name == "Scout")

        client1.submit_commands(
            non_ife_game.game_id,
            turn=1,
            commands=[
                SetWaypointsCommand(
                    fleet_id=non_ife_scout.id,
                    waypoints=[
                        Waypoint(
                            x=non_ife_scout.position.x + 10 * 2**29,
                            y=non_ife_scout.position.y,
                            warp=6,
                        )
                    ],
                )
            ],
        )
        client1.submit_commands(
            ife_game.game_id,
            turn=1,
            commands=[
                SetWaypointsCommand(
                    fleet_id=ife_scout.id,
                    waypoints=[
                        Waypoint(
                            x=ife_scout.position.x + 10 * 2**29,
                            y=ife_scout.position.y,
                            warp=6,
                        )
                    ],
                )
            ],
        )
        moved_non_ife = next(
            fleet
            for fleet in client1.get_state(non_ife_game.game_id).fleets
            if fleet.id == non_ife_scout.id
        )
        moved_ife = next(
            fleet
            for fleet in client1.get_state(ife_game.game_id).fleets
            if fleet.id == ife_scout.id
        )
        non_ife_consumed = non_ife_scout.fuel - moved_non_ife.fuel
        ife_consumed = ife_scout.fuel - moved_ife.fuel

        assert moved_ife.fuel > moved_non_ife.fuel
        assert abs(ife_consumed - (non_ife_consumed * 85 // 100)) <= 1

    def test_ife_catalogue_restriction_enforced_server_side(self):
        no_ife_game = client1.create_game(
            name="Race Fuel Mizer No IFE Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        client1.submit_commands(
            no_ife_game.game_id,
            turn=0,
            commands=[SelectRaceCommand(race=_base_race(max_growth_rate=10))],
        )
        payload = {
            "name": "Fuel Mizer Scout",
            "hull": "scout",
            "components": [
                {"slot_number": 1, "component_id": "fuel_mizer", "component_count": 1},
                {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
            ],
        }
        with pytest.raises(GameAPIError) as exc_info:
            client1.create_ship_design(no_ife_game.game_id, **payload)
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "RACE_RESTRICTED"

        ife_game = client1.create_game(
            name="Race Fuel Mizer IFE Integration Game",
            galaxy_size="small",
            players=[PLAYER_1],
        )
        client1.submit_commands(
            ife_game.game_id,
            turn=0,
            commands=[SelectRaceCommand(race=_base_race(lrts=["IFE"], max_growth_rate=10))],
        )
        created = client1.create_ship_design(ife_game.game_id, **payload)
        assert created["components"][0]["component_id"] == "fuel_mizer"
