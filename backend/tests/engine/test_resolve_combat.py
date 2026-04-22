"""Combat integration tests for resolve-step wiring."""

from __future__ import annotations

import pytest

from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleEndEvent,
    BattleSnapshot,
    CombatLog,
    DamageAppliedEvent,
    Token,
    TokenDestroyedEvent,
)
from openstars.combat.altair.models import (
    Position as ArenaPosition,
)
from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.models import (
    Cargo,
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
    Player,
    Position,
    Scanner,
)
from openstars.engine.resolve import resolve_turn
from openstars.engine.resolve_steps.combat import (
    apply_casualties,
    arena_entry_positions,
    detect_battle_sites,
    resolve_combat,
    run_combat,
)
from openstars.engine.turn_context import TurnContext
from openstars.storage.memory import MemoryStorage

_DEF_FUEL_USAGE = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def _design(design_id: str, owner: str) -> Design:
    return Design(
        id=design_id,
        owner=owner,
        name=f"{owner}-scout",
        hull="scout",
        mass=12,
        fuel_usage=_DEF_FUEL_USAGE,
        fuel_capacity=100,
        scanner=Scanner(normal=0, penetrating=0),
        cost=DesignCost(resources=10, minerals=Minerals()),
    )


def _fleet(fleet_id: str, owner: str, x: int, y: int, *, count: int = 2) -> Fleet:
    return Fleet(
        id=fleet_id,
        name=fleet_id,
        owner=owner,
        position=Position(x=x, y=y),
        composition=[FleetComposition(design_id=f"DE-{owner}", count=count)],
        fuel=50,
    )


def _state(
    fleets: list[Fleet], *, combat_ruleset: str = "altair", next_id: int = 100
) -> GlobalState:
    return GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=next_id, combat_ruleset=combat_ruleset),
        players=[Player(username="a", name="A"), Player(username="b", name="B")],
        planets=[],
        fleets=fleets,
    )


def _galaxy(planets: list[GalaxyPlanet] | None = None) -> Galaxy:
    return Galaxy(galaxy=GalaxyMetadata(name="g", size="small", seed=1), planets=planets or [])


def test_detect_battle_sites_filters_by_distinct_owner_and_is_deterministic():
    fleets = [
        _fleet("FL3", "a", 20, 20),
        _fleet("FL1", "a", 10, 10),
        _fleet("FL2", "b", 10, 10),
        _fleet("FL4", "c", 20, 20),
        _fleet("FL5", "a", 30, 30),
    ]

    sites = detect_battle_sites(fleets)

    assert len(sites) == 2
    assert [fleet.id for fleet in sites[0]] == ["FL1", "FL2"]
    assert [fleet.id for fleet in sites[1]] == ["FL3", "FL4"]


def test_arena_entry_positions_opposite_and_repeatable():
    first = arena_entry_positions(["a", "b"], 10_000)
    second = arena_entry_positions(["a", "b"], 10_000)

    assert first == second
    centre = 5000
    radius = 4000
    assert abs(abs(first["a"].x - centre) - radius) <= 1
    assert first["a"].y == first["b"].y
    assert abs(first["a"].x - first["b"].x) >= 2 * radius - 2


def test_apply_casualties_uses_proportional_round_up_and_preserves_fleet_fields():
    fleet = Fleet(
        id="FL1",
        name="Alpha",
        owner="a",
        position=Position(x=7, y=9),
        composition=[FleetComposition(design_id="DE-a", count=5)],
        fuel=42,
        cargo=Cargo(),
        waypoints=[],
    )
    snap = BattleSnapshot(
        tokens=[
            Token(
                id="BT000000-FL1-0",
                owner="a",
                position=ArenaPosition(x=0, y=0),
                hp=100,
                ship_count=5,
                design_id="DE-a",
            )
        ],
        config=AltairCombatConfig(),
    )
    log = CombatLog(
        config=AltairCombatConfig(),
        events=[
            DamageAppliedEvent(
                target_id="BT000000-FL1-0",
                damage=50,
                remaining_hp=50,
                round_index=0,
            ),
            BattleEndEvent(reason="done"),
        ],
    )

    updated, lost = apply_casualties(snap, log, {"FL1": fleet})

    assert updated["FL1"].composition[0].count == 2
    assert updated["FL1"].position == Position(x=7, y=9)
    assert updated["FL1"].fuel == 42
    assert updated["FL1"].name == "Alpha"
    assert lost == {"a": 3}


