# State File Versioning

Add a root-level `state_version` field to all persisted state JSON files so the backend has an explicit schema version to inspect before loading old saves. Start with version `1`.

This is planning only for now. Per the repo workflow, the PRD/schema updates in Step 1 should be reviewed before implementation begins.

## Scope

- Persist `state_version: 1` in:
  - `global-state-T{N}.json`
  - `player-state-{username}-T{N}.json`
- Keep the storage adapter interface JSON-shaped
- Introduce a single backend-owned state version constant
- Add a narrow upgrade hook so future work can transform older state payloads before model validation

## Non-Goals

- No gameplay changes
- No command file versioning yet
- No galaxy or meta file versioning yet
- No multi-version migration chain beyond the initial `1` contract

## Step 1: Update the PRDs for versioned state files

Document the new root field and the intended compatibility contract before changing the backend.

- [x] Update `docs/prd/05-global-state.md`:
  - [x] add `state_version` to the root schema examples and field descriptions
  - [x] state that the current version is `1`
  - [x] note that future backend versions may upgrade older saved state payloads before validation
- [x] Update `docs/prd/03-turn-lifecycle.md` or `docs/prd/06-technical-platform.md` (whichever is the better fit after review):
  - [x] state that persisted state files are self-versioned
  - [x] describe upgrade-on-load at a high level
- [x] Update `docs/prd/50-api.md` only if needed to clarify that this is a storage concern, not a response-body change
  - [x] No change needed: this does not alter the HTTP response schema

Validation:
- [x] Docs sanity pass: all state-file examples consistently use `state_version: 1`

## Step 2: Add versioned state models and a shared constant

Make the version part of the canonical backend schema.

- [x] Add a shared constant such as `STATE_VERSION = 1` in an appropriate backend module
- [x] Extend `GlobalState` with `state_version: int = STATE_VERSION`
- [x] Extend `PlayerState` with `state_version: int = STATE_VERSION`
- [x] Ensure newly created states inherit the default without every call site having to pass it manually

Unit tests:
- [x] Add or update model tests asserting `GlobalState` and `PlayerState` serialise with `state_version: 1` at the root
- [x] Add a regression test confirming existing constructors used by game creation and fog-of-war derivation still produce valid models with the defaulted version

Validation:
- [x] `cd backend && uv run pytest tests/`

## Step 3: Add a version-aware load path for state files

Introduce a small upgrade layer now so later schema changes have a home.

- [x] Add a backend module for state-file versioning, for example `backend/openstars/storage/state_versioning.py`
- [x] Implement helpers along these lines:
  - [x] `load_state_payload(raw_json: str) -> dict`
  - [x] `upgrade_global_state_payload(payload: dict) -> dict`
  - [x] `upgrade_player_state_payload(payload: dict) -> dict`
- [x] Behaviour:
  - [x] if `state_version` is missing, treat the payload as unsupported for now and fail with a clear error
  - [x] if `state_version == 1`, pass through unchanged
  - [x] if `state_version` is newer than the backend supports, fail with a clear error
- [x] Keep upgrade functions pure and dictionary-in/dictionary-out so future migrations stay easy to test

Unit tests:
- [x] Version `1` payload round-trips unchanged
- [x] Missing `state_version` raises a clear, targeted error
- [x] Unknown future `state_version` raises a clear, targeted error

Validation:
- [x] `cd backend && uv run pytest tests/storage/ tests/server/ tests/engine/`

## Step 4: Route storage adapters through the versioned loader

Make every persisted state read path use the same upgrade-aware logic.

- [x] Update `backend/openstars/storage/local.py`:
  - [x] `load_global_state()` uses the global-state upgrade helper before `GlobalState.model_validate(...)`
  - [x] `load_player_state()` uses the player-state upgrade helper before `PlayerState.model_validate(...)`
- [x] Update `backend/openstars/storage/memory.py` the same way
- [x] Update `backend/openstars/storage/gcs.py` the same way
- [x] Leave save paths JSON-shaped; saving version `1` should just serialise the new root field

Unit tests:
- [x] Local storage saves state files containing root `state_version: 1`
- [x] Memory storage saves state blobs containing root `state_version: 1`
- [x] Storage load tests cover the upgrade helper path rather than only `model_validate_json`
- [x] GCS adapter tests cover the same read/write contract if the current test setup already mocks blob reads

Validation:
- [x] `cd backend && uv run pytest tests/storage/`

## Step 5: Verify end-to-end state generation and loading

Confirm that created games and resolved turns persist versioned state cleanly.

- [x] Add or update an integration-style backend test around game creation and turn resolution
- [x] Assert that:
  - [x] turn 0 global state contains `state_version: 1`
  - [x] derived player state files contain `state_version: 1`
  - [x] loading those files through the normal storage interface still succeeds

Unit tests:
- [x] Extend the most relevant server/storage test to inspect the persisted JSON, not just the loaded models

Validation:
- [x] `cd backend && uv run pytest`

## Step 6: Final quality gate

- [x] `cd backend && uv run ruff check .`
- [x] `cd backend && uv run ruff format --check .`
- [x] `cd backend && uv run pytest`

## Notes

- Use `state_version` in snake_case to match backend/storage naming conventions
- Keep the version at the JSON root, not nested under `game`, so schema upgrades can happen before any specific model section is trusted
- The first implementation should be intentionally boring: write `1`, recognise `1`, and fail loudly for anything else
- Once this lands, future save-format changes should add migrations to the dedicated upgrade module rather than scattering compatibility logic through storage adapters or route handlers
