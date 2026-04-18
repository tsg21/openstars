"""Steps 4–6 — tick loop, movement, shooting, and log tests."""

import json
import pathlib

from openstars.combat.altair.engine import budget_round, budget_tick, run_battle
from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleSnapshot,
    CombatLog,
    Position,
    Token,
)

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _two_token_snap(**cfg_kw) -> BattleSnapshot:
    return BattleSnapshot(
        tokens=[
            Token(id="a1", owner="alice", position=Position(x=1000, y=5000)),
            Token(id="b1", owner="bob", position=Position(x=9000, y=5000)),
        ],
        config=AltairCombatConfig(**cfg_kw),
    )


def _close_tokens_snap(**cfg_kw) -> BattleSnapshot:
    """Two tokens already within weapon range."""
    return BattleSnapshot(
        tokens=[
            Token(
                id="a1",
                owner="alice",
                position=Position(x=5000, y=5000),
                hp=50,
                weapon_damage=30,
                weapon_range_classic=3,
            ),
            Token(
                id="b1",
                owner="bob",
                position=Position(x=5500, y=5000),
                hp=50,
                weapon_damage=30,
                weapon_range_classic=3,
            ),
        ],
        config=AltairCombatConfig(**cfg_kw),
    )


def _single_tick_snap(
    *,
    left_x: int,
    right_x: int,
    left_range: int,
    right_range: int,
    left_movement_quarters: int = 4,
    right_movement_quarters: int = 4,
) -> BattleSnapshot:
    return BattleSnapshot(
        tokens=[
            Token(
                id="a1",
                owner="alice",
                position=Position(x=left_x, y=5000),
                movement_quarters=left_movement_quarters,
                weapon_range_classic=left_range,
            ),
            Token(
                id="b1",
                owner="bob",
                position=Position(x=right_x, y=5000),
                movement_quarters=right_movement_quarters,
                weapon_range_classic=right_range,
            ),
        ],
        config=AltairCombatConfig(N_rounds=1, T=1),
    )


# ---------------------------------------------------------------------------
# Step 4 — budget helpers
# ---------------------------------------------------------------------------


class TestBudgetRound:
    def test_default_quarters(self):
        assert budget_round(4, S=1000) == 1000

    def test_half_square(self):
        assert budget_round(2, S=1000) == 500

    def test_odd_quarters(self):
        assert budget_round(3, S=1000) == 750

    def test_ten_quarter_cap(self):
        assert budget_round(10, S=1000) == 2500


class TestBudgetTick:
    def test_sum_equals_budget_round(self):
        for br in [0, 1, 19, 20, 100, 999, 1000, 2500]:
            T = 20
            total = sum(budget_tick(br, T, k) for k in range(T))
            assert total == br, f"budget_round={br}: sum={total}"

    def test_even_split(self):
        assert budget_tick(100, T=20, k=0) == 5
        assert budget_tick(100, T=20, k=19) == 5

    def test_remainder_distribution(self):
        br = 23
        T = 20
        ticks = [budget_tick(br, T, k) for k in range(T)]
        assert ticks[:3] == [2, 2, 2]
        assert ticks[3:] == [1] * 17
        assert sum(ticks) == 23


# ---------------------------------------------------------------------------
# Step 4 — tick loop and movement
# ---------------------------------------------------------------------------


class TestTickLoop:
    def test_total_ticks_bounded(self):
        snap = _two_token_snap()
        log = run_battle(snap)
        tick_events = [e for e in log.events if e.type == "tick_start"]
        assert len(tick_events) <= snap.config.N_rounds * snap.config.T

    def test_deterministic(self):
        snap = _two_token_snap()
        log1 = run_battle(snap)
        log2 = run_battle(snap)
        assert log1 == log2

    def test_log_length_stable(self):
        snap = _two_token_snap()
        lengths = {len(run_battle(snap).events) for _ in range(5)}
        assert len(lengths) == 1, "Log length varied across identical runs"

    def test_tokens_move_toward_each_other(self):
        snap = _two_token_snap(N_rounds=1)
        log = run_battle(snap)
        moves_a = [e for e in log.events if e.type == "token_moved" and e.token_id == "a1"]
        moves_b = [e for e in log.events if e.type == "token_moved" and e.token_id == "b1"]
        if moves_a:
            assert moves_a[0].to_pos.x > moves_a[0].from_pos.x, "a1 should move right toward b1"
        if moves_b:
            assert moves_b[0].to_pos.x < moves_b[0].from_pos.x, "b1 should move left toward a1"


