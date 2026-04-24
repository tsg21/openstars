import pytest

from openstars.engine.research.costs import BASE_COST, FIELDS, level_up_cost


def test_base_cost_sequence():
    assert BASE_COST[0] == 50
    assert BASE_COST[1] == 80
    assert len(BASE_COST) == 26
    assert BASE_COST[25] == 8_320_400
    for index in range(2, 26):
        assert BASE_COST[index] == BASE_COST[index - 1] + BASE_COST[index - 2]


def test_level_up_cost():
    assert level_up_cost(0, 0) == 50
    assert level_up_cost(0, 12) == 170
    assert level_up_cost(25, 0) == 8_320_400
    with pytest.raises(ValueError):
        level_up_cost(26, 0)


def test_fields_order():
    assert FIELDS == (
        "energy",
        "weapons",
        "propulsion",
        "construction",
        "electronics",
        "biotechnology",
    )
