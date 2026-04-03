# Orbit selection rework

**Date:** 2026-04-03
**Goal:** Change how fleets in orbit are indicated and selected — single blue orbit indicator on the map, fleet list in the planet detail panel, no direct click-selection of orbit fleets.

**Relevant PRDs:** [61-ui-galaxymap.md](../docs/prd/61-ui-galaxymap.md), [62-ui-planet-detail.md](../docs/prd/62-ui-planet-detail.md), [63-ui-fleet-detail.md](../docs/prd/63-ui-fleet-detail.md)
**Related files:** [frontend/src/components/GalaxyMap.tsx](../frontend/src/components/GalaxyMap.tsx), [frontend/src/components/DetailPanel.tsx](../frontend/src/components/DetailPanel.tsx)

---

## Background

Currently, fleets at a planet are rendered as concentric coloured rings (one per fleet) and are directly click-selectable via those rings. The new design simplifies this:

- A single small blue circle (`#60a5fa`) on the planet dot indicates one or more fleets are in orbit — no per-fleet rings
- The selected planet is shown with a larger yellow-grey circle drawn behind the planet dot
- Orbit fleets cannot be selected by clicking the map — you click the planet, then pick the fleet from the planet detail panel
- The planet detail panel shows a "Fleets in Orbit" list; clicking an entry selects that fleet

---

## Step 1 — Planet selection indicator (`GalaxyMap.tsx`)

In `renderPlanets` ([GalaxyMap.tsx:452-460](../frontend/src/components/GalaxyMap.tsx#L452-L460)), replace the white selection ring with a yellow-grey filled circle drawn *before* the planet dot:

- Draw a filled circle at `(sx, sy)` with radius `PLANET_RADIUS * 2`, fill `#d1d5db`, before `ctx.arc` for the planet dot itself
- Remove the current `ctx.stroke()` white ring that follows

- [ ] Update `renderPlanets` to draw the yellow-grey selection circle behind the planet dot
- [ ] Remove the white selection ring stroke

## Step 2 — Orbit fleet indicator (`GalaxyMap.tsx`)

Replace `renderFleetsAtPlanets` ([GalaxyMap.tsx:464](../frontend/src/components/GalaxyMap.tsx#L464)) with a simpler function that draws one small blue circle per planet that has at least one fleet in orbit:

- For each unique planet position that has one or more fleets, draw a small filled circle: radius ~`PLANET_RADIUS + 3`, fill `#60a5fa`, alpha ~0.85
- Remove all concentric ring logic, `FLEET_RING_OFFSET`, and `FLEET_RING_SPACING` usage from this function
- The indicator is drawn on top of the planet dot

- [ ] Rewrite `renderFleetsAtPlanets` to draw a single blue indicator per occupied planet
- [ ] Remove `FLEET_RING_OFFSET` and `FLEET_RING_SPACING` constants if no longer used elsewhere

## Step 3 — Remove orbit fleet hit detection (`GalaxyMap.tsx`)

In the click handler ([GalaxyMap.tsx:905-942](../frontend/src/components/GalaxyMap.tsx#L905-L942)), remove the ring-based hit detection branch for orbit fleets. The `if (planet)` branch that pushes orbit fleets as candidates should be deleted. Only deep-space fleet hits remain.

- [ ] Remove the orbit fleet ring hit detection branch
- [ ] Verify deep-space fleet selection still works

## Step 4 — "Fleets in Orbit" in `PlanetDetail` (`DetailPanel.tsx`)

Add a `fleetsInOrbit` prop and `onSelectFleet` callback to `PlanetDetail` ([DetailPanel.tsx:316](../frontend/src/components/DetailPanel.tsx#L316)):

```ts
fleetsInOrbit: PlayerFleet[];
onSelectFleet: (fleetId: string) => void;
```

Render a "Fleets in Orbit" section above the mineral display, omitted when `fleetsInOrbit` is empty:

```
Fleets in Orbit
  Scout × 1   You          [clickable row]
  Freighter × 2  Player 2  [clickable row]
```

Each row shows fleet name, owner ("You" if own fleet), and total ship count. Clicking selects the fleet via `onSelectFleet`.

- [ ] Add `fleetsInOrbit` and `onSelectFleet` props to `PlanetDetail`
- [ ] Render the "Fleets in Orbit" section when non-empty
- [ ] Wire row clicks to `onSelectFleet`

## Step 5 — Thread props through `DetailPanel` and caller

Add to `DetailPanelProps` ([DetailPanel.tsx:810](../frontend/src/components/DetailPanel.tsx#L810)):

```ts
fleetsAtSelectedPlanet: PlayerFleet[];
onSelectFleet: (fleetId: string) => void;
```

Pass them through to `PlanetDetail` at [DetailPanel.tsx:871](../frontend/src/components/DetailPanel.tsx#L871).

In the caller (find with `grep -r "DetailPanel" frontend/src`): compute `fleetsAtSelectedPlanet` as the subset of `playerState.fleets` whose position matches `selectedPlanet.position`, and pass `onSelectFleet` that calls `onSelect({ kind: "fleet", id })`.

- [ ] Extend `DetailPanelProps` with the two new props
- [ ] Pass props through to `PlanetDetail`
- [ ] Compute and pass `fleetsAtSelectedPlanet` from the caller
- [ ] Implement `onSelectFleet` in the caller

## Step 6 — Tests and lint

- [ ] Update any existing `DetailPanel` tests that render `PlanetDetail` to supply the new props
- [ ] Add test: "Fleets in Orbit" section visible when `fleetsInOrbit` is non-empty
- [ ] Add test: clicking a fleet row calls `onSelectFleet` with the correct fleet ID
- [ ] Add test: section absent when `fleetsInOrbit` is empty
- [ ] `cd frontend && npm run typecheck` — clean
- [ ] `cd frontend && npm run lint` — clean
- [ ] `cd frontend && npm test` — all passing
