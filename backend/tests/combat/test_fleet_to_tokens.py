"""Tests for ``openstars.combat.fleet_to_tokens``."""

from openstars.combat.altair.models import Position as ArenaPosition
from openstars.combat.fleet_to_tokens import tokens_from_fleet
from openstars.engine.component_catalogue import (
    ArmourStats,
    ComponentCatalogue,
    ComponentCatalogueEntry,
    ComponentCost,
    HullSlotDefinition,
    HullStats,
    WeaponStats,
)
from openstars.engine.models import (
    Design,
    DesignComponent,
    DesignCost,
    Fleet,
    FleetComposition,
    Minerals,
    Position,
    Scanner,
)


def _cost(resources: int = 0) -> ComponentCost:
    return ComponentCost(resources=resources, ironium=0, boranium=0, germanium=0)


def _hull_entry(
    hull_id: str,
    *,
    armour_points: int = 20,
    slots: list[HullSlotDefinition] | None = None,
) -> ComponentCatalogueEntry:
    return ComponentCatalogueEntry(
        id=hull_id,
        name=hull_id,
        component_type="hull",
        cost=_cost(),
        mass=10,
        hull=HullStats(
            domain="ship",
            fuel_capacity=100,
            cargo_capacity=0,
            armour_points=armour_points,
            initiative=0,
            slots=slots or [],
        ),
    )


def _weapon_entry(
    component_id: str,
    *,
    damage: int = 10,
    range_classic: int = 1,
    initiative: int = 6,
) -> ComponentCatalogueEntry:
    return ComponentCatalogueEntry(
        id=component_id,
        name=component_id,
        component_type="weapon",
        cost=_cost(),
        mass=2,
        weapon=WeaponStats(range=range_classic, damage=damage, initiative=initiative),
    )


def _armour_entry(component_id: str, *, armour_points: int = 50) -> ComponentCatalogueEntry:
    return ComponentCatalogueEntry(
        id=component_id,
        name=component_id,
        component_type="armour",
        cost=_cost(),
        mass=4,
        armour=ArmourStats(armour_points=armour_points),
    )


def _catalogue(*entries: ComponentCatalogueEntry) -> ComponentCatalogue:
    by_id = {e.id: e for e in entries}
    by_type: dict = {
        "engine": [],
        "scanner": [],
        "weapon": [],
        "shield": [],
        "armour": [],
        "hull": [],
    }
    for e in entries:
        by_type[e.component_type].append(e)
    return ComponentCatalogue(by_id=by_id, by_type=by_type)


def _design(
    design_id: str,
    hull: str,
    components: list[DesignComponent],
) -> Design:
    return Design(
        id=design_id,
        owner="alice",
        name=design_id,
        hull=hull,
        components=components,
        fuel_usage=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        fuel_capacity=100,
        scanner=Scanner(normal=0),
        cargo_capacity=0,
        cost=DesignCost(resources=10, minerals=Minerals()),
    )


def _fleet(composition: list[FleetComposition]) -> Fleet:
    return Fleet(
        id="FL1",
        name="Fleet 1",
        owner="alice",
        position=Position(x=123, y=456),
        composition=composition,
    )


def test_single_design_single_weapon_builds_one_token():
    catalogue = _catalogue(
        _hull_entry("scout", armour_points=20),
        _weapon_entry("laser_mk1", damage=10, range_classic=1, initiative=6),
    )
    design = _design(
        "D1",
        "scout",
        [DesignComponent(slot_number=1, component_id="laser_mk1", component_count=2)],
    )
    fleet = _fleet([FleetComposition(design_id="D1", count=3)])

    tokens = tokens_from_fleet(fleet, {"D1": design}, catalogue)

    assert len(tokens) == 1
    token = tokens[0]
    assert token.owner == "alice"
    assert token.design_id == "D1"
    assert token.ship_count == 3
    assert token.position.x == 0 and token.position.y == 0
    assert token.hp == 20 * 3
    assert len(token.weapons) == 1
    w = token.weapons[0]
    assert w.component_id == "laser_mk1"
    assert w.weapon_type == "beam"
    assert w.count == 2 * 3
    assert w.damage == 10
    assert w.range_classic == 1
    assert w.initiative == 6


