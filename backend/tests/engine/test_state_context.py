from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.galaxy import galaxy_max_coord
from openstars.engine.models import (
    Design,
    DesignCost,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GlobalState,
    Minerals,
    Player,
    Scanner,
)
from openstars.engine.race.presets import default_race
from openstars.engine.state_context import StateContext


def _global_state() -> GlobalState:
    return GlobalState(
        game={"seed": 1, "turn": 0, "next_id": 1},
        players=[
            Player(username="tim", name="Tim", race=default_race()),
            Player(username="sara", name="Sara", race=default_race()),
        ],
        planets=[],
        fleets=[],
    )


def test_state_context_lookups_populated() -> None:
    galaxy = Galaxy(
        galaxy=GalaxyMetadata(name="g", size="small", seed=1),
        planets=[GalaxyPlanet(id="PL1", name="Terra", x=1, y=2)],
    )
    designs = [
        Design(
            id="DE1",
            owner="tim",
            name="Scout",
            hull="scout",
            mass=1,
            fuel_usage=[1] * 10,
            fuel_capacity=10,
            scanner=Scanner(normal=0),
            cost=DesignCost(resources=1, minerals=Minerals()),
        )
    ]
    ctx = StateContext("g1", _global_state(), galaxy, designs, load_component_catalogue())
    assert ctx.galaxy_planets_by_id["PL1"].name == "Terra"
    assert ctx.planet_names == {"PL1": "Terra"}
    assert ctx.planet_coordinates_by_id == {"PL1": (1, 2)}
    assert ctx.planet_coords == {(1, 2)}
    assert set(ctx.players_by_username) == {"tim", "sara"}
    assert ctx.designs_by_id["DE1"].owner == "tim"
    assert ctx.max_coord == galaxy_max_coord(galaxy)
    assert ctx.planet_coordinates("missing") is None
