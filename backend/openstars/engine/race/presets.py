"""Predefined race presets."""

from openstars.engine.race.models import (
    PRT,
    Race,
    RaceHabitability,
    RaceHabitabilityFactor,
)

HUMANOID = Race(
    name="Humanoid",
    plural_name="Humanoids",
    emblem=0,
    prt=PRT.JACK_OF_ALL_TRADES,
    lrts=frozenset(),
    habitability=RaceHabitability(
        gravity=RaceHabitabilityFactor(range=(15, 85)),
        temperature=RaceHabitabilityFactor(range=(15, 85)),
        radiation=RaceHabitabilityFactor(range=(15, 85)),
    ),
)

PREDEFINED_RACES: dict[str, Race] = {"humanoid": HUMANOID}


def default_race() -> Race:
    return HUMANOID.model_copy(deep=True)
