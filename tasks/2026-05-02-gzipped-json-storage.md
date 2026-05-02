# Gzipped JSON Storage Blobs (`.json.gz`)

**Backlog:** [backlog.md](./backlog.md) — "Store game state blobs as `.json.gz` in storage adapters to reduce GCS/storage cost while keeping `GameStorage` load/save APIs JSON-shaped"

**PRD:** [docs/prd/06-technical-platform.md](../docs/prd/06-technical-platform.md) — State Storage section

State blobs (galaxy, global state, player state, commands, designs, combat logs, meta) are large, repetitive JSON that compresses very well with gzip. Switching from `.json` to `.json.gz` on disk / in GCS should cut storage cost and egress without any change to the public `GameStorage` API — callers still pass and receive Pydantic models, and `model_dump_json` / `model_validate_json` continue to be the (de)serialisation boundary.

Compression is an adapter-internal concern. `MemoryStorage` keeps plain JSON strings (no benefit in-process); `LocalStorage` and `GCSStorage` write/read gzipped bytes.

**No backwards compatibility / migration:** existing games (local dev directories and the production bucket) will be cleared down before the new code ships. Adapters only know about `.json.gz` — no legacy `.json` read path, no migration script.

---

## Step 1 — Shared gzip helpers and naming convention

- [x] Add a small module `backend/openstars/storage/compression.py` exposing:
  - `BLOB_SUFFIX = ".json.gz"`
  - `encode_json(payload: str) -> bytes` — gzip-compress a JSON string (UTF-8) at a fixed compression level (use `gzip.compress(data, compresslevel=6, mtime=0)` so output is deterministic — no embedded timestamp, which makes diffs/tests stable)
  - `decode_json(data: bytes) -> str` — gzip-decompress to a JSON string; on `gzip.BadGzipFile` raise `ValueError` with a clear message
- [x] Unit tests in `backend/tests/engine/test_storage_compression.py`:
  - Round-trip: `decode_json(encode_json(s)) == s` for a representative state JSON string
  - Output is deterministic: encoding the same string twice yields identical bytes (no timestamp drift)
  - `decode_json` rejects non-gzipped input with a clear error
  - Compressed size of a realistic global-state JSON (a few KB of repeated structure) is meaningfully smaller than the input — sanity check, not a strict ratio assertion

## Step 2 — `LocalStorage`: write and read `.json.gz`

- [x] In `backend/openstars/storage/local.py`:
  - Replace `_write_json(self, path, data: str)` with `_write_blob(self, path, data: str)` that writes `compression.encode_json(data)` via `path.write_bytes(...)` (binary mode); keep the `_safe_path` containment check
  - Replace `_read_json(self, path)` with `_read_blob(self, path)` that reads bytes and returns `compression.decode_json(...)`; raise `FileNotFoundError` when the path is missing
  - Change every constructed filename from `<name>.json` to `<name>.json.gz` (galaxy, global-state, player-state, commands, meta, design files, combat logs)
  - Update `list_games`: existence check shifts from `(d / "meta.json").exists()` to `(d / "meta.json.gz").exists()`
  - Update `list_designs` and `list_combat_logs` to glob for `*.json.gz` and strip the `.json.gz` suffix
- [x] Update existing tests in `backend/tests/engine/test_storage.py`:
  - Tests that read raw bytes from disk (`test_saved_global_state_includes_root_state_version`, `test_saved_player_state_includes_root_state_version`, `test_load_global_state_rejects_missing_state_version`, `test_load_player_state_rejects_newer_state_version`) must read/write `.json.gz` via the gzip helper
  - All round-trip tests should keep passing as-is (the API surface is unchanged)
- [x] Add a new unit test:
  - Saved galaxy file lives at `{game_id}/galaxy.json.gz` and its bytes are gzip-decodable to valid JSON

## Step 3 — `GCSStorage`: write and read `.json.gz`

