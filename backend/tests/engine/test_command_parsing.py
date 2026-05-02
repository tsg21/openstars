from openstars.engine.resolve_steps.commands import register_builtin_command_parsers
from openstars.engine.resolve_steps.commands.parsing import (
    COMMAND_PARSERS,
    CommandParseContext,
    parse_registered_command,
)
from openstars.server.errors import GameError


def _parse_context() -> CommandParseContext:
    return CommandParseContext(
        username="tim",
        owned_fleet_ids={"FL000001", "FL000002"},
        declared_tmp_fleet_ids=set(),
        max_coord=1023,
        owned_planets={},
        queue_state_by_planet={},
        player_design_ids=set(),
    )


def test_builtin_command_parsers_are_registered():
    register_builtin_command_parsers()

    assert {
        "set_waypoints",
        "jettison_cargo",
        "rename_fleet",
        "merge_split_fleets",
        "add_production_item",
        "move_production_item",
        "remove_production_item",
        "clear_production_queue",
        "set_research",
        "set_planet_production_mode",
        "select_race",
    }.issubset(COMMAND_PARSERS)


def test_parse_registered_command_allows_tmp_fleet_declared_by_previous_command():
    register_builtin_command_parsers()
    ctx = _parse_context()

    merge_command = parse_registered_command(
        {
            "type": "merge_split_fleets",
            "fleets": [
                {"fleet_id": "FL000001", "ships": []},
                {"fleet_id": "tmp_1", "ships": []},
            ],
        },
        ctx,
    )
    waypoint_command = parse_registered_command(
        {
            "type": "set_waypoints",
            "fleet_id": "tmp_1",
            "waypoints": [{"x": 10, "y": 20}],
        },
        ctx,
    )

    assert merge_command.type == "merge_split_fleets"
    assert "tmp_1" in ctx.declared_tmp_fleet_ids
    assert waypoint_command.type == "set_waypoints"
    assert waypoint_command.fleet_id == "tmp_1"


def test_parse_registered_command_rejects_unknown_command_type():
    register_builtin_command_parsers()

    try:
        parse_registered_command({"type": "unknown_command"}, _parse_context())
    except GameError as exc:
        assert exc.error_code == "UNKNOWN_COMMAND"
    else:
        raise AssertionError("Expected UNKNOWN_COMMAND")
