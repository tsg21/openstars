# Altair combat prototype — engine + replay UI

**Date:** 2026-04-06  
**Goal:** Ship a **minimal, isolated** prototype of the **Altair** combat model ([PRD 82](docs/prd/82-combat-altair.md), ruleset **`altair`**): a deterministic backend that emits an **ordered event log**, and a **frontend replay viewer** that steps through that log. This is **not** wired into galaxy turns, fleets, or the main game loop yet.  
**Relevant PRDs:** [80 — Combat fundamentals](docs/prd/80-combat-fundamentals.md), [82 — Altair combat](docs/prd/82-combat-altair.md), [10 — Fleet movement](docs/prd/10-fleet-movement.md) (`isqrt` only)

---

## Principles

- **Separation** — New code lives in **dedicated trees** under `backend/openstars/combat/` with a **narrow import surface** into the rest of the monolith. The main engine, API game models, and galaxy UI must not sprawl into Altair internals.
- **Determinism** — Same inputs → same log (PRD 80 / PRD 04). Integer arithmetic; seeded RNG only where needed, with **derived** stream keys documented in code.
- **Scope** — Prototype may **omit** most of Stars! combat depth (attractiveness tables, full initiative trees, torpedo accuracy, starbases, 256-token caps, etc.) until a later task. Prefer **stubbed or single-path** behaviour with **explicit TODO** comments and tests that lock what *is* implemented.

**Layout:**

| Area | Location |
|------|----------|
| Backend Altair package | `backend/openstars/combat/altair/` |
| Backend combat tests | `backend/tests/combat/altair/` |
| Backend HTTP (optional thin layer) | `backend/openstars/server/routers/combat_altair_prototype.py` (router mounted with a clear prefix) |
| Frontend prototype | `frontend/src/combat-altair-prototype/` (route + components only used by this feature) |

**Future:** Classic combat engine: `backend/openstars/combat/classic/` (PRD 81) — out of scope for this task.

---

## Step 1 — Package skeleton and boundaries

- [ ] Ensure **`backend/openstars/combat/altair/`** exists with `__init__.py` and a short **`README.md`** stating scope, PRD pointers, and “do not import from main game engine except **`openstars.engine.util.isqrt`** (and stdlib).”
- [ ] **No imports** from `resolve_steps`, galaxy models, or FastAPI inside the core Altair package (keep core pure Python).
- [ ] Export a single high-level entry point for v1, e.g. **`run_battle(snap: BattleSnapshot, cfg: AltairCombatConfig) -> CombatLog`**, where types are defined in the Altair package.
- [ ] **Unit test:** importing the Altair combat package does not pull in FastAPI or server modules.

**Output:** Empty or stub `BattleSnapshot` / `CombatLog` types and the public function signature.

---

## Step 2 — Config, geometry, and distance

Implement PRD 82 constants and distance as used by the prototype.

- [ ] **`AltairCombatConfig`**: `S` (default `1000`), `T` (default `20`), `N_rounds` (default `16`), `arena_size` (= `10 * S` per axis), optional `ruleset_schema_version`.
- [ ] **`distance(a, b) -> int`**: `isqrt((dx*dx + dy*dy))` via **`openstars.engine.util.isqrt`** (same contract as PRD 10).
- [ ] **`in_range(dist, R_classic, S, starbase_bonus)`** per PRD 82.
- [ ] **Unit tests:** `isqrt` parity with existing engine tests; a few hand-checked distance / range cases.

---

## Step 3 — Minimal battle snapshot and token model

- [ ] **Pydantic** (or dataclasses + JSON schema) models **internal to the Altair package**: e.g. `BattleSnapshot` with tokens `{ id, owner, position (x,y), label?, movement_quarters? }` — enough to drive the tick loop. **No** `GlobalState` / fleet IDs from the main game required for v1; use string ids local to the snapshot.
- [ ] **Fixture builders** in tests (e.g. two tokens facing each other) for deterministic runs.
- [ ] **Unit tests:** snapshot serialisation round-trip (JSON) if logs are JSON-based.

---

## Step 4 — Tick loop and movement (v1)

Implement **movement only** first: rounds, `T` ticks per round, `budget_round` from **`quarters_round`** with **`budget_round = (quarters_round * S) // 4`**, split across ticks per PRD 82 (`b`, `r` remainder distribution).

