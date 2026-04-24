from openstars.engine.models import Minerals
from openstars.engine.research.miniaturisation import miniaturisation_discount, miniaturise_cost


def test_miniaturisation_discount_and_cost():
    levels = {
        "energy": 4,
        "weapons": 4,
        "propulsion": 4,
        "construction": 4,
        "electronics": 4,
        "biotechnology": 4,
    }
    req = {k: 3 for k in levels}
    assert miniaturisation_discount(req, levels) == 0.04

    base = type("Cost", (), {"resources": 10, "ironium": 5, "boranium": 2, "germanium": 1})
    discounted = miniaturise_cost(base, 0.5)
    assert discounted.resources == 5
    assert discounted.minerals == Minerals(ironium=2, boranium=1, germanium=1)
