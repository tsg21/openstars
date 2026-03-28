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
- `phasing.md` — 7-phase plan (fleet control → UI → economy → combat → multiplayer → AI → polish)

Reference docs in `docs/references/` — original Stars! strategy guide, battle engine, resolution order, terminology mapping.

## Key Design Decisions

- **Command-and-resolve architecture** — the UI is an order editor (command phase), the server resolves all players' orders simultaneously (resolution phase). Clients never run game logic. `(previousState, allOrders) → newState` is the core contract.
- **Engine/UI separation** — game engine is separated from the UI, fully testable in isolation
- **Simultaneous turns** — all players submit orders, then the turn resolves at once (core to async multiplayer)
- **Turn resolution order** follows the original Stars! specification (strict, deterministic pipeline)
- **Server authority** — the resolution engine is authoritative; clients receive fog-of-war-filtered state
- **Faithful mechanics** — aim to replicate the depth of the original, not simplify it away

## Working Pattern

When a new feature is to be added, it needs to be added to the PRD document first, along with a new task file in `tasks/`. This needs to be reviewed and approved before the implementation can begin.

### Task File Organisation

- Task files live in `tasks/` directory
- Each task file is named with ISO-8601 date prefix: `YYYY-MM-DD-feature-name.md`
- Example: `tasks/2026-03-21-galaxy-generation.md`
- This avoids merge conflicts and preserves history
- Completed tasks remain in the directory as a historical record

### Task Execution

Implementation follows the numbered steps in the current task file. Each step should be completed and its checkboxes marked `[x]` before moving to the next. When starting a new session:
1. Check `tasks/` directory for the most recent file (sort by date in filename)
2. Read that file to see where we left off
3. Begin the next unchecked step

**IMPORTANT: Always update task files when work is complete**
- Mark completed checkboxes as `[x]` in the task file
- Add section status markers (✅ for complete, ⏸️ for paused/deferred)
- Add notes explaining any deferred work or partial completion
- Do this proactively at the end of implementation, not just when asked
- This creates a clear progress record

## App Structure

Per PRD 06, the repo structure is:

```
openstars/
  frontend/          # React + Vite SPA (TypeScript + Tailwind + shadcn/ui)
  backend/           # Python API server (FastAPI + Pydantic + pytest)
    openstars/
      engine/        # Pure game engine (no framework deps)
      server/        # FastAPI app, routes, middleware
      storage/       # GCS / local file storage adapter
    tests/
  docker-compose.yaml
  docs/prd/
  docs/references/
  tasks/
```

- **Backend is Python** — FastAPI + Pydantic + pytest. Tim's collaborator knows Python.
- **Frontend is React + TypeScript + Vite + Tailwind + shadcn/ui**
- **Engine** lives inside backend package but has no web/storage dependencies — pure Python, testable in isolation

## Testing

- **Backend:** pytest (engine unit tests + API integration tests)
- **Frontend:** Vitest

## Code Quality

- **Backend:** ruff (linting + formatting)
- **Frontend:** ESLint (strict TypeScript rules)

- **IMPORTANT**: Always run the linter at the end of each implementation task (after tests pass). If any lint errors are found, fix them immediately before marking the task complete.

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
