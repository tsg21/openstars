# Gzipped JSON Storage Blobs (`.json.gz`)

**Backlog:** [backlog.md](./backlog.md) — "Store game state blobs as `.json.gz` in storage adapters to reduce GCS/storage cost while keeping `GameStorage` load/save APIs JSON-shaped"

**PRD:** [docs/prd/06-technical-platform.md](../docs/prd/06-technical-platform.md) — State Storage section

State blobs (galaxy, global state, player state, commands, designs, combat logs, meta) are large, repetitive JSON that compresses very well with gzip. Switching from `.json` to `.json.gz` on disk / in GCS should cut storage cost and egress without any change to the public `GameStorage` API — callers still pass and receive Pydantic models, and `model_dump_json` / `model_validate_json` continue to be the (de)serialisation boundary.

Compression is an adapter-internal concern. `MemoryStorage` keeps plain JSON strings (no benefit in-process); `LocalStorage` and `GCSStorage` write/read gzipped bytes. For a transition window, both adapters also fall back to reading legacy `.json` blobs so existing local dev directories and the production bucket keep working until migrated.

---

## Step 1 — Shared gzip helpers and naming convention

- [ ] Add a small module `backend/openstars/storage/compression.py` exposing:
  - `BLOB_SUFFIX = ".json.gz"`
  - `LEGACY_SUFFIX = ".json"`
  - `encode_json(payload: str) -> bytes` — gzip-compress a JSON string (UTF-8) at a fixed compression level (use `gzip.compress(data, compresslevel=6, mtime=0)` so output is deterministic — no embedded timestamp, which makes diffs/tests stable)
  - `decode_json(data: bytes) -> str` — gzip-decompress to a JSON string; on `gzip.BadGzipFile` raise `ValueError` with a clear message
- [ ] Unit tests in `backend/tests/engine/test_storage_compression.py`:
  - Round-trip: `decode_json(encode_json(s)) == s` for a representative state JSON string
  - Output is deterministic: encoding the same string twice yields identical bytes (no timestamp drift)
  - `decode_json` rejects non-gzipped input with a clear error
  - Compressed size of a realistic global-state JSON (a few KB of repeated structure) is meaningfully smaller than the input — sanity check, not a strict ratio assertion

## Step 2 — `LocalStorage`: write `.json.gz`, read both

- [ ] In `backend/openstars/storage/local.py`:
  - Replace `_write_json(self, path, data: str)` with `_write_blob(self, path, data: str)` that writes `compression.encode_json(data)` via `path.write_bytes(...)` (binary mode); keep the `_safe_path` containment check
  - Replace `_read_json(self, path)` with `_read_blob(self, path)` that:
    1. If `path` (the `.json.gz` path) exists, read bytes and return `compression.decode_json(...)`
    2. Else if a sibling `.json` file exists at the same stem, read it as text and return as-is (legacy fallback)
    3. Else raise `FileNotFoundError`
  - Change every constructed filename from `<name>.json` to `<name>.json.gz` (galaxy, global-state, player-state, commands, meta, design files, combat logs)
  - Update `list_games`: the existence check shifts from `(d / "meta.json").exists()` to "either `meta.json.gz` or legacy `meta.json` exists"
  - Update `list_designs` and `list_combat_logs` to glob for `*.json.gz` AND legacy `*.json`, deduplicate by stem (prefer `.json.gz` when both exist), and strip the appropriate suffix
- [ ] Update existing tests in `backend/tests/engine/test_storage.py`:
  - Tests that read raw bytes from disk (`test_saved_global_state_includes_root_state_version`, `test_saved_player_state_includes_root_state_version`, `test_load_global_state_rejects_missing_state_version`, `test_load_player_state_rejects_newer_state_version`) must read/write `.json.gz` via the gzip helper
  - All round-trip tests should keep passing as-is (the API surface is unchanged)
- [ ] Add new unit tests in the same file:
  - Saved galaxy file lives at `{game_id}/galaxy.json.gz` and is gzip-decodable to valid JSON
  - Loading falls back to a legacy `.json` file when no `.json.gz` is present (write a plain-JSON `meta.json` by hand, then `load_game_meta` succeeds)
  - When both `.json` and `.json.gz` exist for the same stem (mid-migration state), the `.json.gz` version wins
  - `list_designs` / `list_combat_logs` return the union of legacy + new blobs without duplicates

## Step 3 — `GCSStorage`: write `.json.gz`, read both

