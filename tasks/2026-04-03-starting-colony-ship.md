# Starting Colony Ship

Restore the intended turn 0 setup so each player begins with a colony ship in addition to the scout and small freighter.

## Step 1: Seed colony ships during game creation

- [x] Add a `colony_ship` design to turn 0 setup for each player
- [x] Add a starting colony ship fleet at the home planet for each player
- [x] Keep the fleet cargo empty so players must load colonists manually

Unit tests:
- [x] Update turn 0 setup tests for design, fleet, and next-id counts
- [x] Add an API regression test asserting the starting colony ship is visible in player state

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_setup.py tests/server/test_api.py`

## Step 2: Final quality gate

- [x] Backend lint: `cd backend && uv run ruff check .`
