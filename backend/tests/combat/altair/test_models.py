"""Step 1 — snapshot, token, and weapon model tests."""

import json

from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleSnapshot,
    CombatLog,
    Position,
    Token,
    TokenWeapon,
)


def _beam(**overrides) -> TokenWeapon:
    defaults = {
        "component_id": "laser_mk1",
        "weapon_type": "beam",
        "count": 1,
        "damage": 20,
        "range_classic": 2,
        "initiative": 6,
    }
    defaults.update(overrides)
    return TokenWeapon(**defaults)


def _two_token_snapshot(**cfg_overrides) -> BattleSnapshot:
    """Fixture: two tokens of different owners facing each other."""
    return BattleSnapshot(
        tokens=[
            Token(
                id="a1",
                owner="alice",
                position=Position(x=1000, y=5000),
                hp=100,
                movement_quarters=4,
                weapons=[_beam()],
            ),
            Token(
                id="b1",
                owner="bob",
                position=Position(x=9000, y=5000),
                hp=100,
                movement_quarters=4,
                weapons=[_beam()],
            ),
        ],
        config=AltairCombatConfig(**cfg_overrides),
    )


class TestSnapshotRoundTrip:
    def test_json_round_trip(self):
        snap = _two_token_snapshot()
        data = json.loads(snap.model_dump_json())
        restored = BattleSnapshot.model_validate(data)
        assert restored == snap

    def test_token_fields(self):
        snap = _two_token_snapshot()
        a = snap.tokens[0]
        assert a.id == "a1"
        assert a.owner == "alice"
        assert a.position.x == 1000
        assert a.hp == 100
        assert a.ship_count == 1
        assert a.design_id is None


class TestTokenWeapons:
    def test_multiple_weapon_groups_round_trip(self):
        token = Token(
            id="a1",
            owner="alice",
            position=Position(x=0, y=0),
            design_id="d-1",
            ship_count=3,
            weapons=[
                _beam(component_id="laser_mk1", count=6, damage=10, range_classic=1),
                _beam(
                    component_id="heavy_laser", count=3, damage=20, range_classic=3, initiative=5
                ),
            ],
        )
        restored = Token.model_validate(json.loads(token.model_dump_json()))
        assert restored == token
        assert restored.ship_count == 3
        assert {w.component_id for w in restored.weapons} == {"laser_mk1", "heavy_laser"}

    def test_token_without_weapons_is_valid(self):
        token = Token(id="x", owner="alice", position=Position(x=0, y=0))
        assert token.weapons == []
        assert token.ship_count == 1


class TestCombatLogRoundTrip:
    def test_empty_log(self):
        log = CombatLog(config=AltairCombatConfig(), events=[])
        data = json.loads(log.model_dump_json())
        restored = CombatLog.model_validate(data)
        assert restored.schema_version == "altair-v5"
        assert restored.events == []
