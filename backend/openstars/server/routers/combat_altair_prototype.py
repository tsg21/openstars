"""Isolated router for the Altair combat prototype.

Not wired into game auth or turn resolution — this is a standalone
simulation endpoint for development and the replay viewer.
"""

from fastapi import APIRouter

from openstars.combat.altair import BattleSnapshot, CombatLog, run_battle

router = APIRouter(
    prefix="/api/v1/combat-altair-prototype",
    tags=["combat-altair-prototype"],
)


@router.post("/simulate", response_model=CombatLog)
async def simulate(snapshot: BattleSnapshot) -> CombatLog:
    """Run an Altair combat simulation and return the event log."""
    return run_battle(snapshot, snapshot.config)
