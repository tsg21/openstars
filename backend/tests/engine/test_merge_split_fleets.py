from openstars.engine.models import (
    Cargo,
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GameMeta,
    GlobalState,
    MergeSplitFleetEntry,
    MergeSplitFleetsCommand,
    Minerals,
    Player,
    PlayerCommands,
    Position,
    Scanner,
    SetWaypointsCommand,
    Waypoint,
)
from openstars.engine.resolve_steps.apply_commands import apply_commands
from openstars.engine.turn_context import TurnContext


def _design(design_id: str, fuel_capacity: int, cargo_capacity: int) -> Design:
    return Design(
        id=design_id,
        owner="tim",
        name=design_id,
        hull="scout",
        mass=10,
        fuel_usage=[0] * 10,
        fuel_capacity=fuel_capacity,
        cargo_capacity=cargo_capacity,
        scanner=Scanner(normal=0, penetrating=0),
        cost=DesignCost(resources=1, minerals=Minerals()),
    )


def _ctx() -> TurnContext:
    fleets = [
        Fleet(
            id="FL1",
            name="Scout Fleet",
            owner="tim",
            position=Position(x=10, y=20),
            composition=[FleetComposition(design_id="DE_SCOUT", count=1)],
            cargo=Cargo(ironium=20, boranium=10, germanium=5, colonists=400),
            fuel=30,
        ),
        Fleet(
            id="FL2",
            name="Freighter Fleet",
            owner="tim",
            position=Position(x=10, y=20),
            composition=[FleetComposition(design_id="DE_FRT", count=1)],
            cargo=Cargo(ironium=10, boranium=30, germanium=15, colonists=200),
            fuel=50,
        ),
        Fleet(
            id="FL_ENEMY",
            name="Enemy",
            owner="sara",
            position=Position(x=10, y=20),
            composition=[FleetComposition(design_id="DE_SCOUT", count=1)],
        ),
    ]
    state = GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=100),
        players=[Player(username="tim", name="Tim"), Player(username="sara", name="Sara")],
        planets=[],
        fleets=fleets,
    )
    return TurnContext(
        "game1",
        state,
        Galaxy(galaxy=GalaxyMetadata(name="test", size="small", seed=42), planets=[]),
        [_design("DE_SCOUT", 30, 0), _design("DE_FRT", 50, 100)],
    )


def test_merge_two_fleets_into_one_dissolves_other():
    ctx = _ctx()
    apply_commands(
        ctx,
        {
            "tim": PlayerCommands(
                commands=[
                    MergeSplitFleetsCommand(
                        fleets=[
                            MergeSplitFleetEntry(
                                fleet_id="FL1",
                                ships=[
                                    FleetComposition(design_id="DE_SCOUT", count=1),
                                    FleetComposition(design_id="DE_FRT", count=1),
                                ],
                            ),
                            MergeSplitFleetEntry(fleet_id="FL2", ships=[]),
                        ]
                    )
                ]
            )
        },
    )

    assert "FL1" in ctx.fleets_by_id
    assert "FL2" not in ctx.fleets_by_id
    assert {c.design_id: c.count for c in ctx.fleets_by_id["FL1"].composition} == {
        "DE_SCOUT": 1,
        "DE_FRT": 1,
    }


def test_split_one_fleet_creates_new_real_fleet_and_resolves_tmp_waypoint_reference():
    ctx = _ctx()
    apply_commands(
        ctx,
        {
            "tim": PlayerCommands(
                commands=[
                    MergeSplitFleetsCommand(
                        fleets=[
                            MergeSplitFleetEntry(
                                fleet_id="FL1",
                                ships=[FleetComposition(design_id="DE_SCOUT", count=1)],
                            ),
                            MergeSplitFleetEntry(
                                fleet_id="tmp_1",
                                name="New Fleet",
                                ships=[FleetComposition(design_id="DE_FRT", count=1)],
                            ),
                            MergeSplitFleetEntry(fleet_id="FL2", ships=[]),
                        ]
                    ),
                    SetWaypointsCommand(
                        fleet_id="tmp_1",
                        waypoints=[Waypoint(x=11, y=20, warp=5)],
                    ),
                ]
            )
        },
    )

    new_fleet = next(
        fleet
        for fleet in ctx.fleets_by_id.values()
        if fleet.owner == "tim" and fleet.name == "New Fleet"
    )
    assert new_fleet.id.startswith("FL")
    assert new_fleet.id != "tmp_1"
    assert len(new_fleet.waypoints) == 1
    assert new_fleet.waypoints[0].x == 11


def test_fuel_and_cargo_distributed_proportionally():
    ctx = _ctx()
    apply_commands(
        ctx,
        {
            "tim": PlayerCommands(
                commands=[
                    MergeSplitFleetsCommand(
                        fleets=[
                            MergeSplitFleetEntry(
                                fleet_id="FL1",
                                ships=[FleetComposition(design_id="DE_SCOUT", count=1)],
                            ),
                            MergeSplitFleetEntry(
                                fleet_id="FL2",
                                ships=[FleetComposition(design_id="DE_FRT", count=1)],
                            ),
                        ]
                    )
                ]
            )
        },
    )

    assert ctx.fleets_by_id["FL1"].fuel == 30
    assert ctx.fleets_by_id["FL2"].fuel == 50
    assert ctx.fleets_by_id["FL1"].cargo.ironium == 0
    assert ctx.fleets_by_id["FL2"].cargo.ironium == 30


def test_merge_split_rejects_mismatched_ship_totals():
    ctx = _ctx()
    try:
        apply_commands(
            ctx,
            {
                "tim": PlayerCommands(
                    commands=[
                        MergeSplitFleetsCommand(
                            fleets=[
                                MergeSplitFleetEntry(
                                    fleet_id="FL1",
                                    ships=[FleetComposition(design_id="DE_SCOUT", count=2)],
                                ),
                                MergeSplitFleetEntry(fleet_id="FL2", ships=[]),
                            ]
                        )
                    ]
                )
            },
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "ship totals" in str(exc)


def test_merge_split_rejects_unowned_listed_fleet():
    ctx = _ctx()
    try:
        apply_commands(
            ctx,
            {
                "tim": PlayerCommands(
                    commands=[
                        MergeSplitFleetsCommand(
                            fleets=[
                                MergeSplitFleetEntry(
                                    fleet_id="FL1",
                                    ships=[FleetComposition(design_id="DE_SCOUT", count=1)],
                                ),
                                MergeSplitFleetEntry(
                                    fleet_id="FL_ENEMY",
                                    ships=[FleetComposition(design_id="DE_SCOUT", count=1)],
                                ),
                            ]
                        )
                    ]
                )
            },
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "not owned" in str(exc)
