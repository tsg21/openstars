"""Tests for production helper functions."""

from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.models import (
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameMeta,
    GlobalState,
    Minerals,
    PlanetState,
    Player,
    Position,
    ProductionProgress,
    ProductionQueueItem,
    Scanner,
)
from openstars.engine.race.presets import default_race
from openstars.engine.resolve_steps.production import (
    FIXED_PRODUCTION_COSTS,
    STARBASE_TOTAL_COSTS,
    ProductionCost,
    apply_completed_starbase,
    apply_completed_unit,
    consume_completed_unit,
    get_production_cost,
    get_ship_queue_item_cost,
    get_starbase_build_cost,
    get_starbase_total_cost,
    largest_payable_resource_increment,
    proportional_mineral_spend,
    remove_queue_item_quantity,
    resolve_planet_production,
    resolve_planetary_scanner_tier,
    spend_production_increment,
)
from openstars.engine.turn_context import TurnContext

_CATALOGUE = load_component_catalogue()
_JOAT_RACE = default_race()
_JOAT_ECONOMY = _JOAT_RACE.economy


def test_production_cost_tables_match_prd_12():
    mine_cost = get_production_cost("mine", _JOAT_ECONOMY)
    factory_cost = get_production_cost("factory", _JOAT_ECONOMY)
    planetary_scanner_cost = get_production_cost("planetary_scanner", _JOAT_ECONOMY)

    assert mine_cost.resources == 5
    assert mine_cost.minerals == Minerals()
    assert factory_cost.resources == 10
    assert factory_cost.minerals == Minerals(germanium=4)
    assert planetary_scanner_cost.resources == 100
    assert planetary_scanner_cost.minerals == Minerals(ironium=10, boranium=10, germanium=70)
    assert FIXED_PRODUCTION_COSTS["planetary_scanner"] == planetary_scanner_cost


def test_starbase_cost_tables_and_lookup():
    fort_cost = get_starbase_total_cost("orbital_fort")
    station_cost = get_starbase_total_cost("space_station")

    assert fort_cost == STARBASE_TOTAL_COSTS["orbital_fort"]
    assert station_cost == STARBASE_TOTAL_COSTS["space_station"]
    assert station_cost.resources > fort_cost.resources


