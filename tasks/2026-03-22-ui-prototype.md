# UI Prototype — Phase 2

**Date:** 2026-03-22
**Goal:** Build a working UI prototype that lets a player view a galaxy, select planets and fleets, set waypoints, and submit a turn — all against mock data. No backend required.

**Relevant PRDs:** 01 (overview), 02 (galaxy map), 03 (turn lifecycle), 05 (global state), 06 (technical platform), 07 (turn mechanics), 08 (UI)

---

## Step 1 — Scaffold the Frontend Project

Set up the `frontend/` directory with Vite + React + TypeScript + Tailwind CSS + shadcn/ui. Configure linting (ESLint) and testing (Vitest). Verify `npm run dev` serves a blank page.

- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] Install and configure Tailwind CSS (v4)
- [ ] Install and configure shadcn/ui (dark theme only)
- [ ] Configure ESLint (strict TypeScript rules)
- [ ] Configure Vitest
- [ ] Verify dev server runs at `localhost:5173`

**Output:** Empty app shell, all tooling green.

---

## Step 2 — TypeScript Types + Mock Data

Define the TypeScript types that mirror the YAML schemas from PRDs 02, 03, 05, and 07. Create a mock dataset — a small galaxy with 2 players, ~20 planets, 2 fleets with waypoints, and some turn events. This is the data the UI will render for the entire prototype phase.

- [ ] Define types: `Galaxy`, `Planet`, `Fleet`, `Design`, `PlayerState`, `PlayerCommand`, `GameEvent`
- [ ] Create mock `galaxy.yaml` equivalent as a TS fixture (~20 planets, small galaxy)
- [ ] Create mock player state for turn 3 (own planets, own fleet with waypoints, some visible enemy fleet/planets)
- [ ] Create mock turn events (fleet_arrived, planet_scanned)
- [ ] Export a `useMockGameState()` hook that provides all data to the UI

**Output:** Rich test data the whole UI can consume. Types we'll reuse when the real backend exists.

---

## Step 3 — Layout Shell

Build the top-level CSS Grid layout from PRD 08: top bar, galaxy map area, collapsible detail panel (right), collapsible event log (bottom). All panels are empty placeholders with visible boundaries.

