"""Integration tests for freight transport over HTTP API."""

from client import GameClient

from openstars.engine.models import (
    Cargo,
    CargoOrder,
    JettisonCargoCommand,
    SetWaypointsCommand,
    Waypoint,
    WaypointTask,
)

PLAYER_1 = "freight_alice"
PLAYER_2 = "freight_bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()


class TestFreightTransport:
    game_id: str = ""
    freighter_id: str = ""
    scout_id: str = ""
    home_xy: tuple[int, int] = (0, 0)
    home_initial_ironium: int = 0

    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()
        game = client_anon.create_game(
            name="Freight Integration Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        cls.game_id = game.game_id
        client1.select_humanoid_race(cls.game_id)
        client2.select_humanoid_race(cls.game_id)
        client1.resolve(cls.game_id)

    def _state(self):
        return client1.get_state(self.game_id)

    def _fleet_by_id(self, state, fleet_id: str):
        return next(f for f in state.fleets if f.id == fleet_id)

    def _submit_and_resolve(self, commands):
        turn = self._state().turn
        client1.submit_commands(self.game_id, turn=turn, commands=commands)
        client2.submit_commands(self.game_id, turn=turn, commands=[])
        client1.resolve(self.game_id)

    def _step_turn0_has_small_freighter_with_owner_cargo_fields(self):
        state = self._state()
        designs = {d.id: d for d in state.designs}
        own_fleets = list(state.fleets)
        freighter = next(
            f
            for f in own_fleets
            if any(designs[c.design_id].hull == "medium_freighter" for c in (f.composition or []))
        )
        scout = next(
            f
            for f in own_fleets
            if any(designs[c.design_id].hull == "scout" for c in (f.composition or []))
        )
        assert freighter.cargo is not None
        assert freighter.cargo_capacity == 210
        TestFreightTransport.freighter_id = freighter.id
        TestFreightTransport.scout_id = scout.id
        TestFreightTransport.home_xy = (freighter.position.x, freighter.position.y)
        home = next(
            p
            for p in state.planets
            if p.owner == PLAYER_1 and p.x == self.home_xy[0] and p.y == self.home_xy[1]
        )
        TestFreightTransport.home_initial_ironium = home.minerals.ironium

    def _step_transport_load_from_planet(self):
        command = SetWaypointsCommand(
            fleet_id=self.freighter_id,
            waypoints=[
                Waypoint(
                    x=self.home_xy[0],
                    y=self.home_xy[1],
                    task=WaypointTask(
                        type="transport",
                        orders=[CargoOrder(cargo_type="ironium", action="load_amount", amount=20)],
                    ),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([command])

        state = self._state()
        fleet = self._fleet_by_id(state, self.freighter_id)
        home = next(
            p
            for p in state.planets
            if p.owner == PLAYER_1 and p.x == self.home_xy[0] and p.y == self.home_xy[1]
        )
        assert fleet.cargo.ironium >= 20
        assert home.minerals.ironium == self.home_initial_ironium - 20 + home.mining_rate.ironium

    def _step_transport_unload_to_planet(self):
        command = SetWaypointsCommand(
            fleet_id=self.freighter_id,
            waypoints=[
                Waypoint(
                    x=self.home_xy[0],
                    y=self.home_xy[1],
                    task=WaypointTask(
                        type="transport",
                        orders=[CargoOrder(cargo_type="ironium", action="unload_amount", amount=5)],
                    ),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([command])

        state = self._state()
        fleet = self._fleet_by_id(state, self.freighter_id)
        home = next(
            p
            for p in state.planets
            if p.owner == PLAYER_1 and p.x == self.home_xy[0] and p.y == self.home_xy[1]
        )
        assert fleet.cargo.ironium >= 15
        assert home.minerals.ironium >= 285

    def _step_load_is_capped_at_capacity(self):
        command = SetWaypointsCommand(
            fleet_id=self.freighter_id,
            waypoints=[
                Waypoint(
                    x=self.home_xy[0],
                    y=self.home_xy[1],
                    task=WaypointTask(
                        type="transport",
                        orders=[
                            CargoOrder(
                                cargo_type="boranium",
                                action="load_amount",
                                amount=500,
                            )
                        ],
                    ),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([command])
        fleet = self._fleet_by_id(self._state(), self.freighter_id)
        total_load = (
            fleet.cargo.ironium
            + fleet.cargo.boranium
            + fleet.cargo.germanium
            + ((fleet.cargo.colonists + 99) // 100)
        )
        assert total_load <= fleet.cargo_capacity

    def _step_repeat_route_executes_again(self):
        command = SetWaypointsCommand(
            fleet_id=self.freighter_id,
            waypoints=[
                Waypoint(
                    x=self.home_xy[0],
                    y=self.home_xy[1],
                    task=WaypointTask(
                        type="transport",
                        orders=[
                            CargoOrder(cargo_type="boranium", action="unload_amount", amount=2),
                            CargoOrder(cargo_type="germanium", action="load_amount", amount=2),
                        ],
                    ),
                )
            ],
            repeat=True,
        )
        self._submit_and_resolve([command])
        first = self._fleet_by_id(self._state(), self.freighter_id).cargo.germanium

        self._submit_and_resolve([command])
        second = self._fleet_by_id(self._state(), self.freighter_id).cargo.germanium
        assert second >= first + 2

    def _step_jettison_cargo(self):
        current = self._fleet_by_id(self._state(), self.freighter_id).cargo.ironium
        # Move freighter off-planet first so jettison is valid.
        move = SetWaypointsCommand(
            fleet_id=self.freighter_id,
            waypoints=[Waypoint(x=self.home_xy[0] + 3_000_000_000, y=self.home_xy[1])],
            repeat=False,
        )
        self._submit_and_resolve([move])

        jet = JettisonCargoCommand(
            fleet_id=self.freighter_id,
            cargo=Cargo(ironium=3),
        )
        self._submit_and_resolve([jet])
        after = self._fleet_by_id(self._state(), self.freighter_id).cargo.ironium
        assert after == max(current - 3, 0)

    def _step_transfer_between_colocated_fleets(self):
        freighter = self._fleet_by_id(self._state(), self.freighter_id)
        attempts = 0
        while (freighter.position.x, freighter.position.y) != self.home_xy:
            move_home = SetWaypointsCommand(
                fleet_id=self.freighter_id,
                waypoints=[Waypoint(x=self.home_xy[0], y=self.home_xy[1])],
                repeat=False,
            )
            self._submit_and_resolve([move_home])
            freighter = self._fleet_by_id(self._state(), self.freighter_id)
            attempts += 1
            assert attempts <= 10

        scout = self._fleet_by_id(self._state(), self.scout_id)
        transfer = SetWaypointsCommand(
            fleet_id=self.scout_id,
            waypoints=[
                Waypoint(
                    x=scout.position.x,
                    y=scout.position.y,
                    task=WaypointTask(
                        type="transfer",
                        fleet_id=self.freighter_id,
                        orders=[CargoOrder(cargo_type="ironium", action="unload_amount", amount=1)],
                    ),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([transfer])

        state = self._state()
        source = self._fleet_by_id(state, self.freighter_id)
        target = self._fleet_by_id(state, self.scout_id)
        assert target.cargo.ironium >= 1
        assert source.cargo.ironium >= 0

    def test_freight_transport_scenario(self):
        self._step_turn0_has_small_freighter_with_owner_cargo_fields()
        self._step_transport_load_from_planet()
        self._step_transport_unload_to_planet()
        self._step_load_is_capped_at_capacity()
        self._step_repeat_route_executes_again()
        self._step_jettison_cargo()
        self._step_transfer_between_colocated_fleets()
