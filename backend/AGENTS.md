# Backend Instructions

These notes apply to backend changes under `backend/`.

## Working With The Backend

- Backend stack: Python + FastAPI + Pydantic + pytest.
- Backend package management uses `uv`.
- `pyproject.toml` is the single source of truth for dependencies.
- `uv.lock` is committed.

## Package Management

- Never invoke `python`, `python3`, or `pytest` directly.
- Always use `uv run --all-extras` so the correct environment and dependencies are used.
- Run backend commands: `cd backend && uv run --all-extras <command>`
- Add a dependency: `cd backend && uv add <package>`
- Add a dev dependency: `cd backend && uv add --group dev <package>`

## Testing

**IMPORTANT: Always use `uv run` — never `python`, `python3`, `pytest`, `python -m pytest`, or `python3 -m pytest` directly.**

- Backend unit tests: `cd backend && uv run pytest`
- Backend integration tests: `./backend/int_tests/run.sh` (uses `STORAGE_BACKEND=memory` — does not exercise the Firestore backend). It runs the backend as a bare local process but still starts the Firebase auth emulator in docker, because the suite needs real ID tokens.
- Backend integration tests against the real Firestore emulator (mirrors CI's `integration` job): `./backend/int_tests/run_docker.sh`. Always use this script rather than driving `docker compose -f int_tests/docker-compose.yaml` by hand — it builds, waits for health, tears down, and dumps container logs on failure.

### Authentication in integration tests

Identity comes from a verified Google ID token, so integration tests sign in
rather than asserting a username:

- `int_tests/auth.py` mints tokens from the auth emulator's Identity Toolkit
  REST surface, one sign-in per email, cached for the run.
- **Player names are emails.** `GameClient(player="alice@example.com")` sends
  `Authorization: Bearer <token>`; the same string is what `players=[...]` on
  `create_game` must contain, and what `planet.owner` compares equal to.
- `GameClient()` with no player is unauthenticated — every player-scoped route
  answers it with 401.
- `GameClient(player=..., override=...)` sends `X-Player`. That header is an
  override *request*, not an identity, and is honoured only on games created
  with `allow_player_override=True`.
- `create_game` needs a signed-in caller, but the caller does not have to be a
  participant.

## Unit vs Integration Tests

- Unit tests in `backend/tests/` should test pure functions and engine modules directly, with no HTTP or I/O.
- Integration tests in `backend/int_tests/` should exercise the full stack over HTTP against the real backend container.
- Debug logs for integration runs are written to `backend/int_tests/logs/docker-compose.log`.
- See `backend/int_tests/test_game_lifecycle.py` for the established integration-test pattern.
- In task files, the final integration-test step should use this API-over-HTTP style rather than calling engine code directly.

## Code Quality

**IMPORTANT: The CI ruff check will fail the PR if these don't pass. Always run both before pushing:**

- Linting: `cd backend && uv run ruff check .`
- Format check: `cd backend && uv run ruff format --check .`
- Auto-fix format issues: `cd backend && uv run ruff format .`
- Auto-fix lint issues: `cd backend && uv run ruff check --fix .`

Run both checks at the end of every backend implementation task and fix any issues before considering the work complete.

## Style: don't paper over impossible states

- Don't accept `None` (or any "missing" sentinel) for an argument that is always supplied in practice, just to provide a quiet fallback. Examples to avoid: `def foo(race: Race | None)` returning a default when `race is None`; `dict.get(key)` followed by a "if missing then …" branch when the key is guaranteed present by the surrounding invariants.
- Prefer the type-honest signature: take `Race`, not `Race | None`. Use `dict[key]` (raise `KeyError`) instead of `.get(key)` when the key must exist. Let invariants surface as errors so real bugs aren't silently absorbed.
- Only relax this at genuine system boundaries: untrusted user input, external API responses, on-disk data that may predate the current schema. Internal engine code should trust its own invariants.
- Counter-example (do **not** write this):
  ```python
  def _fuel_multiplier_x100(race: Race | None) -> int:
      if race is not None and LRT.IMPROVED_FUEL_EFFICIENCY in race.lrts:
          return 85
      return 100
  ```
  If every caller in turn ≥ 1 has a race, take `Race` directly. A missing race after turn 0 is a bug; let it raise.
