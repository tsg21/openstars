# 2026-03-29 — GCS Storage Adapter

**Goal:** Implement a production `GCSStorage` adapter that satisfies the existing `GameStorage` contract and can be selected by backend configuration without changing route or engine code.
**Relevant PRDs:** 06 (technical platform), 03 (turn lifecycle), 05 (global state), 09/50 (API)
**Status:** ⏸️ Planned

## Current State

- `storage/base.py` defines the `GameStorage` interface used by the server layer.
- `storage/local.py` implements the contract against the local filesystem.
- `server/deps.py` always returns `LocalStorage`; there is no storage backend selection yet.
- PRD 06 now documents `meta.json` as part of the storage contract and keeps `preferences/` explicitly out of Phase 1 scope.

## Step 1 — Add GCS dependency and configuration

- [x] Add `google-cloud-storage` to `backend/pyproject.toml`
- [x] Extend backend config/dependency wiring so `get_storage()` selects:
  - `LocalStorage` when `STORAGE_BACKEND=local`
  - `GCSStorage` when `STORAGE_BACKEND=gcs`
- [x] Fail fast with a clear error when `STORAGE_BACKEND` is missing or unsupported
- [x] Read required GCS settings from environment:
  - `GCS_BUCKET_NAME`
- [x] Fail fast with a clear error when GCS mode is selected but required configuration is missing

**Output:** Backend can construct the correct storage adapter from environment configuration.

---

## Step 2 — Implement `storage/gcs.py`

- [x] Create `GCSStorage(bucket_name)` implementing `GameStorage`
- [x] Mirror the same object layout as `LocalStorage`:
  - `{game_id}/galaxy.json`
  - `{game_id}/meta.json`
  - `{game_id}/state/global-state-T{N}.json`
  - `{game_id}/players/player-state-{username}-T{N}.json`
  - `{game_id}/commands/player-command-{username}-T{N}.json`
- [x] Use Pydantic JSON serialisation/deserialisation just like local storage
- [x] Validate `game_id` and `username` path segments consistently with local storage
- [x] Map missing blobs to `FileNotFoundError`
- [x] Implement `list_games()` by discovering game prefixes that contain `meta.json`

**Output:** Feature-complete GCS adapter with parity against the local storage behaviour.

---

## Step 3 — Handle write safety for resolution-critical files

- [x] Use GCS generation preconditions when writing turn-resolution outputs that must not be duplicated:
  - `state/global-state-T{N}.json`
- [x] Decide and document overwrite policy for:
  - command submissions
  - `meta.json`
  - initial game creation files
- [x] Translate precondition failures into a Python exception shape the server can handle cleanly

**Output:** GCS writes preserve the single-writer turn resolution guarantees from PRD 06.

---

## Step 4 — Test adapter parity

- [x] Add unit tests for `GCSStorage` path generation and round-trip JSON behaviour
- [x] Mock the GCS client rather than requiring live cloud infrastructure
- [x] Cover:
  - save/load for galaxy, global state, player state, commands, metadata
  - `has_commands()`
  - `list_games()`
  - missing-object behaviour
  - generation-precondition conflict on protected writes
- [x] Keep the existing `LocalStorage` tests passing unchanged

**Output:** The storage contract is exercised across both adapters with deterministic tests.

---

## Step 5 — Wire into server and docs

- [x] Update server tests to verify backend selection logic in `get_storage()`
- [x] Add a helper script for creating the game-state bucket and granting backend access
- [ ] Document local vs production storage configuration in `README.md` if needed
- [ ] Revisit `docker-compose.yaml` / deployment env examples only if the adapter is being enabled immediately

**Output:** Backend configuration is ready for production use and documented.

## Notes

- `storage/paths.py` now holds the shared segment validation logic used by both storage adapters.
- `save_global_state()` in `GCSStorage` is create-only and raises `FileExistsError` on generation-precondition conflicts.

## Decisions

- `GCSStorage` uses the bucket root directly; no configurable object prefix in this task.
- Strict create-only semantics apply only to the authoritative `state/global-state-T{N}.json` file.
- `preferences/` remains out of scope for this task and the Phase 1 storage interface.
