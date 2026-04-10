# Backend Instructions

These notes apply to backend changes under `backend/`.

## Working With The Backend

- Backend stack: Python + FastAPI + Pydantic + pytest.
- Backend package management uses `uv`.
- `pyproject.toml` is the single source of truth for dependencies.
- `uv.lock` is committed.

## Package Management

- Never invoke `python`, `python3`, or `pytest` directly.
- Always use `uv run` so the correct environment and dependencies are used.
- Install or sync dependencies: `cd backend && uv sync --all-extras`
- At the start of a new session (and before reporting `uv run` test/lint results), run `uv sync --all-extras` to ensure the environment matches `uv.lock`.
- Run backend commands: `cd backend && uv run <command>`
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
