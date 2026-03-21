# OpenStars!

Modern web reimagining of Stars! (1995) — turn-based 4X space strategy.

## PRD Documents

The product requirements are in `docs/prd/`:

- `01-overview.md` — Vision, goals, scope, command-and-resolve architecture, phasing strategy

## Key Design Decisions

- **Command-and-resolve architecture** — the UI is an order editor (command phase), the server resolves all players' orders simultaneously (resolution phase). Clients never run game logic. `(previousState, allOrders) → newState` is the core contract.
- **Engine/UI separation** — game engine is pure TypeScript with zero framework dependencies, fully testable in isolation
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

*(To be defined — expected: Vite + React + TypeScript + Tailwind for UI, pure TS for engine)*

## Testing

*(To be configured — expected: Vitest, test files alongside source)*

## Code Quality

*(To be configured — expected: ESLint + TypeScript strict mode)*

- **IMPORTANT**: Always run the linter at the end of each implementation task (after tests pass). If any lint errors are found, fix them immediately before marking the task complete.

## Original Game Reference

The original Stars! (1995) game mechanics are extensively documented:
- [Stars! FAQ](http://www.starsfaq.com/) — technical details on battle engine, minefields, turn order
- [Stars! AutoHost Wiki](http://wiki.starsautohost.org/) — community knowledge base
- [Official Strategy Guide](http://starsautohost.org/strategy/guidef/SSG.htm)
- [Wikipedia](https://en.wikipedia.org/wiki/Stars!)
