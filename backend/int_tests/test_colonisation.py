"""Integration tests for colonisation over HTTP API."""

from client import GameClient

from openstars.engine.models import CargoOrder, SetWaypointsCommand, Waypoint, WaypointTask

PLAYER_1 = "colonize_alice"
PLAYER_2 = "colonize_bob"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)
client_anon = GameClient()


def _new_game_id() -> str:
    game = client_anon.create_game(
        name="Colonisation Integration Game",
        galaxy_size="small",
        players=[PLAYER_1, PLAYER_2],
    )
    return game.game_id


def _state(game_id: str):
    return client1.get_state(game_id)


def _submit_and_resolve(game_id: str, commands):
    turn = _state(game_id).turn
    client1.submit_commands(game_id, turn=turn, commands=commands)
    client2.submit_commands(game_id, turn=turn, commands=[])
    client1.resolve(game_id)


def _run_until_waypoints_consumed(game_id: str, fleet_id: str, max_turns: int = 80):
    for _ in range(max_turns):
        state = _state(game_id)
        fleet = next((f for f in state.fleets if f.id == fleet_id), None)
        if fleet is None or not fleet.waypoints:
            return
        _submit_and_resolve(game_id, [])
    raise AssertionError(f"Fleet {fleet_id} still has waypoints after {max_turns} turns")


def _player_fleet_ids_by_hull(state) -> dict[str, str]:
    designs_by_id = {d.id: d for d in state.designs}
    fleets: dict[str, str] = {}
    for fleet in state.fleets:
        for comp in fleet.composition or []:
            hull = designs_by_id[comp.design_id].hull
            fleets.setdefault(hull, fleet.id)
    return fleets


def _first_unowned_planet(state):
    return next(p for p in state.planets if p.owner is None)


def _nearest_unowned_planet(state, x: int, y: int):
    return min(
        (p for p in state.planets if p.owner is None),
        key=lambda p: (p.x - x) ** 2 + (p.y - y) ** 2,
    )


