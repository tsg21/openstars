import pytest

from openstars.engine.create_game import create_initial_state
from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import generate_galaxy
from openstars.engine.models import (
    PlayerCommands,
    SelectRaceCommand,
)
from openstars.engine.race.models import (
    RaceHabitability,
    RaceHabitabilityFactor,
)
from openstars.engine.race.presets import HUMANOID, default_race
from openstars.engine.resolve import resolve_turn
from openstars.server.errors import GameError
from openstars.storage.memory import MemoryStorage


def _fresh_game():
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state, designs = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    return galaxy, state, designs


def _humanoid_commands(*usernames: str) -> dict[str, PlayerCommands]:
    return {
        username: PlayerCommands(commands=[SelectRaceCommand(predefined_id="humanoid")])
        for username in usernames
    }


def test_create_initial_state_is_bare_turn_zero() -> None:
    _galaxy, state, designs = _fresh_game()

    assert all(player.race is None for player in state.players)
    assert all(not planet.is_homeworld for planet in state.planets)
    assert all(planet.owner is None for planet in state.planets)
    assert designs == []
    assert state.fleets == []


def test_create_initial_state_keeps_random_planet_values_until_resolution() -> None:
    _galaxy, state, _designs = _fresh_game()

    assert any(planet.habitability.gravity != 50 for planet in state.planets)
    assert any(planet.concentrations.ironium < 30 for planet in state.planets)
    assert all(1 <= planet.concentrations.ironium <= 200 for planet in state.planets)


def test_turn_zero_player_state_is_empty_command_phase_shape() -> None:
    galaxy, state, designs = _fresh_game()

    player_state = derive_player_state(state, galaxy, "tim", designs)

    assert player_state.race is None
    assert all(planet.scan_level == "none" for planet in player_state.planets)
    assert all(planet.owner is None for planet in player_state.planets)
    assert player_state.fleets == []
    assert player_state.designs == []
    assert player_state.events == []
    assert player_state.research is None


def test_resolve_turn_zero_materialises_homeworlds_designs_and_fleets() -> None:
    galaxy, state, _designs = _fresh_game()
    storage = MemoryStorage()

    result = resolve_turn(
        state,
        galaxy,
        _humanoid_commands("sara", "tim"),
        designs=[],
        game_id="game1",
        storage=storage,
    )

    assert result.game.turn == 1
    assert all(player.race == HUMANOID for player in result.players)
    home_planets = [planet for planet in result.planets if planet.is_homeworld]
    assert len(home_planets) == 2
    for planet in home_planets:
        assert planet.owner in {"sara", "tim"}
        assert planet.population == 25_000
        assert planet.mines == 10
        assert planet.factories == 10
        assert planet.minerals.ironium == 300
        assert planet.minerals.boranium == 300
        assert planet.minerals.germanium == 300
        assert planet.starbase is not None
        assert planet.concentrations.ironium >= 30
        assert planet.concentrations.boranium >= 30
        assert planet.concentrations.germanium >= 30
        assert planet.habitability.gravity == 50
        assert planet.habitability.temperature == 50
        assert planet.habitability.radiation == 50

    assert {event.code for events in result.events.values() for event in events} == {"race.saved"}
    assert len(result.fleets) == 8
    assert len(storage.list_designs("game1", "sara")) == 3
    assert len(storage.list_designs("game1", "tim")) == 3


def test_custom_immune_factor_leaves_homeworld_random_value() -> None:
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state, _designs = create_initial_state(galaxy, ["sara"], game_seed=12345)
    storage = MemoryStorage()
    custom = default_race().model_copy(
        update={
            "habitability": RaceHabitability(
                gravity=RaceHabitabilityFactor(immune=True),
                temperature=RaceHabitabilityFactor(range=(40, 60)),
                radiation=RaceHabitabilityFactor(range=(30, 70)),
            )
        }
    )
    # With a single player, the first assigned home is deterministic.
    original_home = state.planets[state.game.seed % len(galaxy.planets)]

    result = resolve_turn(
        state,
        galaxy,
        {"sara": PlayerCommands(commands=[SelectRaceCommand(race=custom)])},
        designs=[],
        game_id="game1",
        storage=storage,
    )

    home = next(planet for planet in result.planets if planet.is_homeworld)
    assert home.habitability.gravity == original_home.habitability.gravity
    assert home.habitability.temperature == 50
    assert home.habitability.radiation == 50


def test_turn_zero_requires_every_player_to_select_a_race() -> None:
    galaxy, state, _designs = _fresh_game()

    with pytest.raises(GameError) as error:
        resolve_turn(
            state,
            galaxy,
            _humanoid_commands("tim"),
            designs=[],
            game_id="game1",
            storage=MemoryStorage(),
        )

    assert error.value.error_code == "TURN_ZERO_INCOMPLETE"


def test_turn_one_uses_standard_pipeline() -> None:
    galaxy, state, _designs = _fresh_game()
    storage = MemoryStorage()
    turn_one = resolve_turn(
        state,
        galaxy,
        _humanoid_commands("sara", "tim"),
        designs=[],
        game_id="game1",
        storage=storage,
    )

    result = resolve_turn(
        turn_one,
        galaxy,
        {"sara": PlayerCommands(commands=[]), "tim": PlayerCommands(commands=[])},
        designs=storage.list_designs("game1", "sara") + storage.list_designs("game1", "tim"),
        game_id="game1",
        storage=storage,
    )

    assert result.game.turn == 2
    assert all(player.race is not None for player in result.players)
    assert any(planet.minerals.ironium > 300 for planet in result.planets if planet.is_homeworld)