def test_identical_weapons_across_slots_aggregate():
    catalogue = _catalogue(
        _hull_entry("frigate"),
        _weapon_entry("laser_mk1"),
    )
    design = _design(
        "D1",
        "frigate",
        [
            DesignComponent(slot_number=1, component_id="laser_mk1", component_count=2),
            DesignComponent(slot_number=2, component_id="laser_mk1", component_count=3),
        ],
    )
    fleet = _fleet([FleetComposition(design_id="D1", count=4)])

    tokens = tokens_from_fleet(fleet, {"D1": design}, catalogue)

    assert len(tokens[0].weapons) == 1
    assert tokens[0].weapons[0].count == (2 + 3) * 4


def test_unknown_design_is_skipped():
    catalogue = _catalogue(_hull_entry("scout"))
    fleet = _fleet(
        [
            FleetComposition(design_id="MISSING", count=1),
            FleetComposition(design_id="D1", count=1),
        ]
    )
    design = _design("D1", "scout", [])

    tokens = tokens_from_fleet(fleet, {"D1": design}, catalogue)

    assert len(tokens) == 1
    assert tokens[0].design_id == "D1"


def test_armour_components_increase_hp():
    catalogue = _catalogue(
        _hull_entry("frigate", armour_points=45),
        _armour_entry("titanium_armour", armour_points=50),
    )
    design = _design(
        "D1",
        "frigate",
        [DesignComponent(slot_number=2, component_id="titanium_armour", component_count=2)],
    )
    fleet = _fleet([FleetComposition(design_id="D1", count=3)])

    tokens = tokens_from_fleet(fleet, {"D1": design}, catalogue)

    # (45 hull + 2 * 50 armour) * 3 ships
    assert tokens[0].hp == (45 + 100) * 3


def test_arena_position_is_applied_to_all_tokens():
    catalogue = _catalogue(
        _hull_entry("scout"),
        _hull_entry("frigate"),
    )
    designs = {
        "D1": _design("D1", "scout", []),
        "D2": _design("D2", "frigate", []),
    }
    fleet = _fleet(
        [
            FleetComposition(design_id="D1", count=1),
            FleetComposition(design_id="D2", count=1),
        ]
    )

    tokens = tokens_from_fleet(
        fleet,
        designs,
        catalogue,
        position=ArenaPosition(x=9000, y=5000),
    )

    assert [(t.position.x, t.position.y) for t in tokens] == [(9000, 5000), (9000, 5000)]


def test_token_id_prefix_is_applied():
    catalogue = _catalogue(_hull_entry("scout"))
    design = _design("D1", "scout", [])
    fleet = _fleet([FleetComposition(design_id="D1", count=1)])

    tokens = tokens_from_fleet(fleet, {"D1": design}, catalogue, token_id_prefix="side-a")

    assert tokens[0].id == "side-a-FL1-0"


def test_multiple_compositions_produce_one_token_each():
    catalogue = _catalogue(
        _hull_entry("scout"),
        _hull_entry("frigate"),
        _weapon_entry("laser_mk1"),
    )
    designs = {
        "D1": _design("D1", "scout", []),
        "D2": _design(
            "D2",
            "frigate",
            [DesignComponent(slot_number=1, component_id="laser_mk1", component_count=1)],
        ),
    }
    fleet = _fleet(
        [
            FleetComposition(design_id="D1", count=1),
            FleetComposition(design_id="D2", count=2),
        ]
    )

    tokens = tokens_from_fleet(fleet, designs, catalogue)

    assert [t.design_id for t in tokens] == ["D1", "D2"]
    assert tokens[0].weapons == []
    assert tokens[1].weapons[0].count == 2
