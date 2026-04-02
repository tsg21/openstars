# OpenStars!

Modern web reimagining of Stars! (1995) — turn-based 4X space strategy.

## PRD Documents

The product requirements are in `docs/prd/`:

- `01-overview.md` — Vision, goals, scope, command-and-resolve architecture
- `02-galaxy-map.md` — Coordinate system, planet format, galaxy.json, generation algorithm
- `03-turn-lifecycle.md` — Three-file turn cycle (global state → player state → commands), file naming
- `04-engine-conventions.md` — Entity IDs (Feistel cipher), determinism, RNG architecture, engine rules
- `05-global-state.md` — `global-state-T{N}.json` schema (game, players, designs, planets, fleets)
- `06-technical-platform.md` — GCP Cloud Run, GCS, Python backend (FastAPI), React frontend, Docker, CI/CD
- `07-turn-mechanics.md` — Parsec (2^29 coord units), fleet movement (integer math), player commands, Phase 1 resolution pipeline
- `08-ui.md` — Screen layout, Canvas 2D galaxy map, detail panel, event log, waypoint editing, colour system, Phase 2 scope
- `10-fleet-movement.md` — Fleet movement algorithm, warp speed, waypoint consumption, distance units
- `11-scanners.md` — Scanner types (normal/penetrating), visibility rules, fog of war, scan levels
- `12-economy-and-resources.md` — Minerals, mines, factories, resources, concentration depletion
- `phasing.md` — 7-phase plan (fleet control → UI → economy → combat → multiplayer → AI → polish)

Reference docs in `docs/references/` — original Stars! strategy guide, battle engine, resolution order, terminology mapping.

## Key Design Decisions

- **Command-and-resolve architecture** — the UI is an order editor (command phase), the server resolves all players' orders simultaneously (resolution phase). Clients never run game logic. `(previousState, allOrders) → newState` is the core contract.
- **Engine/UI separation** — game engine is separated from the UI, fully testable in isolation
- **Simultaneous turns** — all players submit orders, then the turn resolves at once (core to async multiplayer)
- **Turn resolution order** follows the original Stars! specification (strict, deterministic pipeline)
- **Server authority** — the resolution engine is authoritative; clients receive fog-of-war-filtered state
- **Faithful mechanics** — aim to replicate the depth of the original, not simplify it away

## Working Pattern: Task files

When a new feature is to be added, it needs to be added to the PRD document first. This needs to be reviewed and approved before the implementation can begin.

Once that has been agreed, a new task file should be written in `tasks/`. 

### Task File Organisation

- Task files live in `tasks/` directory
- Each task file is named with ISO-8601 date prefix: `YYYY-MM-DD-feature-name.md`
- Example: `tasks/2026-03-21-galaxy-generation.md`
- This avoids merge conflicts and preserves history
- Completed tasks remain in the directory as a historical record

### Task Execution

Break down work in task files into numbered steps. Each step should include the unit tests relevant for that step — unit tests are not saved for a separate testing step at the end. A dedicated integration test step at the end of the task is fine, but unit tests belong alongside the code they test.

### Task Execution

Implementation follows the numbered steps in the current task file. Each step should be completed and its checkboxes marked `[x]` before moving to the next. When starting a new session:
1. Check `tasks/` directory for the most recent file (sort by date in filename)
2. Read that file to see where we left off
3. Begin the next unchecked step

**IMPORTANT: Always update task files when work is complete**
- Mark completed checkboxes as `[x]` in the task file
- Do this proactively at the end of implementation, not just when asked
- This creates a clear progress record

## Manifest
The repo structure is:
```
openstars/
  frontend/          # React + Vite SPA (TypeScript + Tailwind + shadcn/ui)
  backend/           # Python API server (FastAPI + Pydantic + pytest)
  docker-compose.yaml
  docs/prd/
  docs/references/
  docs/references/manual/README.md # Markdown-extracted copy of the original Stars! manual
  tasks/
```

- **Backend is Python** — FastAPI + Pydantic + pytest.
- **Frontend is React + TypeScript + Vite + Tailwind + shadcn/ui**

## Testing

- **Backend unit tests:** pytest via uv — `cd backend && uv run pytest`
- **Backend integration tests:** pytest against the running backend — `cd backend && uv run pytest int_tests/`
- **Frontend:** Vitest — `cd frontend && npm test`

### Unit vs Integration tests

**Unit tests** (`backend/tests/`) test pure functions and engine modules directly, with no HTTP or I/O. They are fast and run in isolation.

**Integration tests** (`backend/int_tests/`) exercise the full stack over HTTP — they call the real API endpoints against a running backend container, exactly as a client would. They are slower but verify that the entire pipeline (API → engine → storage → response) works end-to-end. See `backend/int_tests/test_game_lifecycle.py` for the established pattern: create a game, submit commands, resolve a turn, assert on the response bodies.

In task files, the final integration test step should use this API-over-HTTP style, not call engine code directly.

## Package Management

- **Backend:** [uv](https://docs.astral.sh/uv/) — fast Python package manager. `pyproject.toml` is the single source of truth for dependencies. `uv.lock` is committed.
  - Install/sync deps: `cd backend && uv sync --all-extras`
  - Run backend commands: `cd backend && uv run <command>`
  - Add a dependency: `cd backend && uv add <package>`
  - Add a dev dependency: `cd backend && uv add --group dev <package>`
- **Frontend:** npm

## Code Quality

- **Backend:** ruff (linting + formatting), run via `uv run ruff check .` and `uv run ruff format --check .`
- **Frontend:** ESLint (strict TypeScript rules)

- **IMPORTANT**: Always run the linter at the end of each implementation task (after tests pass). If any lint errors are found, fix them immediately before marking the task complete.

## API Client — snake_case ↔ camelCase

The API client (`frontend/src/api/client.ts`) automatically converts all backend response keys from `snake_case` to `camelCase` via `keysToCamel` (applied to every response in the `request()` helper). All outgoing command payloads are converted the other way via `keysToSnake`.

This means:
- Backend field `mining_rate` → frontend TypeScript field `miningRate`
- Backend field `scan_level` → frontend TypeScript field `scanLevel`
- All TypeScript types use camelCase; no manual conversion is needed in components or hooks.

## Working with the Frontend

**IMPORTANT**: The frontend is in the `frontend/` directory. All frontend npm commands must be run from that directory.

When working with the frontend:
- Linting: `cd frontend && npm run lint`
- Type checking: `cd frontend && npx tsc --noEmit`
- Dev server: `cd frontend && npm run dev`
- Tests: `cd frontend && npm test`

Or use the shell syntax:
```bash
(cd frontend && npm run lint)
```

The root directory `/Users/tim/code/openstars` does NOT have a package.json — only `frontend/` does.

## Original Game Reference

The original Stars! (1995) game mechanics are extensively documented:
- [Stars! FAQ](http://www.starsfaq.com/) — technical details on battle engine, minefields, turn order
- [Stars! AutoHost Wiki](http://wiki.starsautohost.org/) — community knowledge base
- [Official Strategy Guide](http://starsautohost.org/strategy/guidef/SSG.htm)
- [Wikipedia](https://en.wikipedia.org/wiki/Stars!)
