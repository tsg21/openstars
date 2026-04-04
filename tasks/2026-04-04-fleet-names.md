# Fleet Names

Fleets need display names. Each fleet gets a name when created (e.g. "Fleet #1") and players can rename them via a `rename_fleet` command.

This task covers the backend implementation. UI implementation remains a separate task, but the related UI PRDs should be updated here once the backend contract is settled.

## Step 1: Add `name` field to Fleet and PlayerFleet models

- [x] Add `name: str` to `Fleet` in `backend/openstars/engine/models.py`
- [x] Add `name: str | None = None` to `PlayerFleet` in `backend/openstars/engine/models.py` (only set for own fleets; enemy fleets omit it)

Unit tests:
- [x] Update any existing model snapshot or serialisation tests that construct `Fleet` objects directly

Validation:
- [x] `cd backend && uv run pytest`

## Step 2: Assign names during game creation

- [x] In `backend/openstars/engine/create_game.py`, track a per-player fleet counter and name each starting fleet sequentially: "Fleet #1", "Fleet #2", "Fleet #3"
- [x] Pass `name=` when constructing each `Fleet` in the starting fleet loop

Unit tests:
- [x] Update `tests/engine/test_setup.py` to assert each starting fleet has the correct name (e.g. player's first fleet is "Fleet #1")

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_setup.py`

## Step 3: Add `RenameFleetCommand`

- [x] Add `RenameFleetCommand` to `backend/openstars/engine/models.py`:
  - `type: Literal["rename_fleet"] = "rename_fleet"`
  - `fleet_id: str`
  - `name: str` with `Field(min_length=1, max_length=64)`
- [x] Add `RenameFleetCommand` to the `PlayerCommand` discriminated union

Unit tests:
- [x] Add schema tests asserting `rename_fleet` commands deserialise correctly and that an empty or >64-char name is rejected

Validation:
- [x] `cd backend && uv run pytest tests/`

## Step 4: Handle `rename_fleet` in command application

- [x] In `backend/openstars/engine/resolve_steps/commands.py`, add `_apply_rename_fleet_command` that updates `fleet.name` (ownership check; silently ignore unknown/unowned fleets)
- [x] Import `RenameFleetCommand` and dispatch it in `apply_commands`

Unit tests:
- [x] Add unit tests for `_apply_rename_fleet_command`: own fleet gets renamed, unowned fleet is ignored, name is trimmed to model constraints

Validation:
- [x] `cd backend && uv run pytest tests/engine/`

## Step 5: Propagate `name` through fog of war

- [x] In `backend/openstars/engine/fog.py`, set `name=fleet.name` when building the `PlayerFleet` for own fleets
- [x] Enemy `PlayerFleet` entries leave `name` as `None` (name is not visible through fog of war)
- [x] Add an API-level regression test in `tests/server/test_api.py` asserting that fleet names appear in player state and that submitting a `rename_fleet` command changes the name after resolution

Validation:
- [x] `cd backend && uv run pytest tests/`

## Step 6: Final quality gate

- [x] `cd backend && uv run ruff check .`
- [x] `cd backend && uv run pytest`

## Step 7: Refactor commands.py into a subpackage

Split `backend/openstars/engine/resolve_steps/commands.py` into a `commands/` subdirectory with one file per command group. The top-level `commands.py` keeps `apply_commands` and `galaxy_max_coord` and delegates to the subpackage.

- [x] Create `backend/openstars/engine/resolve_steps/commands/__init__.py` — contains `apply_commands` and `galaxy_max_coord` (replaces `commands.py`)
- [x] Create `commands/set_waypoints.py` — `apply_set_waypoints_command`
- [x] Create `commands/rename_fleet.py` — `apply_rename_fleet_command`
- [x] Create `commands/jettison_cargo.py` — `apply_jettison_cargo_command`
- [x] Create `commands/production.py` — all four production queue handlers plus shared helpers (`_owned_planet`, `_queue_index`, `_insert_queue_item`)
- [x] Remove `commands.py` (superseded by the package)

Validation:
- [x] `cd backend && uv run pytest`
- [x] `cd backend && uv run ruff check .`

## Step 8: Update UI PRDs for fleet naming

- [x] Update `docs/prd/63-ui-fleet-detail.md` so the fleet detail header uses the fleet name as the primary label, shows a `Rename` button to the right, and treats the fleet ID as secondary metadata only
- [x] Specify rename UX in the fleet detail PRD, including inline edit behaviour and `rename_fleet` command submission
- [x] Update `docs/prd/64-ui-waypoint-orders.md` so owned fleet names are used in fleet headers, previews, selectors, and error copy anywhere the UI would otherwise surface a fleet ID

Validation:
- [x] Review both PRD diffs for consistency with backend fog-of-war behaviour (own fleets expose `name`; enemy fleets do not)
