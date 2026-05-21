# PRD 60 — UI Overview

## Overview

This document defines the overall UI design for OpenStars! — the screens, layout, and rendering approach. Sub-documents cover each major UI area:

- [PRD 61 — Galaxy Map](61-ui-galaxymap.md)
- [PRD 62 — Planet Detail Panel](62-ui-planet-detail.md)
- [PRD 63 — Fleet Detail Panel](63-ui-fleet-detail.md)
- [PRD 64 — Waypoint Orders](64-ui-waypoint-orders.md)
- [PRD 65 — Fleet Merge & Split](65-ui-fleet-merge-split.md)
- [PRD 66 — Research UI](66-ui-research.md)
- [PRD 67 — Planet List](67-ui-planet-list.md)
- [PRD 68 — Production UI](68-ui-production.md)

The goal is a galaxy map that evokes the original Stars! (1995) while bringing the controls and information design into the modern era.

The original Stars! UI was a masterclass in information density for its time — planet details, fleet management, production queues, scanner coverage, and a galaxy map all visible at once. But it was built for 800×600 Windows 95. OpenStars! keeps the **information-first philosophy** and the **visual language of the galaxy map**, while replacing the 1990s widget chrome with a clean, modern dark interface.

Reference: `docs/references/stars-1995-screenshot-51464.jpg`

## Design Principles

1. **The map is the game.** The galaxy map dominates the screen. Everything else serves the map — panels appear contextually and never obscure more than they need to.

2. **Dark by default.** Space is black. The UI should feel like mission control, not a spreadsheet. Dark backgrounds, high-contrast text, coloured accents for game elements.

3. **Information on demand.** Show the overview always (map, turn status). Show details when the player asks for them (click a planet, select a fleet). Don't front-load every number — the original's left panel was overwhelming for new players.

4. **Direct manipulation.** Set waypoints by clicking on the map, not by typing coordinates. Drag to pan, scroll to zoom. Select by clicking. The map is interactive, not just a display.

5. **Keyboard accessible.** Common actions have keyboard shortcuts. Tab through fleets, Enter to submit turn, Escape to deselect.

## Technology

- **Galaxy map:** Canvas 2D (see PRD 06 for rendering choice rationale)
- **UI panels:** React + TypeScript + Tailwind CSS + shadcn/ui components
- **State management:** React context or Zustand — TBD during implementation, keep it simple
- **Layout:** CSS Grid for the overall structure, absolute positioning for map overlays

## Screen Layout

```
┌───────────────────────────────────────────────────────────┐
│  Top Bar                                                  │
│  [Game Name]           [Turn 5]  [Waiting: 1/3]  [Submit] │
├───────────────────────────────────────────────────────────┤
│                                          │                │
│                                          │  Detail Panel  │
│                                          │  (contextual)  │
│           Galaxy Map                     │                │
│           (Canvas)                       │  - Planet info │
│                                          │  - Fleet info  │
│                                          │  - Waypoints   │
│                                          │                │
│                                          │                │
│                                          │                │
├──────────────────────────────────────────┴────────────────┤
│  Event Log / Messages                                     │
└───────────────────────────────────────────────────────────┘
```

### Top Bar

A slim, persistent header. Contains:

- **Game name** — which game you're in
- **Turn indicator** — current turn number
- **Submission status** — who has submitted commands this turn (e.g. "Waiting: 1 of 3 players")
- **Submit Turn button** — primary action, prominent. Disabled if already submitted. Shows confirmation state after submission.

No menu bar. No toolbar of cryptic icons. Actions live in context menus and the detail panel.

### Galaxy Map (Centre)

The primary view — takes up the majority of the screen. The map fills all available space not occupied by the top bar, detail panel, or event log.

The detail panel can be collapsed to give the map full width.

### Detail Panel (Right)

A slide-in panel on the right side of the screen. Shows details for the currently selected object:

- **Nothing selected:** panel is collapsed or shows a minimal game summary
- **Planet selected:** planet details (see PRD 62)
- **Fleet selected:** fleet details and waypoint editing controls (see PRD 63)
- **Multiple objects at same location:** tabbed or stacked view

The panel is resizable and collapsible. Default width: ~300–400px.

### Event Log (Bottom)

A collapsible bottom strip showing turn events — fleet arrivals, scan results, detections. Maps to the `events` section of the player state file (PRD 03).

Can be expanded to scroll through all events. Shows the most recent/important event by default. Clicking an event centres the map on the relevant location.

### Unsaved Changes Indicator

If the player has set waypoints but not submitted, a visual indicator warns them:

- Submit button pulses or shows a badge: "Unsaved changes"
- Navigating away from the game shows a browser confirmation dialog

## Colour System

### Player Colours

Colours are **client-side only** — each player chooses how they see themselves and others. This is a display preference, not game state.

**Defaults:**
- **Current player:** Blue (#3b82f6)
- **All other players:** Red (#ef4444)

In the future, the player will be able to customise their own colour and the colour assigned to each other player — matching the original Stars! approach where two players in the same game could see entirely different colour schemes.

Colour preferences will be stored server-side in `player-preferences-{username}.json` (per game, alongside the other player files in GCS), so they follow the player across devices.

For the initial build, the defaults (blue self, red others) are hardcoded. The colour picker is a future enhancement.

### UI Colours

- **Background:** near-black (#0a0a0a for panels, pure black for map)
- **Text:** white/light grey
- **Borders/dividers:** dark grey (#1f1f1f)
- **Interactive elements:** use the standard shadcn/ui dark theme
- **Accents:** player colours for game elements, blue for generic UI highlights

## Phase 2 Scope

Phase 2 (Basic UI) implements the minimum needed to interact with the Phase 1 engine:

**In scope:**
- Galaxy map rendering (planets, fleets, routes, scanner circles)
- Pan and zoom
- Planet selection and basic detail view
- Fleet selection with waypoint editor
- Waypoint setting by clicking the map
- Turn submission and status display
- Event log (fleet arrived, planet scanned)
- Production queue management — top-level workspace (see [PRD 68 — UI Production](68-ui-production.md))
- Responsive layout (detail panel collapse on narrow screens)

**Out of scope (future phases):**
- Ship designer
- Research allocation
- Race/trait configuration
- Battle replay viewer
- Game lobby / game creation UI (Phase 5 — multiplayer)
- Chat / messaging between players
- Notifications (email/push for "it's your turn")
- Planet habitability visualisation
- Minimap

## Screen Size

The UI targets **desktop browsers at 800px+ width**. This is a desktop game — no responsive layouts, no mobile breakpoints, no drawer/bottom-sheet variants.

If the viewport is too narrow, a simple message ("OpenStars! is designed for desktop browsers") is sufficient. Responsive design can be revisited later if the game proves out.

## Accessibility

- All interactive elements are keyboard-reachable
- Canvas elements have ARIA labels for screen readers (planet/fleet names)
- Colour is not the only differentiator — player icons have distinct shapes as well as colours (future enhancement)
- Focus indicators on all controls
- High-contrast text on dark backgrounds (WCAG AA minimum)

## What's Out of Scope

- **Mobile-optimised UI** — desktop is primary. Mobile is functional but not a design target.
- **Sound effects / music** — maybe someday.
- **Animations** — fleet movement between turns could be animated (smooth interpolation), but this is a polish item, not Phase 2.
- **Theming / light mode** — dark only for now. Space is dark.
- **Tutorial / onboarding** — the game will be confusing to new players. That's a Phase 7 problem.
