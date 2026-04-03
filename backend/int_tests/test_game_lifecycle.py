"""Integration test: full game lifecycle over the running backend container.

Covers: create game → get galaxy → get state → submit commands → resolve turn.
"""

import pytest
from client import GameAPIError, GameClient

from openstars.engine.models import AddProductionItemCommand, SetWaypointsCommand, Waypoint

PLAYER_1 = "alice"
PLAYER_2 = "bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()


class TestGameLifecycle:
    """Walk through a full game turn."""

    game_id: str = ""

    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()

    # -- 1. Create game --

    def test_01_create_game(self):
        game = client_anon.create_game(
            name="Integration Test Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        assert game.name == "Integration Test Game"
        assert game.turn == 0
        assert len(game.players) == 2
        assert game.game_id
        TestGameLifecycle.game_id = game.game_id

    # -- 2. List games --

    def test_02_list_games(self):
        response = client_anon.list_games()
        assert any(g.game_id == self.game_id for g in response.games)

    # -- 3. Get game detail --

    def test_03_get_game_detail(self):
        game = client1.get_game(self.game_id)
        assert game.turn == 0
        assert len(game.players) == 2
        for p in game.players:
            assert p.submitted is False

    # -- 4. Get galaxy --

    def test_04_get_galaxy(self):
        galaxy = client1.get_galaxy(self.game_id)
        assert len(galaxy.planets) > 0
        assert galaxy.galaxy.size == "small"

    # -- 5. Get player state (turn 0) --

    def test_05_get_player_state(self):
        state = client1.get_state(self.game_id)
        assert state.turn == 0
        assert len(state.fleets) > 0
        assert len(state.planets) > 0
        TestGameLifecycle.fleet_id = state.fleets[0].id
        TestGameLifecycle.fleet_pos = state.fleets[0].position

    # -- 6. Both players forbidden from seeing each other's state --

    def test_06_non_participant_rejected(self):
        eve = GameClient(player="eve")
        with pytest.raises(GameAPIError) as exc_info:
            eve.get_state(self.game_id)
        assert exc_info.value.status_code == 403

    # -- 7. Submit commands (player 1: set waypoints) --

    def test_07_submit_commands_player1(self):
        pos = self.fleet_pos
        cmd = SetWaypointsCommand(
            fleet_id=self.fleet_id,
            waypoints=[Waypoint(x=pos.x + 1000, y=pos.y + 1000)],
        )
        result = client1.submit_commands(self.game_id, turn=0, commands=[cmd])
        assert result.command_count == 1

    # -- 8. Get submitted commands back --

    def test_08_get_commands(self):
        body = client1.get_commands(self.game_id)
        assert body["turn"] == 0
        assert len(body["commands"]) == 1

    # -- 9. Resolve fails if not all submitted --

    def test_09_resolve_fails_not_all_submitted(self):
        with pytest.raises(GameAPIError) as exc_info:
            client1.resolve(self.game_id)
        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "NOT_ALL_SUBMITTED"

    # -- 10. Submit commands (player 2: empty) --

    def test_10_submit_commands_player2(self):
        result = client2.submit_commands(self.game_id, turn=0, commands=[])
        assert result.command_count == 0

    # -- 11. Resolve succeeds --

    def test_11_resolve_turn(self):
        result = client1.resolve(self.game_id)
        assert result.turn == 1
        assert result.status == "resolved"

    # -- 12. Verify turn advanced --

    def test_12_state_after_resolve(self):
        state = client1.get_state(self.game_id)
        assert state.turn == 1

    # -- 13. Game detail shows turn 1, no submissions --

    def test_13_game_detail_after_resolve(self):
        game = client1.get_game(self.game_id)
        assert game.turn == 1
        for p in game.players:
            assert p.submitted is False

    # -- 14. Economy fields present on own planet at turn 0 --

    def test_14_home_planet_economy_at_turn_0(self):
        # Re-fetch turn-0 state isn't possible post-resolve, so we check turn-1
        # state — the home planet fields should always be present for own planets.
        state = client1.get_state(self.game_id)
        own = next((p for p in state.planets if p.owner == PLAYER_1), None)
        assert own is not None, "Own planet not found in player state"
        assert own.scan_level == "detailed"

        assert own.concentrations is not None, "concentrations missing from own planet"
        for mineral in ("ironium", "boranium", "germanium"):
            val = getattr(own.concentrations, mineral)
            assert 1 <= val <= 200, f"{mineral} concentration out of range"
            assert val >= 30, f"Home planet {mineral} concentration below floor"

        assert own.minerals is not None, "minerals missing from own planet"
        for mineral in ("ironium", "boranium", "germanium"):
            assert getattr(own.minerals, mineral) >= 300, f"Surface {mineral} below initial 300 kT"

        assert own.resources is not None, "resources missing from own planet"
        assert own.resources > 0

        assert own.mining_rate is not None, "mining_rate missing from own planet"

    # -- 15. Economy fields absent on unscanned planets --

    def test_15_unscanned_planets_have_no_economy(self):
        state = client1.get_state(self.game_id)
        unscanned = [p for p in state.planets if p.scan_level == "none"]
        for p in unscanned:
            assert p.concentrations is None
            assert p.minerals is None
            assert p.resources is None
            assert p.mining_rate is None

    # -- 16. Submit production command on turn 1 --

    def test_16_submit_production_turn_1(self):
        state = client1.get_state(self.game_id)
        own_planet = next((p for p in state.planets if p.owner == PLAYER_1), None)
        assert own_planet is not None, "Own planet not found in player state"

        result = client1.submit_commands(
            self.game_id,
            turn=1,
            commands=[
                AddProductionItemCommand(
                    planet_id=own_planet.id,
                    item_type="mine",
                    quantity=1,
                )
            ],
        )
        assert result.command_count == 1

        result_other = client2.submit_commands(self.game_id, turn=1, commands=[])
        assert result_other.command_count == 0

    # -- 17. Resolve turn 1 -> 2 --

    def test_17_resolve_turn_again(self):
        result = client1.resolve(self.game_id)
        assert result.turn == 2
        assert result.status == "resolved"

    # -- 18. Event envelope contains mining + production code families --

    def test_18_events_use_generic_code_values_envelope(self):
        state = client1.get_state(self.game_id)
        assert state.turn == 2
        assert len(state.events) > 0

        for event in state.events:
            assert isinstance(event.owner, str)
            assert isinstance(event.code, str)
            assert isinstance(event.values, list)

        codes = {event.code for event in state.events}
        assert "mining.complete" in codes
        assert "production.completed" in codes
