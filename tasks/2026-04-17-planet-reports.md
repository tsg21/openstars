# Planet Reports — Last-Known Data for Previously Scanned Planets

**PRD:** [11-scanners.md](../docs/prd/11-scanners.md) — Historical Knowledge section

When a player has previously scanned a planet but it is no longer in scanner range, the player state should include the last-known data from that planet (marked `scan_level: "stale"` with a `last_scanned_turn` field) rather than dropping the planet to `scan_level: "none"`.

Stale data is sourced from the previous player state file (`player-state-{username}-T{N-1}.json`) — no separate history store is needed. Stale entries chain automatically across turns: a planet that was stale last turn stays stale this turn with the same `last_scanned_turn`.

---

## Step 1 — Backend: extend `PlayerPlanet` model and `derive_player_state`

- [ ] Add `last_scanned_turn: int | None = None` to `PlayerPlanet` in `backend/openstars/engine/models.py`
- [ ] Update the `scan_level` comment on `PlayerPlanet` to include `"stale"`
- [ ] Update `derive_player_state` signature in `backend/openstars/engine/fog.py` to accept `previous_player_state: PlayerState | None = None`
- [ ] In `derive_player_state`, build a lookup `prev_planets: dict[str, PlayerPlanet]` from `previous_player_state.planets` (keyed by planet ID) when the previous state is provided
- [ ] In the `else` (scan_level `"none"`) branch of planet derivation, check `prev_planets`:
  - If the previous entry exists and its `scan_level` is `"basic"`, `"detailed"`, or `"stale"` → copy the previous `PlayerPlanet` with `scan_level="stale"` (preserve all other fields and `last_scanned_turn` as-is; for entries that were `"basic"` or `"detailed"` set `last_scanned_turn` to the previous state's turn)
  - Otherwise → leave as `scan_level="none"` (no change)
- [ ] Unit tests in the existing fog-of-war test file (or alongside it):
  - Planet scanned last turn appears as `"stale"` with correct `last_scanned_turn` when out of range this turn
  - Planet that was already `"stale"` last turn stays `"stale"` with the original `last_scanned_turn` (not updated)
  - Planet that re-enters scanner range returns to `"basic"` or `"detailed"` (stale is cleared)
  - Turn 0 (no previous state) → out-of-range planets remain `"none"`
  - Basic-scan stale carries only basic fields; detailed-scan stale carries full detail fields

## Step 2 — Backend: pass previous player state at resolve time

- [ ] In `backend/openstars/server/routes/play.py`, in the resolve endpoint, load the current player state (`turn N`) before calling `derive_player_state` for turn `N+1` — pass it as `previous_player_state`
- [ ] Handle the `FileNotFoundError` case gracefully: if no previous player state exists (turn 0 edge case), pass `None`
- [ ] Game creation (`backend/openstars/server/routes/games.py`) passes `None` as `previous_player_state` — no change needed, but verify the call still works

## Step 3 — Integration test: stale planet data survives a turn cycle

Add to `backend/tests/server/test_api.py` in a `TestScanners` class (or alongside the existing scanner tests).

The test needs to:
1. Create a game and find a planet that Tim's fleet can scan (scan_level `"basic"`) but that is close to the edge of scanner range
2. Move Tim's fleet away from that planet so it falls out of range, resolve the turn
3. Assert the planet is now `scan_level: "stale"` in Tim's state with `last_scanned_turn` set to the turn it was last in range
4. Resolve another turn without moving back toward the planet
5. Assert the planet is still `scan_level: "stale"` with the same `last_scanned_turn` (stale chains)

A reliable way to set this up without depending on galaxy generation: start Tim's fleet at the home planet (turn 0 state), find any planet with `scan_level: "basic"`, then set a waypoint moving Tim's fleet far away in the opposite direction. After enough turns the scanned planet should drop out of the 150pc scanner range and become stale.

- [ ] Write `test_stale_planet_after_fleet_moves_away` in `TestScanners`:
  - Create game, get Tim's T0 state
  - Identify a planet with `scan_level: "basic"` (skip the test if none exist at T0, though in a small galaxy there should be some)
  - Record that planet's `id` and the current turn number as the expected `last_scanned_turn`
  - Move Tim's fleet directly away from that planet by more than 150 parsecs (e.g. 200pc), resolve, submit empty commands for both players for enough turns until the planet leaves range
  - Assert the planet has `scan_level: "stale"` and `last_scanned_turn` matches the last turn it was in range
  - Resolve one more turn without moving back; assert the planet is still `"stale"` with the same `last_scanned_turn`

## Step 5 — Frontend: extend types and planet detail panel

- [ ] Add `"stale"` to the `ScanLevel` union in `frontend/src/types/game.ts`
- [ ] Add `lastScannedTurn?: number` to the `PlayerPlanet` type
- [ ] In `frontend/src/components/PlanetDetail.tsx`, add a `scan_level: "stale"` rendering block:
  - Show a staleness banner above the planet data: "Last scanned: Turn N" (using `lastScannedTurn`)
  - Render whatever fields are present (owner, population, minerals, habitability) — same components as `"detailed"`, but wrapped in a muted/50% opacity container
  - Omit the `mining_rate` segment from the mineral bar chart when `scanLevel === "stale"`
  - Omit the production queue section
- [ ] Update `frontend/src/components/GalaxyMap.tsx` / `galaxyMapRender.ts` to render stale planets:
  - Same colour as last-known owner (or grey if uncolonised), at 50% opacity
- [ ] Unit tests covering:
  - `PlanetDetail` renders the staleness banner and muted data for a stale planet
  - `PlanetDetail` omits the banner for non-stale scan levels
  - Galaxy map renders stale planet dot at reduced opacity
