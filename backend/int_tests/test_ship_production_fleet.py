"""Integration test: custom ship design → production queue → new fleet at homeworld."""

from __future__ import annotations

from client import GameClient

from openstars.engine.models import AddProductionItemCommand

PLAYER_1 = "ship_prod_alice"
PLAYER_2 = "ship_prod_bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()

_VALID_SCOUT_COMPONENTS = [
    {"slot_number": 1, "component_id": "trans_galactic_drive", "component_count": 1},
    {"slot_number": 2, "component_id": "rhino_scanner", "component_count": 1},
]


class TestShipProductionCreatesFleet:
    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()

    def _submit_and_resolve(self, game_id: str, commands):
        state = client1.get_state(game_id)
        turn = state.turn
        client1.submit_commands(game_id, turn=turn, commands=commands)
        client2.submit_commands(game_id, turn=turn, commands=[])
        client1.resolve(game_id)

    def _fleet_ids_for_player(self, state, username: str) -> set[str]:
        return {f.id for f in state.fleets if f.owner == username}

    def test_new_design_production_creates_fleet(self):
        game = client_anon.create_game(
            name="Ship production integration game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        game_id = game.game_id

        design = client1.create_ship_design(
            game_id,
            name="Integration Scout Mk2",
            hull="scout",
            components=list(_VALID_SCOUT_COMPONENTS),
        )
        design_id = design["id"]

        state0 = client1.get_state(game_id)
        initial_fleet_ids = self._fleet_ids_for_player(state0, PLAYER_1)
        assert len(initial_fleet_ids) >= 1

        homeworld = next(p for p in state0.planets if p.owner == PLAYER_1)

        self._submit_and_resolve(
            game_id,
            [
                AddProductionItemCommand(
                    planet_id=homeworld.id,
                    item_type="ship",
                    design_id=design_id,
                    quantity=1,
                )
            ],
        )

        def fleet_with_new_design_present(st) -> bool:
            return any(
                f.owner == PLAYER_1
                and f.composition
                and any(c.design_id == design_id and c.count > 0 for c in f.composition)
                for f in st.fleets
            )

        state = client1.get_state(game_id)
        max_extra_turns = 40
        for _ in range(max_extra_turns):
            if fleet_with_new_design_present(state):
                break
            self._submit_and_resolve(game_id, [])
            state = client1.get_state(game_id)
        else:
            raise AssertionError(
                f"Ship design {design_id!r} did not complete within {max_extra_turns} turns"
            )

        matching = [
            f
            for f in state.fleets
            if f.owner == PLAYER_1
            and f.composition
            and any(c.design_id == design_id and c.count > 0 for c in f.composition)
        ]
        assert len(matching) == 1
        new_fleet = matching[0]
        assert new_fleet.id not in initial_fleet_ids
        assert new_fleet.position.x == homeworld.x
        assert new_fleet.position.y == homeworld.y
