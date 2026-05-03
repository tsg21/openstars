from openstars.engine.fog import derive_player_state
from openstars.engine.models import (
    Galaxy,
    GalaxyMetadata,
    GameMeta,
    GlobalState,
    Player,
)
from openstars.engine.race.presets import HUMANOID, default_race


def _empty_galaxy() -> Galaxy:
    return Galaxy(galaxy=GalaxyMetadata(name="Test", size="small", seed=42), planets=[])


def _state(player: Player) -> GlobalState:
    return GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=1),
        players=[player],
        planets=[],
        fleets=[],
    )


def test_player_without_race_defaults_to_none() -> None:
    player = Player(username="alice", name="Alice")

    assert player.race is None


def test_player_race_round_trips_through_json() -> None:
    player = Player(username="alice", name="Alice", race=default_race())

    restored = Player.model_validate_json(player.model_dump_json())

    assert restored == player
    assert restored.race == default_race()


def test_derive_player_state_includes_viewer_race() -> None:
    state = _state(Player(username="alice", name="Alice", race=HUMANOID))

    player_state = derive_player_state(state, _empty_galaxy(), "alice", designs=[])

    assert player_state.race == HUMANOID


def test_derive_player_state_allows_missing_turn_zero_race() -> None:
    state = _state(Player(username="alice", name="Alice"))

    player_state = derive_player_state(state, _empty_galaxy(), "alice", designs=[])

    assert player_state.race is None