class TestColonisation:
    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()

    def test_01_turn_0_has_colony_ship_design_and_fleet(self):
        game_id = _new_game_id()
        state = _state(game_id)
        hull_to_fleet = _player_fleet_ids_by_hull(state)
        colony_designs = [d for d in state.designs if d.hull == "colony_ship"]

        assert colony_designs
        assert all(d.speed == 6 and d.cargo_capacity == 25 for d in colony_designs)
        assert "colony_ship" in hull_to_fleet

    def test_02_transport_then_colonize_unowned_planet(self):
        game_id = _new_game_id()
        state = _state(game_id)
        hull_to_fleet = _player_fleet_ids_by_hull(state)
        colony_fleet_id = hull_to_fleet["colony_ship"]
        colony_fleet = next(f for f in state.fleets if f.id == colony_fleet_id)
        home_xy = (colony_fleet.position.x, colony_fleet.position.y)
        target = _nearest_unowned_planet(state, home_xy[0], home_xy[1])

        load_colonists = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[
                Waypoint(
                    x=home_xy[0],
                    y=home_xy[1],
                    task=WaypointTask(
                        type="transport",
                        orders=[
                            CargoOrder(cargo_type="colonists", action="load_amount", amount=1200),
                            CargoOrder(cargo_type="ironium", action="load_amount", amount=5),
                            CargoOrder(cargo_type="boranium", action="load_amount", amount=4),
                            CargoOrder(cargo_type="germanium", action="load_amount", amount=3),
                        ],
                    ),
                )
            ],
            repeat=False,
        )
        _submit_and_resolve(game_id, [load_colonists])

        colonize = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[Waypoint(x=target.x, y=target.y, task=WaypointTask(type="colonize"))],
            repeat=False,
        )
        _submit_and_resolve(game_id, [colonize])
        _run_until_waypoints_consumed(game_id, colony_fleet_id)

        post = _state(game_id)
        colonized = next(p for p in post.planets if p.id == target.id)
        assert colonized.owner == PLAYER_1
        assert colonized.population > 0
        assert all(f.id != colony_fleet_id for f in post.fleets)
        assert colonized.minerals.ironium >= 6
        assert colonized.minerals.boranium >= 5
        assert colonized.minerals.germanium >= 8

        colonised_events = [
            e for e in post.events if e.type == "colonised" and e.planet_id == target.id
        ]
        assert colonised_events
        assert colonised_events[-1].colonists_landed == 1200
        assert colonised_events[-1].minerals_recovered is not None

    def test_03_non_colony_fleets_remain_after_colony_ship_dismantle(self):
        game_id = _new_game_id()
        state = _state(game_id)
        hull_to_fleet = _player_fleet_ids_by_hull(state)
        colony_fleet_id = hull_to_fleet["colony_ship"]
        scout_fleet_id = hull_to_fleet["scout"]
        colony = next(f for f in state.fleets if f.id == colony_fleet_id)
        target = _nearest_unowned_planet(state, colony.position.x, colony.position.y)

        load = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[
                Waypoint(
                    x=colony.position.x,
                    y=colony.position.y,
                    task=WaypointTask(
                        type="transport",
                        orders=[
                            CargoOrder(
                                cargo_type="colonists",
                                action="load_amount",
                                amount=1000,
                            )
                        ],
                    ),
                )
            ],
            repeat=False,
        )
        _submit_and_resolve(game_id, [load])
        colonize = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[Waypoint(x=target.x, y=target.y, task=WaypointTask(type="colonize"))],
            repeat=False,
        )
        _submit_and_resolve(game_id, [colonize])
        _run_until_waypoints_consumed(game_id, colony_fleet_id)
        post = _state(game_id)
        assert any(f.id == scout_fleet_id for f in post.fleets)
        assert all(f.id != colony_fleet_id for f in post.fleets)

    def test_04_colonize_already_owned_emits_failure_reason(self):
        game_id = _new_game_id()
        state = _state(game_id)
        colony_fleet_id = _player_fleet_ids_by_hull(state)["colony_ship"]
        own_planet = next(p for p in state.planets if p.owner == PLAYER_1)

        command = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[
                Waypoint(
                    x=own_planet.x,
                    y=own_planet.y,
                    task=WaypointTask(type="colonize"),
                )
            ],
            repeat=False,
        )
        _submit_and_resolve(game_id, [command])
        _run_until_waypoints_consumed(game_id, colony_fleet_id)
        latest = _state(game_id)
        failures = [e for e in latest.events if e.type == "colonize_failed"]
        assert failures
        assert failures[-1].reason == "planet_already_owned"

    def test_05_colonize_with_no_colonists_emits_failure_reason(self):
        game_id = _new_game_id()
        state = _state(game_id)
        colony_fleet_id = _player_fleet_ids_by_hull(state)["colony_ship"]
        colony = next(f for f in state.fleets if f.id == colony_fleet_id)
        target = _nearest_unowned_planet(state, colony.position.x, colony.position.y)

        move_only = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[Waypoint(x=target.x, y=target.y)],
            repeat=False,
        )
        _submit_and_resolve(game_id, [move_only])
        _run_until_waypoints_consumed(game_id, colony_fleet_id)

        command = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[Waypoint(x=target.x, y=target.y, task=WaypointTask(type="colonize"))],
            repeat=False,
        )
        _submit_and_resolve(game_id, [command])
        latest = _state(game_id)
        failures = [e for e in latest.events if e.type == "colonize_failed"]
        assert failures
        assert failures[-1].reason == "no_colonists"

    def test_06_colonize_empty_space_emits_no_planet(self):
        game_id = _new_game_id()
        state = _state(game_id)
        colony_fleet_id = _player_fleet_ids_by_hull(state)["colony_ship"]
        colony = next(f for f in state.fleets if f.id == colony_fleet_id)

        command = SetWaypointsCommand(
            type="set_waypoints",
            fleet_id=colony_fleet_id,
            waypoints=[
                Waypoint(
                    x=colony.position.x + 123_456_789,
                    y=colony.position.y + 987_654_321,
                    task=WaypointTask(type="colonize"),
                )
            ],
            repeat=False,
        )
        _submit_and_resolve(game_id, [command])
        latest = _state(game_id)
        failures = [e for e in latest.events if e.type == "colonize_failed"]
        assert failures
        assert failures[-1].reason == "no_planet"
