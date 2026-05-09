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

- Backend unit tests: `cd backend && uv run pytest`
- Backend integration tests: `./backend/int_tests/run.sh`

## Unit vs Integration Tests

- Unit tests in `backend/tests/` should test pure functions and engine modules directly, with no HTTP or I/O.
- Integration tests in `backend/int_tests/` should exercise the full stack over HTTP against the real backend container.
- Debug logs for integration runs are written to `backend/int_tests/logs/docker-compose.log`.
- See `backend/int_tests/test_game_lifecycle.py` for the established integration-test pattern.
- In task files, the final integration-test step should use this API-over-HTTP style rather than calling engine code directly.

## Code Quality

- Linting: `cd backend && uv run ruff check .`
- Format check: `cd backend && uv run ruff format --check .`
- Always run the backend linter & format check at the end of backend implementation work and fix any issues before considering the work complete.

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
