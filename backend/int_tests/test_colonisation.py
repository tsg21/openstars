"""Integration tests for colonisation over HTTP API."""

from client import GameClient

from openstars.engine.models import CargoOrder, SetWaypointsCommand, Waypoint, WaypointTask

PLAYER_1 = "colonize_alice"
PLAYER_2 = "colonize_bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()


class TestColonisation:
    game_id: str = ""
    colony_fleet_id: str = ""
    scout_fleet_id: str = ""
    home_xy: tuple[int, int] = (0, 0)
    target_xy: tuple[int, int] = (0, 0)
    target_planet_id: str = ""

    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()
        game = client_anon.create_game(
            name="Colonisation Integration Game",
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        cls.game_id = game.game_id

    def _state(self):
        return client1.get_state(self.game_id)

    def _fleet(self, state, fleet_id: str):
        return next(f for f in state.fleets if f.id == fleet_id)

    def _submit_and_resolve(self, commands):
        turn = self._state().turn
        client1.submit_commands(self.game_id, turn=turn, commands=commands)
        client2.submit_commands(self.game_id, turn=turn, commands=[])
        client1.resolve(self.game_id)

    def _find_first_unowned_planet(self, state):
        return next(
            p for p in state.planets if p.owner is None and p.x is not None and p.y is not None
        )

    def test_01_turn_0_has_colony_ship_design_and_fleet(self):
        state = self._state()
        designs = {d.id: d for d in state.designs}
        colony_designs = [d for d in state.designs if d.hull == "colony_ship"]
        assert colony_designs
        assert all(d.speed == 6 and d.cargo_capacity == 25 for d in colony_designs)

        self.colony_fleet_id = next(
            f.id
            for f in state.fleets
            if any(designs[c.design_id].hull == "colony_ship" for c in (f.composition or []))
        )
        self.scout_fleet_id = next(
            f.id
            for f in state.fleets
            if any(designs[c.design_id].hull == "scout" for c in (f.composition or []))
        )
        colony_fleet = self._fleet(state, self.colony_fleet_id)
        self.home_xy = (colony_fleet.position.x, colony_fleet.position.y)
        target = self._find_first_unowned_planet(state)
        self.target_xy = (target.x, target.y)
        self.target_planet_id = target.id

    def test_02_transport_then_colonize_unowned_planet(self):
        load_colonists = SetWaypointsCommand(
            fleet_id=self.colony_fleet_id,
            waypoints=[
                Waypoint(
                    x=self.home_xy[0],
                    y=self.home_xy[1],
                    task=WaypointTask(
                        type="transport",
                        orders=[
                            CargoOrder(
                                cargo_type="colonists",
                                action="load_amount",
                                amount=1400,
                            )
                        ],
                    ),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([load_colonists])
        state_after_load = self._state()
        assert self._fleet(state_after_load, self.colony_fleet_id).cargo.colonists == 1400

        colonize = SetWaypointsCommand(
            fleet_id=self.colony_fleet_id,
            waypoints=[
                Waypoint(
                    x=self.target_xy[0],
                    y=self.target_xy[1],
                    task=WaypointTask(type="colonize"),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([colonize])

        state = self._state()
        colonized = next(p for p in state.planets if p.id == self.target_planet_id)
        assert colonized.owner == PLAYER_1
        assert colonized.population == 1400
        assert all(f.id != self.colony_fleet_id for f in state.fleets)
        colonised_events = [
            e for e in state.events if e.type == "colonised" and e.planet_id == colonized.id
        ]
        assert colonised_events
        assert colonised_events[-1].colonists_landed == 1400
        assert colonised_events[-1].minerals_recovered is not None

    def test_03_non_colony_fleets_remain_after_colony_ship_dismantle(self):
        state = self._state()
        assert any(f.id == self.scout_fleet_id for f in state.fleets)

    def test_04_colonize_already_owned_emits_failure_reason(self):
        state = self._state()
        own_planet = next(p for p in state.planets if p.owner == PLAYER_1)
        command = SetWaypointsCommand(
            fleet_id=self.scout_fleet_id,
            waypoints=[
                Waypoint(
                    x=own_planet.x,
                    y=own_planet.y,
                    task=WaypointTask(type="colonize"),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([command])
        latest = self._state()
        failures = [e for e in latest.events if e.type == "colonize_failed"]
        assert failures
        assert failures[-1].reason == "planet_already_owned"

    def test_05_colonize_with_no_colonists_emits_failure_reason(self):
        state = self._state()
        designs_by_id = {d.id: d for d in state.designs}
        freighter = next(
            f
            for f in state.fleets
            if any(
                designs_by_id[c.design_id].hull == "small_freighter" for c in (f.composition or [])
            )
        )
        target = self._find_first_unowned_planet(state)
        command = SetWaypointsCommand(
            fleet_id=freighter.id,
            waypoints=[Waypoint(x=target.x, y=target.y, task=WaypointTask(type="colonize"))],
            repeat=False,
        )
        self._submit_and_resolve([command])
        latest = self._state()
        failures = [e for e in latest.events if e.type == "colonize_failed"]
        assert failures[-1].reason in {"no_colony_ship", "no_colonists"}

    def test_06_colonize_empty_space_emits_no_planet(self):
        state = self._state()
        scout = self._fleet(state, self.scout_fleet_id)
        command = SetWaypointsCommand(
            fleet_id=scout.id,
            waypoints=[
                Waypoint(
                    x=scout.position.x + 123_456_789,
                    y=scout.position.y + 987_654_321,
                    task=WaypointTask(type="colonize"),
                )
            ],
            repeat=False,
        )
        self._submit_and_resolve([command])
        latest = self._state()
        failures = [e for e in latest.events if e.type == "colonize_failed"]
        assert failures[-1].reason == "no_planet"
