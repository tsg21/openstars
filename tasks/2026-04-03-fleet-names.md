# Fleet Names

Fleets need display names. Each fleet gets a name when created (e.g. "Fleet #1") and players can rename them via a `rename_fleet` command.

This task covers the backend only. Frontend changes are a separate task.

## Step 1: Add `name` field to Fleet and PlayerFleet models

- [ ] Add `name: str` to `Fleet` in `backend/openstars/engine/models.py`
- [ ] Add `name: str | None = None` to `PlayerFleet` in `backend/openstars/engine/models.py` (only set for own fleets; enemy fleets omit it)

Unit tests:
- [ ] Update any existing model snapshot or serialisation tests that construct `Fleet` objects directly

Validation:
- [ ] `cd backend && uv run pytest`

## Step 2: Assign names during game creation

- [ ] In `backend/openstars/engine/create_game.py`, track a per-player fleet counter and name each starting fleet sequentially: "Fleet #1", "Fleet #2", "Fleet #3"
- [ ] Pass `name=` when constructing each `Fleet` in the starting fleet loop

Unit tests:
- [ ] Update `tests/engine/test_setup.py` to assert each starting fleet has the correct name (e.g. player's first fleet is "Fleet #1")

Validation:
- [ ] `cd backend && uv run pytest tests/engine/test_setup.py`

## Step 3: Add `RenameFleetCommand`

- [ ] Add `RenameFleetCommand` to `backend/openstars/engine/models.py`:
  - `type: Literal["rename_fleet"] = "rename_fleet"`
  - `fleet_id: str`
  - `name: str` with `Field(min_length=1, max_length=64)`
- [ ] Add `RenameFleetCommand` to the `PlayerCommand` discriminated union

Unit tests:
- [ ] Add schema tests asserting `rename_fleet` commands deserialise correctly and that an empty or >64-char name is rejected

Validation:
- [ ] `cd backend && uv run pytest tests/`

## Step 4: Handle `rename_fleet` in command application

- [ ] In `backend/openstars/engine/resolve_steps/commands.py`, add `_apply_rename_fleet_command` that updates `fleet.name` (ownership check; silently ignore unknown/unowned fleets)
- [ ] Import `RenameFleetCommand` and dispatch it in `apply_commands`

Unit tests:
- [ ] Add unit tests for `_apply_rename_fleet_command`: own fleet gets renamed, unowned fleet is ignored, name is trimmed to model constraints

Validation:
- [ ] `cd backend && uv run pytest tests/engine/`

## Step 5: Propagate `name` through fog of war

- [ ] In `backend/openstars/engine/fog.py`, set `name=fleet.name` when building the `PlayerFleet` for own fleets
- [ ] Enemy `PlayerFleet` entries leave `name` as `None` (name is not visible through fog of war)
- [ ] Add an API-level regression test in `tests/server/test_api.py` asserting that fleet names appear in player state and that submitting a `rename_fleet` command changes the name after resolution

Validation:
- [ ] `cd backend && uv run pytest tests/`

## Step 6: Final quality gate

- [ ] `cd backend && uv run ruff check .`
- [ ] `cd backend && uv run pytest`