- [x] In `backend/openstars/storage/gcs.py`:
  - Change `_write_json(name, data, *, create_only=False)` to `_write_blob(name, data, *, create_only=False)` that uploads `compression.encode_json(data)` with `content_type="application/json"` and `content_encoding="gzip"` (so GCS records the encoding correctly and any direct download via `gsutil cp` / browser will transparently decompress); preserve the `if_generation_match=0` behaviour for create-only writes
  - Change `_read_json(name)` to `_read_blob(name)` that reads bytes via `blob.download_as_bytes()` and decodes with `compression.decode_json`; convert `NotFound` to `FileNotFoundError` as today
  - Note: `download_as_bytes()` is required because `download_as_text()` would auto-decode `Content-Encoding: gzip` and we want the raw compressed bytes to feed our helper. Verify in code review which behaviour the client library actually exhibits — if `download_as_text` already returns the decoded JSON string when `content_encoding="gzip"` is set, we can use it directly. Pick one path and document it in a brief comment.
  - Change every constructed object name from `<name>.json` to `<name>.json.gz`
  - Update `list_games`, `list_designs`, `list_combat_logs` to match `.json.gz` blobs and strip the `.json.gz` suffix
- [x] Update existing tests in `backend/tests/engine/test_storage_gcs.py`:
  - `FakeBlob.upload_from_string` accepts a `content_encoding` kwarg and stores it on the object dict
  - Add a `download_as_bytes()` method to `FakeBlob` (or update reads to match whichever path Step 3 chose)
  - Tests reading `bucket.objects[...]["data"]` directly (the state-version tests, the `_write_json` calls inside `test_load_*_rejects_*` tests) must construct gzipped bytes via the helper
- [x] Add a new unit test:
  - Saved global state blob is stored at `{game_id}/state/global-state-T0.json.gz` with `content_type="application/json"` and `content_encoding="gzip"`

## Step 4 — `MemoryStorage`: align key suffix

- [x] Decision: `MemoryStorage` continues to store raw JSON strings — gzipping in-process buys nothing, costs CPU, and complicates the inspect-the-dict tests. Keep `_put_json` / `_get_json` as-is.
- [x] Change keys from `…/foo.json` to `…/foo.json.gz` so that `MemoryStorage` mirrors the production layout (anything that does prefix matching across adapters stays consistent — list_games, etc.)
- [x] Update `list_games` in memory.py to match the `.json.gz` suffix
- [x] Update `backend/tests/engine/test_storage_memory.py` accordingly (key strings in any direct-dict-inspection asserts)

## Step 5 — Update PRD 06

- [x] In `docs/prd/06-technical-platform.md`, update the bucket layout block to show `.json.gz` filenames throughout
- [x] Add a short paragraph under "State Storage — Google Cloud Storage" explaining:
  - Blobs are stored gzip-compressed (`.json.gz`)
  - GCS blob metadata uses `Content-Type: application/json` + `Content-Encoding: gzip` so direct downloads transparently decompress
  - The `GameStorage` API still exchanges Pydantic models / JSON strings — compression is an adapter-internal concern
- [x] Re-index RAG: `scripts/rag-index`

## Step 6 — Integration test: end-to-end resolve cycle on disk

- [x] In `backend/tests/server/` (an existing API integration file or a new one), add a small test that:
  - Configures the API to use `LocalStorage` against a `tmp_path`
  - Creates a game, submits commands for both players, resolves a turn
  - Asserts the on-disk files for that game all end in `.json.gz`
  - Asserts at least one of those files is valid gzip and decodes to JSON whose root is an object containing the expected keys (e.g. global-state has `state_version` and `game`)
  - Asserts no `.json` (without `.gz`) blobs were written for the new game

## Step 7 — Clear existing data and mark backlog item complete

- [x] Wipe any local dev storage directories (typically `backend/data/` or wherever `STORAGE_BACKEND=local` writes) before running the new code
- [ ] Wipe the production GCS bucket of all existing game blobs as part of the deploy (coordinate with the deploy step — this is destructive and irreversible)
- [x] Tick the box in `tasks/backlog.md` for "Store game state blobs as `.json.gz` in storage adapters…"