- [ ] **Simplified AI v1:** e.g. each token moves **toward** a fixed target position or **primary enemy token** by spending up to `budget_tick(k)` along a single vector (integer step truncation acceptable if documented), **clamped** to arena bounds.
- [ ] **Order:** deterministic sort by token id (or weight field if added later); skip ±15% jitter in v1 **or** implement with derived RNG — if skipped, document.
- [ ] Emit **log events**: at minimum `tick_start`, `token_moved` (from, to, tick, round_index), `round_end_shooting_skipped` placeholder or omit shooting until Step 5.
- [ ] **Unit tests:** for a fixed snapshot, **`sum_k budget_tick(k) == budget_round`**; total ticks ≤ `N_rounds * T`; log length stable across runs.

---

## Step 5 — Shooting phase stub (v1)

Add a **minimal** end-of-round shooting step so the log structure matches PRD 80’s idea of **movement then fire once per round**.

- [ ] **v1 rule suggestion:** one weapon per token, fixed `R_classic`, fixed damage; if `in_range`, append `weapon_fired` / `damage_applied` / `token_destroyed` events; no shield/armour split required in v1 **or** use a single HP pool per token.
- [ ] **Unit tests:** two-token fixture ends with deterministic outcome and stable log hash or full expected event list.

---

## Step 6 — `CombatLog` schema and versioning

- [ ] Define **`CombatLog`** as a versioned document: `schema_version`, `config` echo, ordered **`events: list[CombatEvent]`** with discriminated `type` and payloads (snake_case for API).
- [ ] Document the schema in the package `README.md` (brief field list).
- [ ] **Unit tests:** reject unknown `schema_version` on parse; golden file for one minimal battle JSON under `tests/combat/altair/fixtures/`.

---

## Step 7 — Optional HTTP endpoint (isolated router)

- [ ] Add **`POST /api/v1/combat-altair-prototype/simulate`** (or similar prefix) accepting `BattleSnapshot` + `AltairCombatConfig`, returning `CombatLog`. Router lives in its own module; register in `main.py` in one line.
- [ ] **No** authentication game coupling required for v1 if other prototypes are open; if the app already requires auth, follow existing dev patterns.
- [ ] **Integration test (optional):** httpx call returns 200 and valid JSON matching schema.

---

## Step 8 — Frontend: isolated prototype route and shell

- [ ] Under **`frontend/src/combat-altair-prototype/`**, add a **parent component** and register a **route** (e.g. React Router path `/combat-altair-prototype` or dev-only menu entry) that does **not** require loading a real game — can paste JSON or load fixture file in dev.
- [ ] **Do not** thread combat state through `App.tsx` beyond a single route / lazy import; avoid coupling to `useGameCommands` or galaxy map.

---

## Step 9 — Frontend: replay viewer (v1)

- [ ] **Controls:** play / pause, step tick, jump to round boundary, optional speed slider.
- [ ] **View:** render token positions on a **scaled** 2D plane (SVG or canvas): map arena `0…10S` into viewport coordinates. Labels for round index and tick within round.
- [ ] **Data:** accept `CombatLog` JSON (from file upload, textarea, or fetch to Step 7 endpoint).
- [ ] **Vitest:** pure reducer or “apply event to frame state” tested without DOM; optionally one component smoke test.

---

## Step 10 — Polish and guardrails

- [ ] **Ruff** / **pytest** clean for backend; **lint** / **typecheck** for frontend.
- [ ] PRD 82 already documents backend paths; keep **`combat/altair/README.md`** in sync with implementation status.
- [ ] Update this task file: mark steps `[x]` as completed when done.

---

## Explicitly out of scope for this task

- **Classic** 10×10 ruleset (PRD 81) implementation in `combat/classic/`.
- Integration with **turn resolution**, **fog of war**, or **player commands**.
- Full weapon / component / initiative fidelity from Stars!.
- Polished production UI art; **functional** replay is enough.

---

## Success criteria

1. From a **test fixture**, backend produces a **stable, ordered `CombatLog`** JSON.  
2. Frontend can **load that log** and **scrub** through ticks with correct positions.  
3. Altair code remains **import-isolated** from the main engine except **`isqrt`**, and the UI lives under its **own directory** and route.
