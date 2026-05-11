# PRD 61 — Galaxy Map

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Visual Language

The map follows the original Stars! visual language:

- **Black background** — space is black
- **Planets** — small coloured circles
  - Player-owned: bright, saturated colour (assigned per player)
  - Uncolonised (visible): grey/dim
  - Stale (`scan_level: "stale"`): last-known owner colour at ~50% opacity, or dim grey if last known as uncolonised — visually distinct from a currently-visible planet
  - Never scanned (`scan_level: "none"`): dim grey dot, indistinguishable from uncolonised until scanned
  - Selected: a larger yellow-grey circle drawn behind the planet dot (`#d1d5db`, radius ~2× the planet dot radius)
- **Planet names** — small labels below or beside each planet, toggleable for declutter
- **Fleets** — rendering depends on whether the fleet is at a planet or in deep space:
  - **At a planet (in orbit):** a small blue circle is drawn on the planet to indicate at least one fleet is present
    - Colour: `#60a5fa` (blue), regardless of fleet owner(s)
    - One indicator per planet — it does not scale with fleet count
    - When clicking the planet location, repeated clicks cycle through the planet and fleets in orbit
  - **In deep space:** dart shape (concave kite) pointing in direction of travel
    - Centered on fleet position
    - Rotates to point toward first waypoint
    - Player's own: bright player colour
    - Other players' (visible via scanners): their player colour, slightly dimmed
    - Selected: highlighted with white outline
- **Fleet routes** — lines from fleet to waypoints
  - Player's own: solid lines in player colour
  - Active/selected fleet: brighter, with waypoint markers
- **Scanner circles** — two concentric circles per scanner source (PRD 11), matching the original Stars! visual style:
  - **Normal scanner range:** red circle (`rgba(255, 0, 0, 0.15)` fill, `rgba(255, 0, 0, 0.4)` border)
  - **Penetrating scanner range:** light green circle (`rgba(0, 255, 0, 0.1)` fill, `rgba(0, 255, 0, 0.3)` border) — always smaller, drawn inside the red circle
  - Both fleet scanners and planet scanners contribute (planet scanners future phase)
  - Scanner circles are drawn per-fleet, centred on the fleet's position
  - The effective scanner range for a fleet is the maximum scanner range of any ship design in its composition (same rule for both normal and penetrating)
  - Toggleable via a keyboard shortcut or UI toggle — can be visually noisy, so the player should be able to show/hide them
  - When a fleet is selected, its scanner circles are drawn brighter/more opaque for emphasis
- **Selection indicator** — a ring or bracket around the selected planet/fleet

## Zoom Levels

The map supports smooth zoom from galaxy overview (all planets visible) to close-up (individual planet detail).

At different zoom levels, the rendering adapts:

| Zoom Level | What's Shown |
|------------|-------------|
| Far (overview) | Planet dots only, no labels, no fleet icons. Scanner coverage as faint regions. |
| Medium | Planet dots + names, fleet icons, route lines, scanner circles |
| Close | Full detail — planet names, fleet names, composition count, waypoint markers |

The zoom level thresholds are tuned during implementation. The principle: don't render what you can't read.

## Pan and Zoom Controls

- **Scroll wheel** — zoom in/out, centred on cursor position
- **Click and drag** (on empty space) — pan the map
- **Pinch to zoom** — on trackpad/touch (future, not Phase 2 priority)
- **Keyboard** — arrow keys to pan, +/- to zoom
- **Double-click planet/fleet** — zoom to and centre on that object
- **Fit to galaxy** — button or keyboard shortcut to reset zoom to show everything

## Click Interactions

- **Click planet** — select it, open detail panel with planet info
- **Repeated clicks on a planet with fleets in orbit** — cycle through the planet and each orbiting fleet, then wrap back to the planet
- **Click fleet (deep space only)** — select it, open detail panel with fleet info and waypoint editor
- **Repeated clicks on overlapping fleets** — cycle through fleets that are indistinguishable or nearly indistinguishable at the current zoom level
- **Click empty space** — deselect current selection
- **Right-click / long-press on map** — context menu (e.g. "set waypoint here" when a fleet is selected)

## Waypoint Setting

When a fleet is selected:

1. The fleet's current waypoints are shown as connected markers on the map
2. **Click a planet** — adds it as the next waypoint (snaps to planet position)
3. **Click empty space** — adds a deep-space waypoint at that position
4. **Click an existing waypoint marker** — select it for editing or deletion
5. **Drag a waypoint marker** — reposition it
6. **Right-click a waypoint** — remove it
7. Waypoint changes are local until the player submits the turn — the detail panel shows unsaved changes

This is the core interaction loop for Phase 2: select fleet → set waypoints → submit turn → see results.
