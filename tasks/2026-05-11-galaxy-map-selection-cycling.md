# Galaxy map selection cycling

**Date:** 2026-05-11

**Goal:** Let repeated map clicks cycle through stacked selectable objects, including planets with fleets in orbit and overlapping fleets.

## Step 1 — Specify map selection cycling

- [x] Update PRD 61 so orbiting fleets are reachable through repeated clicks on the planet location.
- [x] Clarify that overlapping fleets cycle when repeated clicks hit the same stack.

Relevant checks:

- Documentation-only step; no automated checks required.

## Step 2 — Implement deterministic hit stack cycling

- [x] Include orbiting fleets in the galaxy map click candidate stack after the planet they orbit.
- [x] Keep first click on a planet-with-fleets selecting the planet.
- [x] Cycle from the current selection to the next hit candidate, wrapping back to the first candidate.
- [x] Preserve waypoint editing click behaviour.

Relevant checks:

- `cd frontend && npm test -- GalaxyMap`
- `cd frontend && npm run typecheck`