- [ ] In `backend/openstars/storage/gcs.py`:
  - Change `_write_json(name, data, *, create_only=False)` to `_write_blob(name, data, *, create_only=False)` that uploads `compression.encode_json(data)` with `content_type="application/json"` and `content_encoding="gzip"` (so GCS records the encoding correctly and any direct download via `gsutil cp` / browser will transparently decompress); preserve the `if_generation_match=0` behaviour for create-only writes
  - Change `_read_json(name)` to `_read_blob(name)` that:
    1. Tries `name` (the `.json.gz` form); on success reads bytes via `blob.download_as_bytes()` and decodes with `compression.decode_json`
    2. On `NotFound`, falls back to the legacy `.json` name (sibling-stem) via `download_as_text`
    3. If neither exists, raises `FileNotFoundError`
  - Note: `download_as_bytes()` is required because `download_as_text()` would auto-decode `Content-Encoding: gzip` and we want the raw compressed bytes to feed our helper. Verify in code review which behaviour the client library actually exhibits — if `download_as_text` already returns the decoded JSON string when `content_encoding="gzip"` is set, we can use it directly and skip the helper for reads. Pick one path and document it in a brief comment.
  - Change every constructed object name from `<name>.json` to `<name>.json.gz`
  - Update `list_games`, `list_designs`, `list_combat_logs` to match `.json.gz` AND legacy `.json` blobs, deduplicating by stem (prefer `.json.gz` when both exist)
- [ ] Update existing tests in `backend/tests/engine/test_storage_gcs.py`:
  - `FakeBlob.upload_from_string` accepts a `content_encoding` kwarg and stores it on the object dict
  - Add a `download_as_bytes()` method to `FakeBlob` (or update reads to match whichever path Step 3 chose)
  - Tests reading `bucket.objects[...]["data"]` directly (the state-version tests, the `_write_json` calls inside `test_load_*_rejects_*` tests) must construct gzipped bytes via the helper
- [ ] Add new unit tests:
  - Saved global state blob is stored at `{game_id}/state/global-state-T0.json.gz` with `content_type="application/json"` and `content_encoding="gzip"`
  - Loading falls back to a legacy `.json` blob when no `.json.gz` exists (manually inject a plain-JSON object into the fake bucket, then `load_game_meta` succeeds)
  - `list_games` returns games discovered via `.json.gz` meta blobs and via legacy `.json` meta blobs, with no duplicates when both exist for the same game

## Step 4 — `MemoryStorage`: no change beyond key suffix consistency

- [ ] Decision: `MemoryStorage` continues to store raw JSON strings — gzipping in-process buys nothing, costs CPU, and complicates the inspect-the-dict tests. Keep `_put_json` / `_get_json` as-is.
- [ ] However, change keys from `…/foo.json` to `…/foo.json.gz` so that `MemoryStorage` mirrors the production layout (anything that does prefix matching across adapters stays consistent — list_games, etc.)
- [ ] Update `backend/tests/engine/test_storage_memory.py` accordingly (key strings in any direct-dict-inspection asserts).
- [ ] Update `list_games` in memory.py to match the `.json.gz` suffix (still no legacy fallback needed — memory storage is per-process).

## Step 5 — Update PRD 06

- [ ] In `docs/prd/06-technical-platform.md`, update the bucket layout block to show `.json.gz` filenames throughout
- [ ] Add a short paragraph under "State Storage — Google Cloud Storage" explaining:
  - Blobs are stored gzip-compressed (`.json.gz`)
  - GCS blob metadata uses `Content-Type: application/json` + `Content-Encoding: gzip` so direct downloads transparently decompress
  - The `GameStorage` API still exchanges Pydantic models / JSON strings — compression is an adapter-internal concern
- [ ] Re-index RAG: `scripts/rag-index`

## Step 6 — One-shot migration script for existing data

A small CLI to compress legacy `.json` blobs in place and (optionally) delete the originals. Useful for the production bucket and any local dev directories that pre-date this change. The legacy-fallback read path in Steps 2 & 3 means the script can be run lazily — it's not blocking for deployment.

- [ ] Add `backend/scripts/migrate_storage_to_gzip.py` with:
  - `--backend {local,gcs}` flag
  - `--path <dir>` for local, `--bucket <name>` for GCS
  - `--dry-run` (default) and `--apply` flags
  - `--delete-originals` flag (default off — leave both copies until verified)
  - Walks all blobs ending in `.json` (under any game's directory tree), produces a `.json.gz` sibling, and optionally deletes the `.json`
  - Skips blobs that already have a `.json.gz` sibling
  - Reports counts: scanned, compressed, skipped, deleted, total bytes saved
- [ ] Unit tests in `backend/tests/scripts/test_migrate_storage_to_gzip.py`:
  - Dry run on a `tmp_path` populated with mixed `.json` / `.json.gz` reports the right counts and writes nothing
  - `--apply` produces valid gzip blobs that round-trip back to the original JSON via the helper from Step 1
  - `--apply --delete-originals` removes the legacy files; without that flag, both copies remain
  - Existing `.json.gz` siblings are skipped (idempotent)

## Step 7 — Integration test: end-to-end resolve cycle on disk

- [ ] In `backend/tests/server/` (an existing API integration file or a new one), add a small test that:
  - Configures the API to use `LocalStorage` against a `tmp_path`
  - Creates a game, submits commands for both players, resolves a turn
  - Asserts the on-disk files for that game all end in `.json.gz`
  - Asserts at least one of those files is valid gzip and decodes to JSON whose root is an object containing the expected keys (e.g. global-state has `state_version` and `game`)
  - Asserts no `.json` (without `.gz`) blobs were written for the new game

## Step 8 — Mark backlog item complete

- [ ] Tick the box in `tasks/backlog.md` for "Store game state blobs as `.json.gz` in storage adapters…"
