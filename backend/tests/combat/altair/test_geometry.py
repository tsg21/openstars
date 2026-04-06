"""Step 2 — config, geometry, and distance tests."""

from openstars.combat.altair.geometry import distance, in_range
from openstars.combat.altair.models import AltairCombatConfig
from openstars.engine.util import isqrt

# --- isqrt parity (same function, but verify from this import path) ---


class TestIsqrtParity:
    def test_zero(self):
        assert isqrt(0) == 0

    def test_perfect_squares(self):
        for n in [1, 4, 9, 16, 25, 100, 10000]:
            r = isqrt(n)
            assert r * r == n

    def test_non_perfect(self):
        assert isqrt(2) == 1
        assert isqrt(3) == 1
        assert isqrt(5) == 2
        assert isqrt(8) == 2
        assert isqrt(10) == 3

    def test_large(self):
        assert isqrt(1_000_000) == 1000
        r = isqrt(999_999)
        assert r == 999
        assert r * r <= 999_999 < (r + 1) * (r + 1)


# --- AltairCombatConfig ---


class TestConfig:
    def test_defaults(self):
        cfg = AltairCombatConfig()
        assert cfg.S == 1000
        assert cfg.T == 20
        assert cfg.N_rounds == 16
        assert cfg.arena_size == 10_000

    def test_custom_S(self):
        cfg = AltairCombatConfig(S=500)
        assert cfg.arena_size == 5_000


# --- distance ---


class TestDistance:
    def test_same_point(self):
        assert distance(100, 200, 100, 200) == 0

    def test_horizontal(self):
        assert distance(0, 0, 1000, 0) == 1000

    def test_vertical(self):
        assert distance(0, 0, 0, 1000) == 1000

    def test_diagonal_3_4_5(self):
        assert distance(0, 0, 3000, 4000) == 5000

    def test_diagonal_non_exact(self):
        d = distance(0, 0, 1000, 1000)
        assert d == isqrt(2_000_000)
        assert d == 1414


# --- in_range ---


class TestInRange:
    def test_exactly_at_range(self):
        assert in_range(2000, R_classic=2, S=1000) is True

    def test_just_inside(self):
        assert in_range(1999, R_classic=2, S=1000) is True

    def test_just_outside(self):
        assert in_range(2001, R_classic=2, S=1000) is False

    def test_zero_range_same_point(self):
        assert in_range(0, R_classic=0, S=1000) is True

    def test_zero_range_different_point(self):
        assert in_range(1, R_classic=0, S=1000) is False

    def test_starbase_bonus(self):
        assert in_range(2500, R_classic=2, S=1000, starbase_bonus=False) is False
        assert in_range(2500, R_classic=2, S=1000, starbase_bonus=True) is True
        assert in_range(3000, R_classic=2, S=1000, starbase_bonus=True) is True
        assert in_range(3001, R_classic=2, S=1000, starbase_bonus=True) is False
