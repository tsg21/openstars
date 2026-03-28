# Remove Zoom — Fixed Scale with Pan

**Date:** 2026-03-28
**Goal:** Replace the zoom + detail-level system with a fixed "close" scale. All map elements (planet labels, fleet icons, routes, waypoint markers) are always visible. Panning remains. Zoom will be re-added later once the basics are solid.

**Why:** At the default fit-to-galaxy scale the detail level evaluates to "far", hiding fleet routes, fleet icons, and labels. Rather than tweaking thresholds, simplify: one good scale, always show everything.

---

## Changes

### 1. `useViewport` — remove zoom, keep pan

- Remove `onWheel` handler
- Remove `+`/`-`/`=`/`_` keyboard zoom bindings
- Remove `ZOOM_FACTOR`, `MIN_SCALE_FACTOR`, `MAX_SCALE_FACTOR`, `clampScale`
- Scale is fixed: pick a scale so ~200 parsecs span 1000px (i.e. `1000 / (200 * PARSEC)`) — this gives comfortable spacing for labels and icons
- Initial centre: player's first owned planet (Sol in mock data), not the galaxy centroid
- Keep click-drag pan and arrow-key pan
- Keep Home key → reset to initial centre (same fixed scale)
- `fitToGalaxy` becomes `resetView` (recentres, no scale change)
- Remove `isPanning` cursor logic if it simplifies things, or keep for UX — dealer's choice

### 2. `GalaxyMap` — remove detail levels

- Delete `getDetailLevel`, `DetailLevel` type
- Remove all `detail`-gated branches (`if (detail !== "far")`, `if (detail === "close")`, etc.)
- Always render: planet dots + labels, fleet icons + ID labels, fleet routes + waypoint markers
- Remove the fit-to-galaxy button (bottom-right Home icon) — not needed without zoom

### 3. Tests

- Update `useViewport.test.ts` — remove any zoom-related assertions
- Update `GalaxyMap.test.tsx` — remove detail-level tests if any

### 4. Task file update

- Add a note to Step 5 in `2026-03-22-ui-prototype.md` that zoom was removed and will return later

---

## Not in scope

- Re-adding zoom later (separate task)
- Changing planet/fleet rendering style
- Minimap or other navigation aids
