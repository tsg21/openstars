# PRD 62 — Planet Detail Panel

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Planet View

When a planet is selected, the detail panel shows what the player knows about it, based on `scan_level` (PRD 11):

**`scan_level: "detailed"` (own planet or within penetrating scanner range):**
- Planet name
- Owner (you / other player name)
- Population
- Mine count
- Factory count
- Mineral summary (see Mineral Display below)
- *(Future phases: production queue, defences, habitability)*

**`scan_level: "basic"` (within normal scanner range):**
- Planet name
- Owner (or "Uncolonised")
- *(No population or mineral detail — normal scanners don't penetrate)*

**`scan_level: "none"` (outside all scanner range):**
- Planet name
- "No scanner data" or "Unexplored"
- Planet is still visible on the map (all planets are always on the map — PRD 11) but no information beyond name and position

## Mineral Display

When a planet is selected and `scan_level` is `"detailed"`, the detail panel shows mine and factory counts below the population line, followed by a mineral summary. The mineral summary is a canvas-rendered bar chart — three rows, one per mineral type.

**Reference:** The original Stars! "Planet Summary" panel (bottom-right of `docs/references/stars-1995-screenshot-51464.jpg`).

### Layout

```
┌────────────────────────────────┐
│  Ironium    [████░░    ]  642kT│
│  Boranium   [██░░░░░   ]  213kT│
│  Germanium  [███░░     ]  416kT│
└────────────────────────────────┘
```

Each bar row contains:
- **Label** — mineral name (left-aligned, fixed width)
- **Bar** — canvas-rendered horizontal bar, two segments left to right:
  - **Bright segment** — surface stockpile (current `minerals` value), anchored at the left
  - **Dark/muted segment** — mining rate (`mining_rate`), immediately to the right of the bright segment, showing what will be added next turn
- **Value** — surface stockpile in kT (right-aligned)

### Colours

| Mineral    | Bright (stockpile) | Dark (mining rate) |
|------------|--------------------|--------------------|
| Ironium    | `#60a5fa` (blue)   | `#1e40af`          |
| Boranium   | `#facc15` (yellow) | `#713f12`          |
| Germanium  | `#e5e7eb` (white)  | `#6b7280`          |

These match the original Stars! colour assignments (blue / yellow / white).

### Scale

The bar chart x-axis scales to the largest single stockpile value across all three minerals on the selected planet (minimum scale: 100kT). This keeps bars comparable within a planet without being dwarfed by one large stockpile.

### Implementation

Rendered as a `<canvas>` element inside the React detail panel. The canvas redraws on selection change. No animation required — static render on data change is sufficient.

Data source: `PlayerPlanet.minerals` (stockpile), `PlayerPlanet.mining_rate` (per-mineral next-turn output), `PlayerPlanet.concentrations`.

If `minerals`, `mining_rate`, or `concentrations` are absent (scan level below detailed, or planet not yet initialised), the mineral section is omitted entirely.
