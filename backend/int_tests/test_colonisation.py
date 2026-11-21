"""Integration tests for colonisation over the HTTP API."""

from __future__ import annotations

import math

from client import GameClient

from openstars.engine.models import CargoOrder, SetWaypointsCommand, Waypoint, WaypointTask

PLAYER_1 = "colonise_alice@example.com"
PLAYER_2 = "colonise_bob@example.com"

client1 = GameClient(player=PLAYER_1)
client2 = GameClient(player=PLAYER_2)


class TestColonisation:
    @classmethod
    def setup_class(cls):
        client1.wait_for_backend()

    def _create_game(self, name: str) -> str:
        game = client1.create_game(
            name=name,
            galaxy_size="small",
            players=[PLAYER_1, PLAYER_2],
        )
        client1.select_humanoid_race(game.game_id)
        client2.select_humanoid_race(game.game_id)
        return game.game_id

    def _state(self, game_id: str):
        return client1.get_state(game_id)

    def _submit_and_resolve(self, game_id: str, commands):
        turn = self._state(game_id).turn
        client1.submit_commands(game_id, turn=turn, commands=commands)
        client2.submit_commands(game_id, turn=turn, commands=[])
        return self._state(game_id)

    def _resolve_until(self, game_id: str, predicate, max_turns: int = 200):
        state = self._state(game_id)
        for _ in range(max_turns):
            if predicate(state):
                return state
            state = self._submit_and_resolve(game_id, [])
        raise AssertionError("Colonisation scenario did not resolve within max_turns")

    def _fleet_for_hull(self, state, hull: str):
        designs = {d.id: d for d in state.designs}
        return next(
            fleet
            for fleet in state.fleets
            if fleet.composition
            and any(designs[comp.design_id].hull == hull for comp in fleet.composition)
        )

    def _own_homeworld(self, state):
        return next(planet for planet in state.planets if planet.owner == PLAYER_1)

    def _closest_unowned_planet(self, state, x: int, y: int):
        return min(
            (planet for planet in state.planets if planet.owner is None),
            key=lambda planet: math.dist((x, y), (planet.x, planet.y)),
        )

    def test_successful_colonisation_over_http(self):
        game_id = self._create_game("Colonisation Success")
        state = self._state(game_id)
        colony_fleet = self._fleet_for_hull(state, "colony_ship")
        home = self._own_homeworld(state)
        target = self._closest_unowned_planet(state, home.x, home.y)

        command = SetWaypointsCommand(
            fleet_id=colony_fleet.id,
            waypoints=[
                Waypoint(
                    x=home.x,
                    y=home.y,
                    task=WaypointTask(
                        type="transport",
                        orders=[CargoOrder(cargo_type="colonists", action="load_all")],
                    ),
                ),
                Waypoint(
                    x=target.x,
                    y=target.y,
                    task=WaypointTask(type="colonise"),
                ),
            ],
        )

        state = self._submit_and_resolve(game_id, [command])
        state = self._resolve_until(
            game_id,
            lambda current: any(
                event.code == "colonisation.colonised" and event.source_id == target.id
                for event in current.events
            ),
        )

        colonised = next(planet for planet in state.planets if planet.id == target.id)
        assert colonised.owner == PLAYER_1
        assert colonised.population > 0
        assert colonised.minerals is not None
        assert colonised.minerals.ironium >= 1
        assert colonised.minerals.boranium >= 1
        assert colonised.minerals.germanium >= 5
        assert all(fleet.id != colony_fleet.id for fleet in state.fleets)

    def test_colonise_failed_no_planet(self):
        game_id = self._create_game("Colonisation No Planet")
        state = self._state(game_id)
        colony_fleet = self._fleet_for_hull(state, "colony_ship")
        home = self._own_homeworld(state)

        command = SetWaypointsCommand(
            fleet_id=colony_fleet.id,
            waypoints=[
                Waypoint(
                    x=home.x,
                    y=home.y,
                    task=WaypointTask(
                        type="transport",
                        orders=[CargoOrder(cargo_type="colonists", action="load_all")],
                    ),
                ),
                Waypoint(
                    x=home.x + 1,
                    y=home.y + 1,
                    task=WaypointTask(type="colonise"),
                ),
            ],
        )

        state = self._submit_and_resolve(game_id, [command])
        failure = next(event for event in state.events if event.code == "colonisation.failed")
        assert failure.source_id is None
        assert failure.values[-1] == "no_planet"

    def test_colonise_failed_planet_already_owned(self):
        game_id = self._create_game("Colonisation Already Owned")
        state = self._state(game_id)
        colony_fleet = self._fleet_for_hull(state, "colony_ship")
        home = self._own_homeworld(state)

        command = SetWaypointsCommand(
            fleet_id=colony_fleet.id,
            waypoints=[
                Waypoint(
                    x=home.x,
                    y=home.y,
                    task=WaypointTask(
                        type="transport",
                        orders=[CargoOrder(cargo_type="colonists", action="load_all")],
                    ),
                ),
                Waypoint(
                    x=home.x,
                    y=home.y,
                    task=WaypointTask(type="colonise"),
                ),
            ],
        )

        state = self._submit_and_resolve(game_id, [command])
        failure = next(event for event in state.events if event.code == "colonisation.failed")
        assert failure.source_id == home.id
        assert failure.values[-1] == "planet_already_owned"
        assert any(fleet.id == colony_fleet.id for fleet in state.fleets)

    def test_colonise_failed_no_colony_ship(self):
        game_id = self._create_game("Colonisation No Colony Ship")
        state = self._state(game_id)
        freighter = self._fleet_for_hull(state, "medium_freighter")
        home = self._own_homeworld(state)
        target = self._closest_unowned_planet(state, home.x, home.y)

        command = SetWaypointsCommand(
            fleet_id=freighter.id,
            waypoints=[
                Waypoint(
                    x=home.x,
                    y=home.y,
                    task=WaypointTask(
                        type="transport",
                        orders=[CargoOrder(cargo_type="colonists", action="load_all")],
                    ),
                ),
                Waypoint(
                    x=target.x,
                    y=target.y,
                    task=WaypointTask(type="colonise"),
                ),
            ],
        )

        state = self._submit_and_resolve(game_id, [command])
        state = self._resolve_until(
            game_id,
            lambda current: any(
                event.code == "colonisation.failed" and event.values[-1] == "no_colony_ship"
                for event in current.events
            ),
        )
        failure = next(event for event in state.events if event.code == "colonisation.failed")
        assert failure.source_id == target.id
        assert failure.values[-1] == "no_colony_ship"

    def test_colonise_failed_no_colonists(self):
        game_id = self._create_game("Colonisation No Colonists")
        state = self._state(game_id)
        colony_fleet = self._fleet_for_hull(state, "colony_ship")
        home = self._own_homeworld(state)
        target = self._closest_unowned_planet(state, home.x, home.y)

        command = SetWaypointsCommand(
            fleet_id=colony_fleet.id,
            waypoints=[
                Waypoint(
                    x=target.x,
                    y=target.y,
                    task=WaypointTask(type="colonise"),
                ),
            ],
        )

        state = self._submit_and_resolve(game_id, [command])
        state = self._resolve_until(
            game_id,
            lambda current: any(
                event.code == "colonisation.failed" and event.values[-1] == "no_colonists"
                for event in current.events
            ),
        )
        failure = next(event for event in state.events if event.code == "colonisation.failed")
        assert failure.source_id == target.id
        assert failure.values[-1] == "no_colonists"
