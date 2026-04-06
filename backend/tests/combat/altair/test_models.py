"""Step 3 — snapshot and token model tests."""

import json

from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleSnapshot,
    CombatLog,
    Position,
    Token,
)


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
                weapon_damage=20,
                weapon_range_classic=2,
            ),
            Token(
                id="b1",
                owner="bob",
                position=Position(x=9000, y=5000),
                hp=100,
                movement_quarters=4,
                weapon_damage=20,
                weapon_range_classic=2,
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


class TestCombatLogRoundTrip:
    def test_empty_log(self):
        log = CombatLog(config=AltairCombatConfig(), events=[])
        data = json.loads(log.model_dump_json())
        restored = CombatLog.model_validate(data)
        assert restored.schema_version == "altair-v1"
        assert restored.events == []
