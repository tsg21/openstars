# Planet detail: habitability display (PRD 62)

Wire up the population and habitability data from PRD 14 into the planet detail panel.

## Scope

Frontend only. The backend already emits `habitability`, `max_population`, and `pop_growth` on `PlayerPlanet` (PRD 14). This task adds the TypeScript types, the canvas habitability bars component, and the panel wiring.

---

## Step 1: Frontend types (`src/types/game.ts`)

- [x] Add `Habitability` interface: `{ gravity: number; temperature: number; radiation: number }`
- [x] Extend `PlayerPlanet` with optional fields:
  - `habitability?: Habitability | null`
  - `maxPopulation?: number | null`
  - `popGrowth?: number | null`
- [x] Add `ColonistsDiedEvent` and `PlanetAbandonedEvent` event types and add them to the `GameEvent` union:
  ```ts
  interface ColonistsDiedEvent  { type: "colonists_died";  planetId: string; planetName?: string; deaths: number; cause: string; turn: number }
  interface PlanetAbandonedEvent { type: "planet_abandoned"; planetId: string; planetName?: string; turn: number }
  ```

---

## Step 2: Habitability bars component (`DetailPanel.tsx`)

Add a `HabitabilityBars` component rendered on a `<canvas>`, modelled on the existing `MineralBars` component.

Each of the three rows (Gravity, Temperature, Radiation) renders:
- A label (left-aligned, fixed width)
- A full-width track (black background, spanning raw values 0–100)
- A coloured band from the race's low to high for that factor (JOAT defaults: [15, 85] for all three)
- A crosshair marker — a circle with a cross (⊕) — drawn at the planet's raw value on top of the track
- A value label (right-aligned) formatted with display units

**Colours:**

| Factor      | Band colour      |
|-------------|------------------|
| Gravity     | `#3b82f6` (blue) |
| Temperature | `#dc2626` (red)  |
| Radiation   | `#16a34a` (green)|

**Display units (value label only — bar position always uses raw 0–100):**

| Factor      | Conversion                                             |
|-------------|--------------------------------------------------------|
| Gravity     | `0.12 × (4.00/0.12)^(v/100)` g, formatted to 2 d.p.  |
| Temperature | `(v - 50) × 4` °C (0→−200°C, 50→0°C, 100→+200°C)    |
| Radiation   | `v` mR (direct)                                        |

**JOAT race range constants** (hardcode in the component for now):
```ts
const JOAT_RANGE = { low: 15, high: 85 };
```

**Crosshair marker:** draw a small circle (radius ~5px) at the value position with a horizontal and vertical line through the centre, using a contrasting colour (white or the band colour at full opacity).

- [x] Implement `HabitabilityBars` component
- [x] Canvas is `aria-label="Habitability bars"` and `height: 66` (same as mineral bars)

---

## Step 3: Wire into `PlanetDetail`

- [x] Below the mineral bars block, add a `HabitabilityBars` section when `planet.scanLevel === "detailed"` and `planet.habitability != null`
- [x] Below population (own planets, `scanLevel === "detailed"`), show `max_population` and `pop_growth`:
  - `Max pop: 1,000,000` (formatted with `toLocaleString`)
  - `Growth: +3,750 / turn` (signed; omit if null)

---

## Step 4: Tests and lint

- [x] Add `DetailPanel.test.tsx` coverage:
  - Habitability bars render when `scanLevel === "detailed"` and `habitability` is present
  - Habitability bars absent when `scanLevel === "basic"`
  - `max_population` and `pop_growth` visible for own planet
  - `max_population` absent when viewing another player's planet
- [x] `cd frontend && npm run typecheck` — clean
- [x] `cd frontend && npm run lint` — clean
- [x] `cd frontend && npm test` — all passing
