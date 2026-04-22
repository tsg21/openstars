"""Integration test: combat resolves when fleets of different owners meet."""

from __future__ import annotations

from client import GameClient

from openstars.engine.models import SetWaypointsCommand, Waypoint

PLAYER_1 = "combat_alice"
PLAYER_2 = "combat_bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()


class TestCombatResolution:
    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()

    def _submit_and_resolve(
        self,
        game_id: str,
        commands_p1=None,
        commands_p2=None,
    ):
        turn = client1.get_state(game_id).turn
        client1.submit_commands(game_id, turn=turn, commands=commands_p1 or [])
        client2.submit_commands(game_id, turn=turn, commands=commands_p2 or [])
        client1.resolve(game_id)

    def _resolve_until(self, game_id: str, predicate, max_turns: int = 50):
        for _ in range(max_turns):
            state = client1.get_state(game_id)
            if predicate(state):
                return state
            self._submit_and_resolve(game_id)
        raise AssertionError(f"Predicate not met within {max_turns} turns")

    def _own_homeworld(self, state, owner: str):
        return next(planet for planet in state.planets if planet.owner == owner)

    def _scout_fleet(self, state):
        designs = {d.id: d for d in state.designs}
        return next(
            fleet
            for fleet in state.fleets
            if fleet.composition
            and any(designs[c.design_id].hull == "scout" for c in fleet.composition)
        )

    def test_fleets_meeting_triggers_combat_resolved_event(self):
        game = client_anon.create_game(
            name="Combat Integration Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        game_id = game.game_id

        state1 = client1.get_state(game_id)
        state2 = client2.get_state(game_id)
        scout1 = self._scout_fleet(state1)
        scout2 = self._scout_fleet(state2)
        home1 = self._own_homeworld(state1, PLAYER_1)
        home2 = self._own_homeworld(state2, PLAYER_2)

        meeting_x = (home1.x + home2.x) // 2
        meeting_y = (home1.y + home2.y) // 2
        meeting_point = Waypoint(x=meeting_x, y=meeting_y, warp=5)

        self._submit_and_resolve(
            game_id,
            commands_p1=[SetWaypointsCommand(fleet_id=scout1.id, waypoints=[meeting_point])],
            commands_p2=[SetWaypointsCommand(fleet_id=scout2.id, waypoints=[meeting_point])],
        )

        state = self._resolve_until(
            game_id,
            lambda s: any(event.code == "combat.resolved" for event in s.events),
        )

        combat_events = [event for event in state.events if event.code == "combat.resolved"]
        assert len(combat_events) >= 1
        event = combat_events[0]
        assert event.values, "combat.resolved event should carry battle metadata"
        battle_id = event.values[0]
        assert isinstance(battle_id, str) and battle_id.startswith("BT")
        # Third value is ships lost by this owner; scouts have no weapons so 0.
        assert event.values[2] == 0
