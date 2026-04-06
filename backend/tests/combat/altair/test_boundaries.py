"""Step 1 — import isolation: Altair package must not pull in FastAPI or server."""

import importlib
import sys


def test_altair_import_does_not_pull_fastapi():
    mods_before = set(sys.modules.keys())
    importlib.import_module("openstars.combat.altair")

    new_mods = set(sys.modules.keys()) - mods_before
    server_leaks = [m for m in new_mods if "fastapi" in m or "openstars.server" in m]
    assert server_leaks == [], f"Altair imported server/FastAPI modules: {server_leaks}"


def test_altair_import_does_not_pull_resolve():
    mods_before = set(sys.modules.keys())
    importlib.import_module("openstars.combat.altair")

    new_mods = set(sys.modules.keys()) - mods_before
    resolve_leaks = [m for m in new_mods if "resolve" in m]
    assert resolve_leaks == [], f"Altair imported resolve modules: {resolve_leaks}"


def test_public_api_exports():
    from openstars.combat.altair import (
        AltairCombatConfig,
        BattleSnapshot,
        CombatLog,
        run_battle,
    )

    assert callable(run_battle)
    assert AltairCombatConfig is not None
    assert BattleSnapshot is not None
    assert CombatLog is not None
