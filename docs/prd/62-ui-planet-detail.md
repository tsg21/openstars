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
- Planetary scanner installation (see Scanner Installation Display below)
- Mineral summary (see Mineral Display below)
- Habitability bars (see Habitability Display below)
- Research contribution toggle (own planet only — see Research Contribution below)
- *(Future phases: production queue, defences)*

**`scan_level: "basic"` (within normal scanner range):**
- Planet name
- Owner (or "Uncolonised")
- *(No population or mineral detail — normal scanners don't penetrate)*

**Stale data (`scan_age > 0`, previously scanned, now outside range):**
- Planet name
- A staleness banner: "Scan age: N turns"
- All fields from the last recorded scan (owner, and population/minerals/etc. if last scan was detailed), rendered in muted/greyed colours to indicate the data may be out of date
- If last scan was detailed, the mineral and habitability displays are shown in their muted form (see Stale Colours below)
- Scanner row is only shown for detailed scans (not stale basic scans)

**`scan_level: "none"` (outside all scanner range, never scanned):**
- Planet name
- "Unexplored" label
- Planet is still visible on the map (all planets are always on the map — PRD 11) but no information beyond name and position

## Fleets in Orbit

When a planet is selected, a "Fleets in Orbit" section appears if any fleets are currently orbiting. Each entry shows:

- Fleet name
- Owner (player name, or "You" for own fleets)
- Ship count

Clicking a fleet entry selects that fleet and opens the fleet detail panel.

If no fleets are in orbit the section is omitted entirely.

This section is shown regardless of `scan_level` — any fleet in orbit is visible to any player who can see the planet (consistent with scanner rules in PRD 11).

## Scanner Installation Display

Shown when `scan_level` is `"detailed"`. Appears between the factory count line and the mineral display.

### Own Planet

If `has_scanner` is true, show the current scanner tier name and its ranges:

```
Scanner:  Scoper 220   (normal 220 pc)
```

For Snooper-class installations (penetrating capability):

```
Scanner:  Snooper 320X   (normal 320 pc / penetrating 160 pc)
```

The active tier is derived server-side from `has_scanner` plus the planet owner's Electronics and Bio-Tech levels — the client receives the resolved tier name and range values in the player state.

If `has_scanner` is false, show a muted placeholder:

```
Scanner:  None installed
```

No inline production shortcut is shown here — the player uses the production queue panel (future phase) to add one.

### Enemy Planet (Penetrating Scan)

If the enemy planet has a scanner installation, show only the presence — not the tier or range:

```
Scanner:  Installed
```

If no scanner is present:

```
Scanner:  None
```

### Data Source

`PlayerPlanet.scanner` — a field added alongside `has_scanner` in the player-state shape for detailed-scan planets:

```json
{
  "scanner": {
    "installed": true,
    "name": "Scoper 220",
    "normal": 220,
    "penetrating": 0
  }
}
```

For own planets, `installed`, `name`, `normal`, and `penetrating` are always present when `has_scanner` is true. When `has_scanner` is false the field is `null`. For enemy planets at detailed scan level, only `installed` (boolean) is returned — the server omits `name` and range values.

---

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

When `scan_level` is `"stale"`, the mineral bars are rendered at 50% opacity to signal that the data may no longer be accurate. The `mining_rate` segment is omitted for stale data (it was a derived field at scan time and is certainly outdated).

## Habitability Display

When a planet is selected and `scan_level` is `"detailed"`, the detail panel shows a habitability summary below the mineral display. The habitability summary is a canvas-rendered bar chart — three rows, one per environmental factor.

**Reference:** The original Stars! habitability panel showing coloured range bands and a crosshair marker.

### Layout

```
┌──────────────────────────────────────┐
│  Gravity     [░░░████████░░░]  1.60g│
│  Temperature [░░░░████████░░]  -56°C │
│  Radiation   [░░░░████████░░]   50mR │
└──────────────────────────────────────┘
```

Each bar row contains:
- **Label** — factor name (left-aligned, fixed width)
- **Bar** — canvas-rendered horizontal bar spanning the full 0–100 range:
  - **Background** — black (out-of-range zone)
  - **Coloured band** — the race's habitable range for this factor, filled with the factor colour
  - **Crosshair marker** — a circle with a cross (⊕) at the planet's current value, drawn on top of the bar
- **Value** — the planet's value formatted with display units (right-aligned)

The crosshair marker sits inside the coloured band when the planet is within range (positive hab contribution), and in the black zone when outside range (hostile contribution).

### Colours

| Factor      | Band colour          |
|-------------|----------------------|
| Gravity     | `#3b82f6` (blue)     |
| Temperature | `#dc2626` (red)      |
| Radiation   | `#16a34a` (green)    |

### Display Units

Raw values (0–100 integers stored in `Habitability`) are converted to display units for the value label:

| Factor      | Conversion                              | Example |
|-------------|------------------------------------------|---------|
| Gravity     | 0 → 0.12g, 100 → 4.00g (exponential)   | 1.60g   |
| Temperature | 0 → −200°C, 100 → +200°C (linear)      | −56°C   |
| Radiation   | Direct (mR)                             | 50mR    |

The exact gravity formula follows the original Stars! convention: `g = 0.12 × (4.00/0.12)^(v/100)`. The bar position always uses the raw 0–100 value — only the label converts to display units.

### Race Range

The habitable range band is drawn from the race's low to high values for each factor. For the current JOAT defaults (PRD 14): all three ranges are [15, 85].

### Implementation

Rendered as a `<canvas>` element inside the React detail panel, below the mineral display. Same redraw-on-selection-change approach.

Data source: `PlayerPlanet.habitability` (planet values), race constants from the frontend (JOAT defaults hardcoded until race design is implemented).

If `habitability` is absent (scan level below detailed), the habitability section is omitted entirely.

When `scan_level` is `"stale"`, the habitability bars are rendered at 50% opacity, consistent with the mineral display treatment.

## Research Contribution

Shown on **own planets only**. Gated on ownership, not `scan_level` — own planets are always `scan_level: "detailed"` in the player view (PRD 11), but the reverse is not true: an enemy planet under a penetrating scanner is also `"detailed"` and must not expose this control.

The practical gate in the client is "is `PlayerPlanet.contribute_only_leftover_to_research` present?" — PRD 21 specifies that field is populated only for the viewing player's own planets, so its presence is the definitive owner-only signal and avoids an explicit ownership comparison.

Appears below the habitability display, above the (future) production queue section. The section exposes the per-planet `contribute_only_leftover_to_research` toggle defined in [PRD 21 — Research & Technology](21-research-and-technology.md).

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Research                                               │
│  [ ] Contribute only leftover resources to research    │
│                                                         │
│  Reserved this turn:   ≈ 62 resources  (15% of 412)    │
│  Projected leftover:   ≈ 18 resources                   │
└─────────────────────────────────────────────────────────┘
```

Elements:

- **Toggle** — a labelled checkbox wired to `PlayerPlanet.contribute_only_leftover_to_research`. Clicking it queues a `set_planet_production_mode` command for this planet (see Command Model below).
- **Reserved this turn** — `floor(total_resources * allocation_percent / 100)` when the toggle is off; `0` when on. Uses the player's current `research.allocation_percent` from `PlayerState` and the planet's total resources.
- **Projected leftover** — a rough estimate of resources the production queue is not expected to spend this turn. Derivation is best-effort — it can read the queued items' remaining cost against `production_budget`. If the estimate is not readily available in the first pass, this line may be omitted and added as a follow-up.

When the toggle is **on**, the "Reserved" line reads `— (leftover only)` and the "Projected leftover" line becomes the planet's sole contribution figure.

### Command Model

Flipping the toggle queues a single `set_planet_production_mode` command scoped to this planet:

```json
{
  "type": "set_planet_production_mode",
  "planet_id": "PLk8m3x2",
  "contribute_only_leftover_to_research": true
}
```

Only one such command per planet per turn — a second flip replaces the first in the local unsubmitted-commands buffer. If the player flips the toggle back to its server-side value, the pending command is removed entirely (no no-op command submitted).

### Visibility

- The section is absent for non-own planets, including enemy planets under a penetrating scanner — the toggle is owner-only, keyed on `PlayerPlanet.contribute_only_leftover_to_research` being present.
- The section is absent on stale own planets (an own planet can become stale if it is captured and later falls out of scanner range); the toggle needs a live planet view to edit.
- The section is absent when the player's `PlayerState.research` is absent (e.g. pre-PRD 21 states during migration), since the "Reserved this turn" figure has no source.