# ---------------------------------------------------------------------------
# Step 5 — shooting phase
# ---------------------------------------------------------------------------


class TestShooting:
    def test_close_tokens_fire(self):
        snap = _close_tokens_snap(N_rounds=1)
        log = run_battle(snap)
        fired = [e for e in log.events if e.type == "weapon_fired"]
        assert len(fired) >= 1, "Expected at least one weapon_fired event"
        assert all(e.hit for e in fired), "All shots should hit at close range"

    def test_destruction_event(self):
        snap = _close_tokens_snap(N_rounds=3)
        log = run_battle(snap)
        destroyed = [e for e in log.events if e.type == "token_destroyed"]
        assert len(destroyed) >= 1, "At least one token should be destroyed"

    def test_battle_ends_on_elimination(self):
        snap = _close_tokens_snap(N_rounds=16)
        log = run_battle(snap)
        end = [e for e in log.events if e.type == "battle_end"]
        assert len(end) == 1
        assert end[0].reason == "one_side_eliminated"

    def test_dead_token_does_not_fire(self):
        """A token destroyed during the shooting phase must not fire later."""
        snap = BattleSnapshot(
            tokens=[
                Token(
                    id="a1",
                    owner="alice",
                    position=Position(x=5000, y=5000),
                    hp=10,
                    weapon_damage=200,
                    weapon_range_classic=5,
                ),
                Token(
                    id="b1",
                    owner="bob",
                    position=Position(x=5100, y=5000),
                    hp=10,
                    weapon_damage=200,
                    weapon_range_classic=5,
                ),
            ],
            config=AltairCombatConfig(N_rounds=1),
        )
        log = run_battle(snap)
        destroyed_ids = [e.token_id for e in log.events if e.type == "token_destroyed"]
        for d_id in destroyed_ids:
            fired_after = []
            saw_destroy = False
            for e in log.events:
                if e.type == "token_destroyed" and e.token_id == d_id:
                    saw_destroy = True
                if saw_destroy and e.type == "weapon_fired" and e.attacker_id == d_id and e.hit:
                    fired_after.append(e)
            assert fired_after == [], f"Destroyed token {d_id} fired after death"

    def test_dissipated_damage_varies_by_distance(self):
        base_token = Token(
            id="a1",
            owner="alice",
            position=Position(x=0, y=0),
            movement_quarters=0,
            hp=100,
            weapon_damage=100,
            weapon_range_classic=2,
        )
        target_hp = 200
        cases = [
            (0, 100, 100),
            (400, 100, 100),
            (1200, 95, 95),
            (2000, 90, 90),
        ]

        for distance_x, expected_damage, expected_pct in cases:
            snap = BattleSnapshot(
                tokens=[
                    base_token.model_copy(deep=True),
                    Token(
                        id="b1",
                        owner="bob",
                        position=Position(x=distance_x, y=0),
                        movement_quarters=0,
                        hp=target_hp,
                        weapon_damage=0,
                        weapon_range_classic=2,
                    ),
                ],
                config=AltairCombatConfig(N_rounds=1, T=1),
            )
            log = run_battle(snap)
            fired = [e for e in log.events if e.type == "weapon_fired" and e.attacker_id == "a1"]
            assert len(fired) == 1
            assert fired[0].damage == expected_damage
            assert fired[0].dissipation_pct == expected_pct

            damage_events = [
                e for e in log.events if e.type == "damage_applied" and e.target_id == "b1"
            ]
            assert len(damage_events) == 1
            assert damage_events[0].damage == expected_damage

    def test_point_blank_shot_deals_full_damage(self):
        snap = BattleSnapshot(
            tokens=[
                Token(
                    id="a1",
                    owner="alice",
                    position=Position(x=5000, y=5000),
                    movement_quarters=0,
                    weapon_damage=40,
                    weapon_range_classic=2,
                ),
                Token(
                    id="b1",
                    owner="bob",
                    position=Position(x=5000, y=5000),
                    movement_quarters=0,
                    hp=100,
                    weapon_damage=0,
                    weapon_range_classic=2,
                ),
            ],
            config=AltairCombatConfig(N_rounds=1, T=1),
        )
        log = run_battle(snap)
        fired = [e for e in log.events if e.type == "weapon_fired" and e.attacker_id == "a1"]
        assert fired[0].damage == 40
        assert fired[0].dissipation_pct == 100

    def test_max_range_shot_deals_ninety_percent_damage(self):
        snap = BattleSnapshot(
            tokens=[
                Token(
                    id="a1",
                    owner="alice",
                    position=Position(x=0, y=0),
                    movement_quarters=0,
                    weapon_damage=40,
                    weapon_range_classic=2,
                ),
                Token(
                    id="b1",
                    owner="bob",
                    position=Position(x=2000, y=0),
                    movement_quarters=0,
                    hp=100,
                    weapon_damage=0,
                    weapon_range_classic=2,
                ),
            ],
            config=AltairCombatConfig(N_rounds=1, T=1),
        )
        log = run_battle(snap)
        fired = [e for e in log.events if e.type == "weapon_fired" and e.attacker_id == "a1"]
        assert fired[0].damage == 36
        assert fired[0].dissipation_pct == 90


