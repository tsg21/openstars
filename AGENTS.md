# OpenStars!

Modern web reimagining of Stars! (1995) — turn-based 4X space strategy.

## PRD Documents

The product requirements are in `docs/prd/`. [listing](docs/prd/README.md)

Reference docs in `docs/references/` — original Stars! strategy guide, battle engine, resolution order, terminology mapping.

### PRD authoring model

- PRDs represent the **current canonical view** of the game, not incremental deltas.
- Each PRD should read as a complete specification for its area as of "now".
- When requirements change, update the relevant PRD(s) in place so they remain accurate and internally consistent.
- Avoid wording that frames a PRD as "phase-only" if that wording would make the document stale after later decisions.
- Cross-PRD references should be used for ownership boundaries, but readers should still be able to understand the current contract from the owning PRD without reconstructing historical steps.

### Code snippets in PRDs

PRDs should **not** contain Python/TypeScript model stubs, class definitions, or implementation pseudocode. These duplicate the actual code, go stale, and don't help convey game mechanics. Instead, describe schema changes as prose field lists.

Code snippets that **are** appropriate in PRDs:
- **Formulas and algorithms** — mathematical specifications that define game mechanics (e.g. mineral spending proportional algorithm, habitability calculation, fuel consumption formula)
- **JSON examples** — request/response shapes, event payloads, data file examples that illustrate the API contract
- **ASCII diagrams** — architecture diagrams, UI wireframes, pipeline summaries

## Key Design Decisions

- **Command-and-resolve architecture** — the UI is an order editor (command phase), the server resolves all players' orders simultaneously (resolution phase). Clients never run game logic. `(previousState, allOrders) → newState` is the core contract.
- **Engine/UI separation** — game engine is separated from the UI, fully testable in isolation
- **Simultaneous turns** — all players submit orders, then the turn resolves at once (core to async multiplayer)
- **Turn resolution order** follows the original Stars! specification (strict, deterministic pipeline)
- **Server authority** — the resolution engine is authoritative; clients receive fog-of-war-filtered state
- **Faithful mechanics** — aim to replicate the depth of the original, not simplify it away

## Language Conventions

- Use **British English** in code, docs, UI copy, and task files where practical.
- Example: prefer `colonise` / `colonisation` over `colonize` / `colonization`.

## RAG Search

Before doing research or design work, query the local RAG index to find relevant PRD sections, task history, and reference docs:

```bash
scripts/rag-query "<topic>" -n 5
```

There's no need to do this when simply following implementation steps.

Re-index after adding or editing docs:

```bash
scripts/rag-index
```

## Working Pattern: Task files

When a new feature is to be added, it needs to be added to the PRD document first. This needs to be reviewed and approved before the implementation can begin.

Once that has been agreed, a new task file should be written in `tasks/`. 

### Task File Organisation

- Task files live in `tasks/` directory
- Each task file is named with ISO-8601 date prefix: `YYYY-MM-DD-feature-name.md`
- The date is always the date that the file was created.
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

## Frontend Instructions

When making frontend edits under `frontend/`, always read `frontend/AGENTS.md` first and follow it as the primary frontend-specific guidance.

## Backend Instructions

When making backend edits under `backend/`, always read `backend/AGENTS.md` first and follow it as the primary backend-specific guidance.

## Original Game Reference

The original Stars! (1995) game mechanics are extensively documented:
- [Stars! FAQ](http://www.starsfaq.com/) — technical details on battle engine, minefields, turn order
- [Stars! AutoHost Wiki](http://wiki.starsautohost.org/) — community knowledge base
- [Official Strategy Guide](http://starsautohost.org/strategy/guidef/SSG.htm)
- [Wikipedia](https://en.wikipedia.org/wiki/Stars!)

## Cursor Cloud specific instructions

### Services overview

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| Backend API | `cd backend && STORAGE_BACKEND=memory uv run uvicorn openstars.server.main:app --host 127.0.0.1 --port 8080` | 8080 | Use `STORAGE_BACKEND=memory` for dev (no database needed) |
| Frontend dev server | `cd frontend && npm run dev` | 5173 | Vite proxies `/api/*` to `http://localhost:8080` |

No databases, caches, or external infrastructure required for local development. The backend stores game state in memory (or local filesystem with `STORAGE_BACKEND=local`).

### Runtime requirements

- **Node.js >=24 <25** — install via `nvm install 24 && nvm use 24`
- **Python >=3.12** — pre-installed on the VM
- **uv** — install via `pip install uv` if not present; ensure `$HOME/.local/bin` is on `PATH`

### Testing preference
- Default to terminal-driven automated checks (`pytest`, `npm test`, `typecheck`, `lint`) for normal implementation work.
- Do **not** run browser/manual smoke tests (including `computerUse`) unless the user explicitly asks for manual/UI verification in that session.
- Do **not** start the frontend dev server (`npm run dev`) unless the user explicitly asks for it; the user normally runs it separately.
- If manual browser testing is skipped due to this preference, call that out briefly in the final summary.

### Gotchas

- The frontend `package.json` requires Node >=24; Node 22 (the VM default) will not work.
- Always use `uv run` for backend commands, never bare `python` or `pytest`.
- The backend health endpoint is at `/api/v1/health`, not `/api/health` or `/`.
- When running the backend with `STORAGE_BACKEND=memory`, game state is lost on restart.
