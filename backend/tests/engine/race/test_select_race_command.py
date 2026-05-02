import pytest
from pydantic import ValidationError

from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.models import (
    Galaxy,
    GalaxyMetadata,
    GameMeta,
    GlobalState,
    Player,
    PlayerCommands,
    SelectRaceCommand,
)
from openstars.engine.race.costs import RaceValidationError
from openstars.engine.race.models import (
    PRT,
    Race,
    RaceEconomy,
    RaceHabitability,
    RaceHabitabilityFactor,
    RaceResearch,
    ResearchCostProfile,
)
from openstars.engine.race.presets import HUMANOID, default_race
from openstars.engine.research.costs import FIELDS
from openstars.engine.resolve_steps.apply_commands import apply_commands
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError

_CATALOGUE = load_component_catalogue()


def _ctx() -> TurnContext:
    return TurnContext(
        "game1",
        GlobalState(
            game=GameMeta(seed=42, turn=0, next_id=1),
            players=[Player(username="alice", name="Alice")],
            planets=[],
            fleets=[],
        ),
        Galaxy(galaxy=GalaxyMetadata(name="Test", size="small", seed=42), planets=[]),
        designs=[],
        component_catalogue=_CATALOGUE,
    )


def _apply(ctx: TurnContext, *commands: SelectRaceCommand) -> None:
    apply_commands(ctx, {"alice": PlayerCommands(commands=list(commands))})


def _custom_race(name: str = "Custom") -> Race:
    return default_race().model_copy(
        update={
            "name": name,
            "plural_name": f"{name}s",
            "emblem": 1,
            "max_growth_rate": 14,
        }
    )


def _overspent_race() -> Race:
    return Race(
        name="Spendthrift",
        plural_name="Spendthrifts",
        emblem=1,
        prt=PRT.JACK_OF_ALL_TRADES,
        habitability=RaceHabitability(
            gravity=RaceHabitabilityFactor(immune=True),
            temperature=RaceHabitabilityFactor(immune=True),
            radiation=RaceHabitabilityFactor(immune=True),
        ),
        max_growth_rate=20,
        economy=RaceEconomy(
            colonists_per_resource=700,
            factory_output_per_10=15,
            factory_cost_resources=5,
            factories_per_10k_colonists=25,
            factories_save_germanium=True,
            mine_output_per_10=25,
            mine_cost_resources=2,
            mines_per_10k_colonists=25,
            ar_resource_divisor=5,
        ),
        research=RaceResearch(
            field_profile={field: ResearchCostProfile.CHEAP for field in FIELDS},
            start_at_tech_3=True,
        ),
    )


def test_predefined_humanoid_selection_sets_player_race() -> None:
    ctx = _ctx()

    _apply(ctx, SelectRaceCommand(predefined_id="humanoid"))
    result = ctx.build_result()

    assert result.players[0].race == HUMANOID


def test_custom_race_selection_writes_canonical_record() -> None:
    ctx = _ctx()
    race = _custom_race()

    _apply(ctx, SelectRaceCommand(race=race))
    result = ctx.build_result()

    assert result.players[0].race == race


def test_select_race_rejects_neither_predefined_nor_custom() -> None:
    with pytest.raises(ValidationError):
        SelectRaceCommand()


def test_select_race_rejects_both_predefined_and_custom() -> None:
    with pytest.raises(ValidationError):
        SelectRaceCommand(predefined_id="humanoid", race=_custom_race())


def test_unknown_predefined_race_raises_code() -> None:
    ctx = _ctx()

    with pytest.raises(GameError) as error:
        _apply(ctx, SelectRaceCommand(predefined_id="rabbitoid"))

    assert error.value.error_code == "PREDEFINED_RACE_UNKNOWN"


def test_overspent_custom_race_raises_validation_code() -> None:
    ctx = _ctx()

    with pytest.raises(RaceValidationError) as error:
        _apply(ctx, SelectRaceCommand(race=_overspent_race()))

    assert error.value.code == "RACE_OVERSPENT"


def test_multiple_select_race_commands_last_one_wins() -> None:
    ctx = _ctx()
    final_race = _custom_race("Final")

    _apply(
        ctx,
        SelectRaceCommand(predefined_id="humanoid"),
        SelectRaceCommand(race=final_race),
    )
    result = ctx.build_result()

    assert result.players[0].race == final_race
