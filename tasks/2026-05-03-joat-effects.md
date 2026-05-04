# JOAT Effects Implementation

**Date:** 2026-05-03
**Goal:** Implement the three JOAT PRT effects now documented in PRD 22: starting tech levels, complete starting fleet, and built-in scanner on Scout/Frigate/Destroyer hulls.
**Relevant PRDs:** [22 — Race Design](docs/prd/22-race-design.md) §"PRT-Driven Engine Coefficients", §"Turn-0 resolution step 8"

---

## Background

Phase A (task `2026-04-26-race-design-phase-a.md`) is complete. The following JOAT-specific effects were researched and added to the PRD but are not yet implemented:

1. **Tech level 3 for all fields** — JOAT races start with all six research fields at level 3, unconditionally. The `start_at_tech_3` accelerator (if enabled) then raises expensive fields to level 4 on top of this.
2. **Complete starting fleet** — the current `_build_starting_fleets` builds 4 ships (2 scouts, 1 small freighter, 1 colony ship). The correct JOAT fleet is 6 ships: 2 scouts, 1 colony ship, 1 medium freighter (Privateer if construction level ≥ 4), 1 mini miner, 1 destroyer.
3. **Built-in scanner** — Scout, Frigate, and Destroyer hull designs owned by a JOAT player get scanner ranges: penetrating = `10 × electronics_level` ly, normal = `20 × electronics_level` ly, applied as a floor over any component-derived scanner. Active even with the NAS LRT (future consideration; NAS will not forbid the built-in).

---

## Step 1 — Starting tech levels

Edit `backend/openstars/engine/resolve_steps/turn_zero.py`.

In `resolve_turn_zero`, after `apply_select_race_command` sets `ctx.race_by_username[username]`, apply starting tech levels to `ctx.research_state_by_username[username].levels` in two passes:

**Pass 1 — JOAT base:**
- If `race.prt == PRT.JACK_OF_ALL_TRADES`, set every field in `levels` to `max(current, 3)`.

**Pass 2 — `start_at_tech_3` accelerator:**
- If `race.research.start_at_tech_3 == True`:
  - Compute `target = 4 if race.prt == PRT.JACK_OF_ALL_TRADES else 3`.
  - For each field whose `race.research.field_profile[field] == ResearchCostProfile.expensive`, set `levels[field] = max(current, target)`.

The per-player research state is read back into the `GlobalState` by `build_result` via `ctx.research_state_by_username`, so no other wiring is needed.