- [ ] CSS Grid layout matching PRD 08 diagram
- [ ] Top bar: game name, turn number, submission status, Submit Turn button (all static/placeholder)
- [ ] Detail panel (right): collapsible, 350px default width
- [ ] Event log (bottom): collapsible strip
- [ ] Dark theme: near-black panels (#0a0a0a), pure black map area
- [ ] Desktop-only gate: show message below 1280px

**Output:** The four-zone layout, resizable and collapsible, looks like a game screen even with placeholder text.

---

## Step 4 — Galaxy Map Canvas (Static Render)

Render the galaxy onto a Canvas 2D element. Transform galaxy coordinates to screen coordinates. Draw planets as coloured dots with name labels. No interactivity yet — just a static render of the mock galaxy data.

- [ ] `<canvas>` element fills the map zone
- [ ] Coordinate transform: galaxy coords → screen pixels (with initial viewport showing the full placement region)
- [ ] Render planets: coloured circles (blue=own, grey=uncolonised, red=enemy-owned)
- [ ] Render planet names as labels (below each dot)
- [ ] Render fleets: small chevron/triangle icons at their position
- [ ] Render fleet routes: lines from fleet to each waypoint in sequence
- [ ] Handle DPI scaling (`devicePixelRatio`) for sharp rendering on Retina displays

**Output:** A static galaxy map showing planets, fleets, and routes against a black background.

---

## Step 5 — Pan and Zoom

Make the map interactive. Scroll-wheel zoom (centred on cursor), click-drag to pan, keyboard arrows to pan, +/- to zoom. Maintain the coordinate transform so all rendering stays correct as the viewport changes.

- [ ] Viewport state: centre position (in galaxy coords) + zoom level
- [ ] Scroll wheel → zoom in/out, centred on cursor position
- [ ] Click and drag on empty space → pan
- [ ] Keyboard: arrow keys to pan, +/- to zoom
- [ ] "Fit to galaxy" button/shortcut (Home key?) to reset viewport
- [ ] Adaptive detail levels: far zoom shows dots only, medium adds labels, close adds fleet names and waypoint markers
- [ ] Smooth/responsive — requestAnimationFrame render loop, not re-render on every event

**Output:** A pannable, zoomable galaxy map. Feels like navigating a real map.

---

## Step 6 — Selection + Detail Panel (Planets)

Click a planet to select it. Show a highlight ring on the selected planet. Populate the detail panel with planet information from the mock player state.

- [ ] Hit detection: click on canvas → find nearest planet within click radius
- [ ] Selected planet gets a highlight ring/glow
- [ ] Click empty space → deselect
- [ ] Detail panel: planet name, owner, population (or "Uncolonised")
- [ ] Detail panel shows appropriate info based on visibility (own planet = full detail, enemy = limited, uncolonised = minimal)

**Output:** Clicking planets shows their info. The detail panel is alive.

---

## Step 7 — Selection + Detail Panel (Fleets)

Same as Step 6 but for fleets. Click a fleet to select it. Show fleet info and the waypoint editor in the detail panel.

- [ ] Hit detection for fleet icons
- [ ] Selected fleet gets highlight
- [ ] Detail panel: fleet ID, composition (design × count), speed, current position
- [ ] Waypoint list in detail panel: ordered destinations with estimated turns to arrival
- [ ] When a fleet is selected, its route is visually emphasised on the map
- [ ] Handle overlapping objects (planet + fleet at same location): click cycles through or shows picker

**Output:** Fleet selection works. Waypoint list is displayed (read-only for now).

---

## Step 8 — Waypoint Editing

When a fleet is selected, clicking the map adds waypoints. This is the core gameplay interaction.

- [ ] With fleet selected: click a planet → append as waypoint (snap to planet position)
- [ ] With fleet selected: click empty space → append deep-space waypoint
- [ ] Waypoint markers rendered on map (numbered circles along the route)
- [ ] Right-click a waypoint marker → remove it
- [ ] "Clear All" button in the detail panel
- [ ] Waypoint changes tracked as local unsaved state (not yet "submitted")
- [ ] Estimated turns recalculated as waypoints change (client-side: distance / speed)
- [ ] Route lines update in real-time as waypoints are added/removed

**Output:** The player can plan fleet movements visually. This is the moment it feels like a game.

---

## Step 9 — Turn Submission Flow

Wire up the Submit Turn button. Track unsaved changes. Show submission state.

- [ ] Track dirty state: any waypoint changes that haven't been "submitted"
- [ ] Submit button shows "Unsaved changes" badge when dirty
- [ ] Clicking Submit: serialise current waypoint commands into the command format (PRD 07), log to console (no backend yet)
- [ ] After submit: button changes to "Submitted ✓", commands are "locked" (editable again on resubmit)
- [ ] Top bar shows turn number and placeholder player status ("Waiting: 1 of 2 players")
- [ ] Browser beforeunload warning when unsaved changes exist

**Output:** The full turn flow works end-to-end against mock data. Submit → see the command object → UI reflects submitted state.

---

## Step 10 — Event Log

Populate the bottom event log strip with mock turn events. Clicking an event centres the map on the relevant location.

- [ ] Render events from mock data (fleet_arrived, planet_scanned, fleet_detected)
- [ ] Each event is a single line: icon + description + turn number
- [ ] Click an event → pan/zoom the map to the relevant planet/fleet
- [ ] Scrollable when expanded, shows latest event when collapsed

**Output:** Events are visible and interactive. The last piece of the Phase 2 UI puzzle.

---

## Stretch Goals (if time permits)

These aren't blockers — nice-to-haves that improve the prototype feel:

- [ ] Scanner range circles (semi-transparent, toggleable)
- [ ] Double-click planet/fleet → zoom to and centre
- [ ] Keyboard shortcuts: Tab to cycle fleets, Escape to deselect, Enter to submit
- [ ] Minimap (small overview in corner)
- [ ] Animate fleet position interpolation between "turns" (using a second mock state)

---

## Notes

- **No backend.** The entire prototype runs against in-memory mock data. When the Python backend exists (Phase 1 engine + FastAPI server), we swap `useMockGameState()` for real API calls. The UI code shouldn't need to change.
- **No auth.** Single-player view of mock data. The current "player" is hardcoded.
- **No Docker yet.** Just `npm run dev` during prototyping. Dockerfile comes when we integrate with the backend.
- **Canvas vs DOM:** The galaxy map is Canvas 2D. The UI panels (detail, events, top bar) are React components. They communicate through React state, not canvas events.
