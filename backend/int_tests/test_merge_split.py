"""Integration tests for merge/split fleet commands."""

import pytest
from client import GameClient

from openstars.engine.models import (
    FleetComposition,
    MergeSplitFleetEntry,
    MergeSplitFleetsCommand,
    SetWaypointsCommand,
    Waypoint,
)

PLAYER_1 = "merge_tim@example.com"
PLAYER_2 = "merge_sara@example.com"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)


class TestMergeSplit:
    game_id: str = ""

    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()
        game = client1.create_game(
            name="Merge/Split Integration Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        cls.game_id = game.game_id
        client1.select_humanoid_race(cls.game_id)
        client2.select_humanoid_race(cls.game_id)

    def _state(self):
        return client1.get_state(self.game_id)

    def _submit_and_resolve(self, commands):
        turn = self._state().turn
        client1.submit_commands(self.game_id, turn=turn, commands=commands)
        client2.submit_commands(self.game_id, turn=turn, commands=[])

    def test_merge_split_and_tmp_waypoint(self):
        state = self._state()
        own = list(state.fleets)
        assert len(own) >= 2
        first = own[0]
        second = own[1]

        merge = MergeSplitFleetsCommand(
            fleets=[
                MergeSplitFleetEntry(
                    fleet_id=first.id,
                    ships=[
                        FleetComposition(design_id=c.design_id, count=c.count)
                        for c in (first.composition or [])
                    ],
                ),
                MergeSplitFleetEntry(
                    fleet_id="tmp_1",
                    ships=[
                        FleetComposition(design_id=c.design_id, count=c.count)
                        for c in (second.composition or [])
                    ],
                ),
                MergeSplitFleetEntry(fleet_id=second.id, ships=[]),
            ]
        )
        set_wp = SetWaypointsCommand(
            fleet_id="tmp_1", waypoints=[Waypoint(x=first.position.x, y=first.position.y, warp=5)]
        )

        self._submit_and_resolve([merge, set_wp])
        after = self._state()
        fleets_here = [
            f
            for f in after.fleets
            if f.position.x == first.position.x and f.position.y == first.position.y
        ]
        assert len(fleets_here) >= 2
        assert all(not f.id.startswith("tmp_") for f in fleets_here)

    def test_invalid_ship_totals_rejected(self):
        state = self._state()
        fleet = state.fleets[0]

        bad = MergeSplitFleetsCommand(
            fleets=[
                MergeSplitFleetEntry(
                    fleet_id=fleet.id,
                    ships=[
                        FleetComposition(design_id=(fleet.composition or [])[0].design_id, count=99)
                    ],
                )
            ]
        )

        turn = state.turn
        client1.submit_commands(self.game_id, turn=turn, commands=[bad])
        with pytest.raises(Exception):
            client2.submit_commands(self.game_id, turn=turn, commands=[])