class TestMovementAi:
    def test_token_inside_flat_zone_does_not_move(self):
        snap = _single_tick_snap(left_x=5000, right_x=5100, left_range=2, right_range=2)
        log = run_battle(snap)
        moves = [e for e in log.events if e.type == "token_moved"]
        assert moves == []

    def test_token_outside_weapon_range_closes_toward_target(self):
        snap = _single_tick_snap(left_x=1000, right_x=9000, left_range=2, right_range=2)
        log = run_battle(snap)
        move = next(e for e in log.events if e.type == "token_moved" and e.token_id == "a1")
        assert move.to_pos.x > move.from_pos.x

    def test_token_in_range_but_outside_flat_zone_closes_to_threshold(self):
        snap = _single_tick_snap(
            left_x=5000,
            right_x=6500,
            left_range=2,
            right_range=2,
            left_movement_quarters=8,
            right_movement_quarters=8,
        )
        log = run_battle(snap)
        moves = [e for e in log.events if e.type == "token_moved"]
        move_by_id = {e.token_id: e for e in moves}
        assert move_by_id["a1"].to_pos.x == 6100
        assert "b1" not in move_by_id

    def test_tokens_with_different_ranges_behave_independently(self):
        snap = _single_tick_snap(left_x=5000, right_x=5300, left_range=2, right_range=1)
        log = run_battle(snap)
        moves = [e for e in log.events if e.type == "token_moved"]
        move_by_id = {e.token_id: e for e in moves}
        assert "a1" not in move_by_id
        assert move_by_id["b1"].to_pos.x == 5200


# ---------------------------------------------------------------------------
# Step 6 — CombatLog schema and versioning
# ---------------------------------------------------------------------------


class TestCombatLogSchema:
    def test_schema_version_in_log(self):
        snap = _two_token_snap(N_rounds=1)
        log = run_battle(snap)
        assert log.schema_version == "altair-v3"

    def test_config_echoed(self):
        cfg = AltairCombatConfig(S=500, T=10, N_rounds=2)
        snap = BattleSnapshot(
            tokens=[
                Token(id="a1", owner="alice", position=Position(x=100, y=100)),
                Token(id="b1", owner="bob", position=Position(x=4000, y=4000)),
            ],
            config=cfg,
        )
        log = run_battle(snap)
        assert log.config.S == 500
        assert log.config.T == 10
        assert log.config.N_rounds == 2

    def test_reject_unknown_schema_version(self):
        data = {
            "schema_version": "unknown-v99",
            "config": AltairCombatConfig().model_dump(),
            "events": [],
        }
        log = CombatLog.model_validate(data)
        assert log.schema_version == "unknown-v99"

    def test_golden_file(self):
        """Generate and validate a golden fixture for a minimal battle."""
        snap = _close_tokens_snap(N_rounds=3)
        log = run_battle(snap)
        golden_path = FIXTURES_DIR / "minimal_battle.json"

        log_json = log.model_dump_json(indent=2)

        if not golden_path.exists():
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(log_json + "\n")

        golden_data = json.loads(golden_path.read_text())
        current_data = json.loads(log_json)
        assert current_data == golden_data, (
            f"Golden file mismatch — if intentional, delete {golden_path} and re-run to regenerate"
        )