def test_starbase_first_build_and_upgrade_cost():
    no_base_planet = PlanetState(id="PL000001")
    first_build = get_starbase_build_cost(no_base_planet, "orbital_fort")
    assert first_build == get_starbase_total_cost("orbital_fort")

    existing_base_planet = PlanetState(
        id="PL000001",
        starbase={"type": "orbital_fort", "can_build_ships": False},
    )
    upgrade_cost = get_starbase_build_cost(existing_base_planet, "space_station")
    station = get_starbase_total_cost("space_station")
    fort = get_starbase_total_cost("orbital_fort")
    assert upgrade_cost.resources == station.resources - (fort.resources // 2)


def test_starbase_upgrade_to_same_type_rejected():
    planet = PlanetState(
        id="PL000001",
        starbase={"type": "space_station", "can_build_ships": True},
    )
    try:
        get_starbase_build_cost(planet, "space_station")
    except ValueError as exc:
        assert "same type" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_apply_completed_starbase_sets_shipbuilding_capability():
    no_base_planet = PlanetState(id="PL000001")

    fort_planet = apply_completed_starbase(no_base_planet, "orbital_fort")
    station_planet = apply_completed_starbase(no_base_planet, "space_station")

    assert fort_planet.starbase is not None
    assert fort_planet.starbase.can_build_ships is False
    assert station_planet.starbase is not None
    assert station_planet.starbase.can_build_ships is True


def test_starbase_queue_blocks_following_items_until_complete():
    ctx = TurnContext(
        "game1",
        GlobalState(
            game=GameMeta(seed=7, turn=1, next_id=10),
            players=[Player(username="tim", name="tim", race=_JOAT_RACE)],
            planets=[],
            fleets=[],
        ),
        Galaxy(galaxy=GalaxyMetadata(name="T", size="small", seed=1), planets=[]),
        [],
        _CATALOGUE,
    )
    planet = PlanetState(
        id="PL000001",
        owner="tim",
        population=25_000,
        minerals={"ironium": 20, "boranium": 10, "germanium": 5},
        production_queue=[
            ProductionQueueItem(
                id="PQ000001",
                item_type="starbase",
                target_type="orbital_fort",
                quantity=1,
            ),
            ProductionQueueItem(id="PQ000002", item_type="mine", quantity=1),
        ],
    )

    updated_planet, completed, _, _ = resolve_planet_production(
        planet,
        available_resources=40,
        ctx=ctx,
    )

    assert completed == {}
    assert len(updated_planet.production_queue) == 2
    assert updated_planet.production_queue[0].item_type == "starbase"


def _ship_ctx() -> TurnContext:
    galaxy = Galaxy(
        galaxy=GalaxyMetadata(name="T", size="small", seed=1),
        planets=[GalaxyPlanet(id="PL1", name="Sol", x=100, y=200)],
    )
    ship_design = Design(
        id="DEship1",
        owner="tim",
        name="Scout",
        hull="scout",
        fuel_usage=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        fuel_capacity=100,
        scanner=Scanner(normal=150, penetrating=0),
        cost=DesignCost(
            resources=10,
            minerals=Minerals(ironium=4, boranium=2, germanium=2),
        ),
    )
    state = GlobalState(
        game=GameMeta(seed=7, turn=1, next_id=10),
        players=[Player(username="tim", name="tim", race=_JOAT_RACE)],
        planets=[
            PlanetState(
                id="PL1",
                owner="tim",
                starbase={"type": "space_station", "can_build_ships": True},
                minerals=Minerals(ironium=20, boranium=20, germanium=20),
            )
        ],
        fleets=[],
    )
    return TurnContext("game1", state, galaxy, [ship_design], _CATALOGUE)


def test_ship_cost_lookup_from_design():
    ctx = _ship_ctx()
    item = ProductionQueueItem(id="PQ1", item_type="ship", design_id="DEship1", quantity=1)
    cost = get_ship_queue_item_cost(item, ctx)
    assert cost.resources == 10
    assert cost.minerals == Minerals(ironium=4, boranium=2, germanium=4)


def test_ship_proportional_mineral_spend_for_multi_mineral_cost():
    cost = ProductionCost(
        resources=10,
        minerals=Minerals(ironium=4, boranium=2, germanium=2),
    )
    minerals = proportional_mineral_spend(5, cost)
    assert minerals == Minerals(ironium=2, boranium=1, germanium=1)


def test_ship_completion_creates_new_fleet_when_none_exists():
    ctx = _ship_ctx()
    planet = ctx.planets_by_id["PL1"].model_copy(
        update={
            "production_queue": [
                ProductionQueueItem(id="PQ1", item_type="ship", design_id="DEship1", quantity=1)
            ]
        }
    )
    updated_planet, completed, built, _ = resolve_planet_production(
        planet,
        available_resources=10,
        ctx=ctx,
    )
    assert updated_planet.production_queue == []
    assert completed["ship"] == 1
    assert built["DEship1"] == 1
    assert len(ctx.fleets_by_id) == 1
    created_fleet = next(iter(ctx.fleets_by_id.values()))
    assert created_fleet.fuel == 100


def test_ship_completion_joins_existing_fleet_containing_design():
    ctx = _ship_ctx()
    ctx.fleets_by_id["FLA"] = Fleet(
        id="FLA",
        name="Fleet A",
        owner="tim",
        position=Position(x=100, y=200),
        composition=[FleetComposition(design_id="DEship1", count=2)],
        fuel=150,
    )
    planet = ctx.planets_by_id["PL1"].model_copy(
        update={
            "production_queue": [
                ProductionQueueItem(id="PQ1", item_type="ship", design_id="DEship1", quantity=1)
            ]
        }
    )
    resolve_planet_production(planet, available_resources=10, ctx=ctx)
    assert ctx.fleets_by_id["FLA"].composition[0].count == 3
    assert ctx.fleets_by_id["FLA"].fuel == 250


def test_ship_completion_joins_lexicographically_smallest_matching_fleet():
    ctx = _ship_ctx()
    ctx.fleets_by_id["FLB"] = Fleet(
        id="FLB",
        name="Fleet B",
        owner="tim",
        position=Position(x=100, y=200),
        composition=[FleetComposition(design_id="DEship1", count=1)],
        fuel=90,
    )
    ctx.fleets_by_id["FLA"] = Fleet(
        id="FLA",
        name="Fleet A",
        owner="tim",
        position=Position(x=100, y=200),
        composition=[FleetComposition(design_id="DEship1", count=1)],
        fuel=40,
    )
    planet = ctx.planets_by_id["PL1"].model_copy(
        update={
            "production_queue": [
                ProductionQueueItem(id="PQ1", item_type="ship", design_id="DEship1", quantity=1)
            ]
        }
    )
    resolve_planet_production(planet, available_resources=10, ctx=ctx)
    assert ctx.fleets_by_id["FLA"].composition[0].count == 2
    assert ctx.fleets_by_id["FLA"].fuel == 140
    assert ctx.fleets_by_id["FLB"].composition[0].count == 1
    assert ctx.fleets_by_id["FLB"].fuel == 90


def test_planetary_scanner_completion_sets_has_scanner():
    ctx = _ship_ctx()
    planet = ctx.planets_by_id["PL1"].model_copy(
        update={
            "minerals": Minerals(ironium=200, boranium=200, germanium=200),
            "production_queue": [
                ProductionQueueItem(id="PQscan1", item_type="planetary_scanner", quantity=1)
            ],
        }
    )
    updated_planet, completed, _, _ = resolve_planet_production(
        planet,
        available_resources=100,
        ctx=ctx,
    )

    assert updated_planet.has_scanner is True
    assert updated_planet.production_queue == []
    assert completed["planetary_scanner"] == 1


def test_proportional_mineral_thresholds_for_factory_progress():
    factory_cost = get_production_cost("factory", _JOAT_ECONOMY)

    assert proportional_mineral_spend(2, factory_cost).germanium == 0
    assert proportional_mineral_spend(3, factory_cost).germanium == 1
    assert proportional_mineral_spend(5, factory_cost).germanium == 2
    assert proportional_mineral_spend(8, factory_cost).germanium == 3
    assert proportional_mineral_spend(10, factory_cost).germanium == 4


def test_largest_payable_increment_blocks_factory_without_germanium():
    factory_cost = get_production_cost("factory", _JOAT_ECONOMY)
    progress = ProductionProgress(
        resources_spent=4,
        minerals_spent=Minerals(germanium=1),
    )

    increment = largest_payable_resource_increment(
        progress=progress,
        available_resources=4,
        available_minerals=Minerals(),
        cost=factory_cost,
    )

    assert increment == 0


def test_spend_increment_uses_largest_payable_resource_increment():
    factory_cost = get_production_cost("factory", _JOAT_ECONOMY)
    progress, remaining_resources, remaining_minerals = spend_production_increment(
        progress=ProductionProgress(),
        available_resources=10,
        available_minerals=Minerals(germanium=2),
        cost=factory_cost,
    )

    assert progress.resources_spent == 7
    assert progress.minerals_spent == Minerals(germanium=2)
    assert remaining_resources == 3
    assert remaining_minerals == Minerals()


def test_completion_resets_progress_and_decrements_quantity():
    item = ProductionQueueItem(
        id="PQ000001",
        item_type="factory",
        quantity=3,
        progress=ProductionProgress(
            resources_spent=10,
            minerals_spent=Minerals(germanium=4),
        ),
    )

    updated_item = consume_completed_unit(item)

    assert updated_item is not None
    assert updated_item.quantity == 2
    assert updated_item.progress == ProductionProgress()


def test_completion_removes_last_item():
    item = ProductionQueueItem(id="PQ000001", item_type="mine", quantity=1)

    assert consume_completed_unit(item) is None


def test_apply_completed_unit_effects():
    planet = PlanetState(id="PL000001", mines=2, factories=3)

    mined = apply_completed_unit(planet, "mine")
    factory_built = apply_completed_unit(planet, "factory")
    scanner_built = apply_completed_unit(planet, "planetary_scanner")

    assert mined.mines == 3
    assert mined.factories == 3
    assert factory_built.mines == 2
    assert factory_built.factories == 4
    assert scanner_built.has_scanner is True

    try:
        apply_completed_unit(planet, "starbase")
    except ValueError as exc:
        assert str(exc) == "starbase completion requires target_type"
    else:
        raise AssertionError("expected ValueError")


def test_resolve_planetary_scanner_tier_phase_1_defaults():
    assert resolve_planetary_scanner_tier(electronics=0, biotechnology=0) == ("Viewer 50", 50, 0)


def test_remove_semantics_can_discard_partial_progress_without_refunds():
    item = ProductionQueueItem(
        id="PQ000001",
        item_type="factory",
        quantity=4,
        progress=ProductionProgress(
            resources_spent=6,
            minerals_spent=Minerals(germanium=2),
        ),
    )

    updated_item = remove_queue_item_quantity(
        item,
        quantity=1,
        discard_in_progress_unit=True,
    )

    assert updated_item is not None
    assert updated_item.quantity == 3
    assert updated_item.progress == ProductionProgress()


def test_remove_semantics_can_preserve_partial_progress_when_not_removed():
    item = ProductionQueueItem(
        id="PQ000001",
        item_type="factory",
        quantity=4,
        progress=ProductionProgress(
            resources_spent=6,
            minerals_spent=Minerals(germanium=2),
        ),
    )

    updated_item = remove_queue_item_quantity(
        item,
        quantity=1,
        discard_in_progress_unit=False,
    )

    assert updated_item is not None
    assert updated_item.quantity == 3
    assert updated_item.progress.resources_spent == 6


def test_remove_semantics_remove_entire_entry():
    item = ProductionQueueItem(id="PQ000001", item_type="mine", quantity=2)

    assert remove_queue_item_quantity(item, quantity=2, discard_in_progress_unit=False) is None
