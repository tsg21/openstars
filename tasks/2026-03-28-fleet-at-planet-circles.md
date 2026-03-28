# Fleet at Planet — Circle Rendering

**Date:** 2026-03-28
**Goal:** Change fleet rendering so that fleets at planets are shown as circles around the planet, not as arrow icons offset from the planet.

**Relevant PRDs:** 08 (UI)
**Related files:** [frontend/src/components/GalaxyMap.tsx](../frontend/src/components/GalaxyMap.tsx)

---

## Background

Currently, all fleets are rendered as small triangular chevron icons positioned offset from their location (see [GalaxyMap.tsx:256-293](../frontend/src/components/GalaxyMap.tsx#L256-L293)). When a fleet is at a planet, this creates visual clutter with the chevron floating near the planet dot.

The new behavior (as documented in PRD 08):
- **Fleet at a planet** → render as a coloured circle/ring around the planet
- **Fleet in deep space** → render as a dart (concave kite) pointing in direction of travel

This makes the map cleaner and more readable, especially when multiple fleets are stationed at the same planet.

---

## Implementation Steps

### Step 1 — Update Fleet Rendering Logic ✅

Modify the fleet rendering section in [GalaxyMap.tsx:256-293](../frontend/src/components/GalaxyMap.tsx#L256-L293):

- [x] Add a helper function `isFleetAtPlanet(fleet, galaxy, playerState)` that checks if a fleet's position matches a planet's position
- [x] Split the fleet rendering loop into two paths:
  - **Path 1 (at planet):** Draw a ring around the matching planet
    - Radius: `PLANET_RADIUS + FLEET_RING_OFFSET` (e.g., 10-12px)
    - Stroke style: fleet owner colour (self or enemy)
    - Line width: 1.5px (or 2px if selected)
    - If selected: add white highlight or thicker stroke
  - **Path 2 (deep space):** Draw dart shape (concave kite) pointing toward first waypoint

### Step 2 — Update Hit Detection ✅

Modify the click handler in [GalaxyMap.tsx:473-491](../frontend/src/components/GalaxyMap.tsx#L473-L491):

- [x] Update fleet hit detection to account for the new rendering:
  - If fleet is at a planet: check distance from planet centre (using ring radius)
  - If fleet is in deep space: check distance from dart center (centered on fleet position)

### Step 3 — Handle Multiple Fleets at Same Planet ✅

When multiple fleets are at the same planet, we need to show all of them:

- [x] Draw concentric rings with increasing radii (e.g., +6px per fleet)
- [x] Order consistently (e.g., sort by fleet ID alphabetically)
- [x] Cap at a reasonable maximum (e.g., 3-4 rings) — if more fleets, could show a count badge instead (future enhancement)

### Step 4 — Visual Polish ✅

- [x] Ensure fleet labels (ID text) are positioned appropriately:
  - For fleets at planets: position label outside the outermost ring
  - For deep space fleets: keep existing label position
- [x] Test with selected/unselected states
- [x] Test with own fleets vs enemy fleets (different colours)

### Step 5 — Testing ✅

- [x] Manual testing: verify fleets at planets show as rings, fleets in space show as darts pointing toward destination
- [x] Test selection cycling when both planet and fleet(s) are at the same location
- [x] Test waypoint setting from a fleet at a planet
- [x] Verify no visual glitches at different zoom levels (though zoom is currently disabled)

### Step 6 — Linting ✅

- [x] Run `npm run lint` in frontend directory
- [x] Fix any lint errors

---

## Design Decisions

1. **Ring radius increments:** Start with +7px from planet radius for first fleet, +6px for each additional fleet
2. **Maximum rings:** Cap at 4 fleets visible as rings, beyond that show "×N" badge (defer this to future task if needed)
3. **Selection indicator:** For selected fleet at planet, use brighter colour + thicker stroke (2.5px)
4. **Hit detection priority:** When clicking on overlapping planet + fleet(s), cycle through all objects (existing behavior)

---

## Notes

- This is a visual-only change — no changes to data model or game logic
- Dart shape uses canvas rotation to point toward the fleet's first waypoint
- Consider extracting fleet rendering into a separate function for better organization

---

## Completion Notes (2026-03-28)

**Status:** ✅ Complete

### Implementation Summary

All steps completed successfully:

1. **Helper functions added:**
   - `isFleetAtPlanet()` - Detects if fleet position matches any planet
   - `groupFleetsByPosition()` - Groups fleets by position for concentric ring rendering

2. **Fleet rendering updated:**
   - Fleets at planets: Coloured rings with radii = PLANET_RADIUS + FLEET_RING_OFFSET + (index × FLEET_RING_SPACING)
   - Multiple fleets: Concentric rings, sorted by fleet ID for consistency
   - Selection: Thicker stroke (2.5px vs 1.5px) + white outline
   - Labels: Positioned around rings at varying angles
   - Deep space fleets: Dart shape (concave kite) centered on fleet position, rotated to point toward first waypoint

3. **Hit detection updated:**
   - Ring-based hit detection for fleets at planets (checks if click is within ring annulus)
   - Center-based hit detection for deep space fleets (centered on fleet position)
   - Maintains cycle-through behavior for overlapping objects

4. **Testing:**
   - Added fleet FLm5t9r3 in deep space to mock data for testing both rendering paths
   - All linting checks pass

### Files Modified

- [GalaxyMap.tsx](../frontend/src/components/GalaxyMap.tsx) - Rendering and hit detection logic
- [playerState.ts](../frontend/src/mocks/playerState.ts) - Added deep-space fleet for testing
- [08-ui.md](../docs/prd/08-ui.md) - Updated PRD with fleet rendering specification