- [x] Implement the two-pass tech level initialisation in `resolve_turn_zero`.
- [x] Unit tests in `backend/tests/engine/race/test_turn_zero_resolution.py`:
  - After resolving turn 0 with the Humanoid preset (JOAT, no `start_at_tech_3`), every field in `Player.research_state.levels` equals 3.
  - After resolving with a custom JOAT race where `start_at_tech_3=True` and `energy` is `expensive`, `energy` level is 4 and all other fields are 3.
  - After resolving with a custom JOAT race where `start_at_tech_3=True` and `energy` is `standard`, `energy` level stays 3.
  - A non-JOAT race (once non-JOAT PRTs are unblocked) with all `standard` profiles and no `start_at_tech_3` starts at level 0. *(Gate this test behind a `pytest.mark.skip` with note "remove when non-JOAT PRTs are unblocked" so the file is ready but the test doesn't fail Phase A.)*

---

## Step 2 — Complete starting fleet

The JOAT fleet is: 2 scouts, 1 colony ship, 1 medium freighter (Privateer if construction ≥ 4), 1 mini miner, 1 destroyer. Currently the code builds 3 designs (Scout, Small Freighter, Colony Ship) and 4 fleets. This step corrects both.

Edit `_build_starting_designs` and `_build_starting_fleets` in `backend/openstars/engine/resolve_steps/turn_zero.py`.

**Designs to add / change:**

| Old | New |
|-----|-----|
| `small_freighter` hull | `medium_freighter` hull (or `privateer` if `construction_level ≥ 4`) |
| *(new)* | `destroyer` hull — engine slot only (`quick_jump_5`) |
| *(new)* | `mini_miner` hull — engine slot only (`quick_jump_5`) |

Components for the new designs follow the same minimal-loadout pattern as the existing ones: only the required engine slot is filled (`quick_jump_5`, slot 1). Optional slots are left empty.

`_build_starting_designs` must look up the player's current `electronics` level from `ctx.research_state_by_username[username].levels` when selecting the freighter hull:

```
construction_level = ctx.research_state_by_username[username].levels["construction"]
freighter_hull = "privateer" if construction_level >= 4 else "medium_freighter"
```

Note: after Step 1 runs first, JOAT base construction level is 3, so the default freighter is `medium_freighter`. A JOAT race with `start_at_tech_3=True` and `construction` marked `expensive` would start at construction 4 and get a Privateer — this is correct behaviour.

**`_build_starting_fleets` signature change:**

```python
def _build_starting_fleets(
    ctx, username, home_x, home_y,
    scout_design, freighter_design, colony_ship_design,
    mini_miner_design, destroyer_design,  # new
) -> None
```

Add two fleet entries (mini miner and destroyer) following the same pattern as existing entries, numbering fleets sequentially.

- [x] Change the freighter design from `small_freighter` to `medium_freighter`/`privateer`.
- [x] Add destroyer and mini miner designs.
- [x] Wire all five designs into `_build_starting_fleets`.
- [x] Unit tests in `backend/tests/engine/race/test_turn_zero_resolution.py`:
  - After turn-0 resolution, the design registry for each player contains exactly 5 designs: Scout, Medium Freighter, Colony Ship, Destroyer, Mini Miner (hulls match).
  - After turn-0 resolution, `GlobalState.fleets` for each player contains exactly 6 fleets at the homeworld position.
  - A JOAT race with `start_at_tech_3=True` and `construction=expensive` starts with a Privateer instead of a Medium Freighter.
  - The existing integration test in `backend/int_tests/test_race_selection.py` Scenario A still passes (update the fleet/design count assertions from 4/3 to 6/5).

---

## Step 3 — Built-in scanner

The JOAT built-in scanner applies a floor on the scanner ranges for Scout, Frigate, and Destroyer designs owned by a JOAT player. It is computed at fog-of-war derivation time (not baked into the design record) because it scales with the current electronics level.

Edit `backend/openstars/engine/fog.py`.

In `_scanner_positions`, after building the `design_scanners` dict (which records component-derived scanner ranges per design id), augment entries for JOAT:

```python
# Find the viewer's player record once
viewer_player = next((p for p in global_state.players if p.username == username), None)
if viewer_player and viewer_player.race and viewer_player.race.prt == "JOAT":
    electronics_level = viewer_player.research_state.levels.get("electronics", 0)
    joat_pen_ly = 10 * electronics_level
    joat_normal_ly = 20 * electronics_level
    JOAT_BUILTIN_HULLS = {"scout", "frigate", "destroyer"}
    for d in designs:
        if d.owner == username and d.hull in JOAT_BUILTIN_HULLS:
            existing_n, existing_p = design_scanners.get(d.id, (0, 0))
            design_scanners[d.id] = (
                max(existing_n, joat_normal_ly * LIGHT_YEAR),
                max(existing_p, joat_pen_ly * LIGHT_YEAR),
            )
```

This is applied before the fleet-iteration loop that reads `design_scanners`, so all fleets using those designs immediately see the updated ranges.

Edge case: `electronics_level == 0` produces `joat_pen_ly = 0`, `joat_normal_ly = 0` — no change for a JOAT player at electronics 0 (the design's component scanner, if any, still applies). This is correct: a freshly-started JOAT race at electronics level 3 gets `pen = 30 ly`, `normal = 60 ly`.

`_scanner_positions` already receives `global_state` and `designs`, so no signature change is needed.

- [x] Implement the JOAT built-in scanner augmentation in `_scanner_positions`.
- [x] Unit tests in `backend/tests/engine/test_fog.py` (or a new `test_fog_joat.py`):
  - A JOAT player with electronics level 3 and a Scout fleet: `_scanner_positions` returns a scanner entry with `pen = 30 * LIGHT_YEAR` and `normal = 60 * LIGHT_YEAR`.
  - A JOAT player with electronics level 0: the Scout entry is not present (no range).
  - A JOAT player's Frigate and Destroyer designs also receive the built-in scanner range.
  - A non-JOAT player's Scout is unaffected (zero range unless a scanner component is fitted).
  - A JOAT player's Cruiser hull (not in the built-in set) is unaffected.
  - The built-in scanner floor does not override a *higher* component scanner (i.e. it only applies when the built-in range exceeds the component range).

---

## Step 4 — Lint, format, test

- [x] `cd backend && uv run ruff check .` clean.
- [x] `cd backend && uv run ruff format --check .` clean.
- [x] `cd backend && uv run pytest` passes.
