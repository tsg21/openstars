"""Built-in command parser registration."""


def register_builtin_command_parsers() -> None:
    """Import command modules so their parsers register with the shared registry."""
    from openstars.engine.resolve_steps.commands import (  # noqa: F401
        jettison_cargo,
        merge_split_fleets,
        production,
        rename_fleet,
        select_race,
        set_planet_production_mode,
        set_research,
        set_waypoints,
    )