def test_apply_casualties_dissolves_destroyed_fleets_and_sums_lost_by_owner():
    snap = BattleSnapshot(
        tokens=[
            Token(
                id="BT000000-FL1-0",
                owner="a",
                position=ArenaPosition(x=0, y=0),
                hp=30,
                ship_count=3,
                design_id="DE-a",
            ),
            Token(
                id="BT000000-FL2-0",
                owner="a",
                position=ArenaPosition(x=0, y=0),
                hp=20,
                ship_count=2,
                design_id="DE-a",
            ),
        ],
        config=AltairCombatConfig(),
    )
    log = CombatLog(
        config=AltairCombatConfig(),
        events=[
            TokenDestroyedEvent(token_id="BT000000-FL1-0", round_index=0),
            TokenDestroyedEvent(token_id="BT000000-FL2-0", round_index=0),
            BattleEndEvent(reason="done"),
        ],
    )
    fleets = {
        "FL1": _fleet("FL1", "a", 0, 0, count=3),
        "FL2": _fleet("FL2", "a", 0, 0, count=2),
    }

    updated, lost = apply_casualties(snap, log, fleets)

    assert "FL1" not in updated
    assert "FL2" not in updated
    assert lost == {"a": 5}


def test_run_combat_dispatches_rulesets():
    snap = BattleSnapshot(tokens=[], config=AltairCombatConfig())
    assert isinstance(run_combat("altair", snap), CombatLog)
    with pytest.raises(NotImplementedError, match="classic ruleset not implemented"):
        run_combat("classic", snap)


def test_resolve_combat_no_sites_is_no_op():
    storage = MemoryStorage()
    fleet = _fleet("FL1", "a", 1, 1)
    ctx = TurnContext(
        "game1",
        _state([fleet], next_id=200),
        _galaxy(),
        [_design("DE-a", "a")],
        load_component_catalogue(),
    )
    ctx.fleets = [fleet]

    resolve_combat(ctx, storage)

    assert ctx._next_id == 200
    assert ctx.owner_events == {}
    assert storage.list_combat_logs("game1") == []


def test_resolve_turn_integration_writes_log_and_event_for_each_owner(monkeypatch):
    storage = MemoryStorage()
    fleets = [_fleet("FL1", "a", 10, 10), _fleet("FL2", "b", 10, 10)]
    state = _state(fleets, next_id=1)
    galaxy = _galaxy([GalaxyPlanet(id="PL1", name="Altair", x=10, y=10)])
    designs = [_design("DE-a", "a"), _design("DE-b", "b")]

    def fake_run(_ruleset: str, snapshot: BattleSnapshot, *, cfg=None):
        token = sorted(snapshot.tokens, key=lambda token: token.id)[0]
        return CombatLog(
            config=snapshot.config,
            events=[
                DamageAppliedEvent(
                    target_id=token.id,
                    damage=token.hp,
                    remaining_hp=0,
                    round_index=0,
                ),
                TokenDestroyedEvent(token_id=token.id, round_index=0),
                BattleEndEvent(reason="one_side_eliminated"),
            ],
        )

    monkeypatch.setattr("openstars.engine.resolve_steps.combat.run_combat_step", fake_run)

    new_state = resolve_turn(
        state,
        galaxy,
        {},
        designs,
        game_id="game1",
        storage=storage,
    )

    battle_ids = storage.list_combat_logs("game1")
    assert len(battle_ids) == 1
    assert battle_ids[0].startswith("BT")
    assert len(new_state.events["a"]) == 1
    assert len(new_state.events["b"]) == 1
    assert new_state.events["a"][0].code == "combat.resolved"
    assert new_state.events["a"][0].values[0] == battle_ids[0]
    assert new_state.events["a"][0].values[1] == "Altair"
    assert new_state.game.next_id == 2


def test_resolve_turn_classic_only_raises_when_battle_occurs():
    designs = [_design("DE-a", "a"), _design("DE-b", "b")]
    colliding = _state(
        [_fleet("FL1", "a", 10, 10), _fleet("FL2", "b", 10, 10)],
        combat_ruleset="classic",
    )
    separate = _state(
        [_fleet("FL1", "a", 10, 10), _fleet("FL2", "b", 11, 10)],
        combat_ruleset="classic",
    )

    with pytest.raises(NotImplementedError):
        resolve_turn(colliding, _galaxy(), {}, designs, game_id="game1", storage=MemoryStorage())

    result = resolve_turn(
        separate, _galaxy(), {}, designs, game_id="game1", storage=MemoryStorage()
    )
    assert result.game.turn == 1
