# PRD 12 — Economy & Resources

## Overview

This document defines the planetary economy model for OpenStars! — minerals, mines, factories, and resources. These are the foundational systems that drive production, ship building, and technological progress. Without a functioning economy, players can't build anything.

This PRD covers the **simulation layer** — what the engine calculates each turn.

## Design Philosophy

The economy faithfully reproduces the core Stars! mechanics:

- **Three mineral types** — each with distinct strategic value
- **Concentration-based mining** — mineral extraction degrades over time, forcing expansion
- **Factory-amplified resources** — population produces resources; factories multiply them
- **Race-configurable parameters** — economy settings are per-race (hardcoded defaults until race design is implemented)

The system is deterministic: given the same state and RNG seed, the same economy results are produced every time.

## Minerals

### The Three Mineral Types

| Mineral    | Role | Colour |
|------------|------|--------|
| Ironium    | Basic construction — hulls, structures, most components | Blue |
| Boranium   | Advanced components — weapons, shields, electronics | Yellow |
| Germanium  | High-tech items — engines, scanners, factories | White |

All three minerals are measured in **kT** (kilotons). They are physical commodities — they sit on planet surfaces, are carried as cargo, and are consumed during production.

### Mineral Concentrations

Every planet has a **concentration** value for each mineral type, representing how rich the planet's deposits are.

| Property | Value |
|----------|-------|
| Range | 1–200 (integer) |
| Display | Shown to players as the raw value |
| Effect | Linearly scales mining output |

A concentration of 100 is the baseline — each mine produces its rated output. At concentration 50, output is halved. At concentration 150, output is 50% higher.

Concentrations are generated at game creation (turn 0) for every planet. They deplete over time as minerals are extracted (see "Concentration Depletion").

#### Home Planet Concentrations

Home planets have a **permanent floor** of 30 on each mineral concentration. This applies at generation **and throughout gameplay** — home world concentrations never drop below 30, regardless of who occupies the planet. This is a property of the planet itself, not the owner.

Random planets have no guaranteed minimums — concentrations are uniformly distributed in the range [1, 200] per mineral type, generated using the game's seeded RNG (PRD 04).

### Surface Minerals

Each planet has a **surface mineral deposit** for each mineral type — minerals that have been mined (or were present initially) and are sitting on the planet ready to be used in production or loaded onto ships.

Surface minerals accumulate without limit. They are consumed by the production queue (future PRD) and can be transported by cargo ships (future phase).

Minerals mined in a given turn are available for production **that same turn** — the Stars! resolution order runs mining before production (see "Resolution Pipeline Changes").

#### Initial Surface Minerals

| Planet Type | Ironium | Boranium | Germanium |
|-------------|---------|----------|-----------|
| Home planet | 300 kT  | 300 kT   | 300 kT    |
| Other       | 0 kT    | 0 kT     | 0 kT      |

## Mines

Mines extract minerals from a planet's deposits. More mines = more minerals per turn, but concentrations gradually deplete.

### Mining Output

Each turn, the mining step produces minerals for each owned planet:

```
minerals_mined[type] = floor(mines_operated × mine_rate × concentration[type] / 100)
```

Where:
- `mines_operated` = min(planet.mines, max_mines_for_population)
- `max_mines_for_population` = floor(population / 10000) × mines_per_10k_colonists
- `mine_rate` = kT per mine per turn at concentration 100 (default: 1.0 — see Race Economy Defaults)
- `concentration[type]` = current concentration for that mineral type (1–200)

Mining output is calculated **independently for each mineral type** using the planet's concentration for that type. The same number of mines produces different amounts of each mineral based on their respective concentrations.

Mined minerals are added to the planet's surface deposits.

### Concentration Depletion

Mining depletes mineral concentrations over time. The depletion model tracks cumulative **mine-years** per mineral type per planet:

> One mine-year = one mine operating on a planet for one year (turn).

Each turn, `mines_operated` is added to the mine-year accumulator for **each** mineral type independently. When the accumulated mine-years reach a threshold, the concentration drops by 1 point and the accumulator resets:

```
mine_years_to_deplete[type] = floor(12500 / concentration[type])
```

The process each turn, per mineral type:

```python
planet.mine_years[type] += mines_operated
threshold = 12500 // concentration[type]
while planet.mine_years[type] >= threshold and concentration[type] > min_concentration:
    concentration[type] -= 1
    planet.mine_years[type] -= threshold
    threshold = 12500 // concentration[type]  # recalculate for new concentration
```

Where `min_concentration` is 1 for normal planets, or 30 for home worlds.

**Key properties:**
- Depletion is **independent of mining efficiency** — two players with the same number of mines over the same number of years get the same concentration decrease, regardless of race settings
- High concentrations deplete faster — at concentration 200 it takes only 62 mine-years per point; at concentration 100 it takes 125 mine-years per point
- Low concentrations deplete slower — at concentration 10 it takes 1,250 mine-years per point (there's less to extract, so it's harder to exhaust)
- Concentrations never drop below 1 (or 30 for home worlds)

### Mine Limits

The number of mines a planet can operate is limited by population:

```
max_mines = floor(population / 10000) × mines_per_10k_colonists
```

You can build more mines than you can operate (e.g. in anticipation of population growth), but only `min(mines, max_mines)` produce output each turn.

### Mine Construction Cost

| Cost Type | Amount |
|-----------|--------|
| Resources | 5 per mine |
| Minerals  | None |

Mines are cheap to build but limited by the population needed to operate them.

## Factories

Factories generate resources from population. They are the economic multiplier — without factories, a planet's resource output depends solely on population.

The manual describes factories as "virtual colonists" — once built, they produce work and consume nothing.

### Resource Generation

Total resources available each turn on a planet:

```
population_resources = floor(population / colonists_per_resource)
factory_resources = floor(factories_operated × factory_rate)
total_resources = population_resources + factory_resources
```

Where:
- `factories_operated` = min(planet.factories, max_factories_for_population)
- `max_factories_for_population` = floor(population / 10000) × factories_per_10k_colonists
- `factory_rate` = resources per factory (default: 1.0 — see Race Economy Defaults)
- `colonists_per_resource` = population needed per 1 resource (default: 1000 — see Race Economy Defaults)

Resources are **not stockpiled** — they are generated and consumed within the same turn. Unspent resources are directed into research (future PRD). This is consistent with Stars! — resources represent work capacity, not a stored commodity.

### Factory Limits

Like mines, factory operation is limited by population:

```
max_factories = floor(population / 10000) × factories_per_10k_colonists
```

### Factory Construction Cost

| Cost Type  | Amount |
|------------|--------|
| Resources  | 10 per factory |
| Germanium  | 4 kT per factory |

The germanium cost creates an early-game bottleneck — new colonies need germanium imports to industrialise. This is a core Stars! dynamic.

**G-box variant (future):** A race trait that reduces the germanium cost by 1 kT. Not implemented until race design.

## Race Economy Defaults

Until race design is implemented, all players use these defaults (equivalent to JOAT — Jack of All Trades):

| Parameter | Value | Description |
|-----------|-------|-------------|
| `colonists_per_resource` | 1000 | 1 resource per 1,000 colonists |
| `factory_rate` | 1.0 | 1 resource per factory per turn |
| `factory_cost_resources` | 10 | Resources to build one factory |
| `factory_cost_germanium` | 4 | kT germanium to build one factory |
| `factories_per_10k_colonists` | 10 | Max factories operated per 10,000 pop |
| `mine_rate` | 1.0 | 1 kT per mine per turn (at concentration 100) |
| `mine_cost_resources` | 5 | Resources to build one mine |
| `mines_per_10k_colonists` | 10 | Max mines operated per 10,000 pop |

These values are stored in the player/race data structure (future PRD). For now, they are engine constants.

## Schema Changes

### Global State — `PlanetState`

Extended fields (all new fields default to 0):

```python
class Minerals(BaseModel):
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0

class PlanetState(BaseModel):
    id: str
    owner: str | None = None
    population: int = 0
    mines: int = 0                          # NEW
    factories: int = 0                      # NEW
    minerals: Minerals = Minerals()         # NEW — surface deposits
    concentrations: Minerals = Minerals()   # NEW — current mineral concentrations
    mine_years: Minerals = Minerals()       # NEW — cumulative mine-years per mineral (for depletion)
    is_homeworld: bool = False              # NEW — true for starting home planets (concentration floor = 30)
```

#### Example: Home Planet at Turn 0

```json
{
  "id": "PLk8m3x2",
  "owner": "tim",
  "population": 25000,
  "mines": 10,
  "factories": 10,
  "minerals": { "ironium": 300, "boranium": 300, "germanium": 300 },
  "concentrations": { "ironium": 97, "boranium": 54, "germanium": 112 },
  "mine_years": { "ironium": 0, "boranium": 0, "germanium": 0 },
  "is_homeworld": true
}
```

#### Example: Uncolonised Planet

```json
{
  "id": "PL4fn9v6",
  "owner": null,
  "population": 0,
  "mines": 0,
  "factories": 0,
  "minerals": { "ironium": 0, "boranium": 0, "germanium": 0 },
  "concentrations": { "ironium": 145, "boranium": 23, "germanium": 88 },
  "mine_years": { "ironium": 0, "boranium": 0, "germanium": 0 },
  "is_homeworld": false
}
```

### Player State — `PlayerPlanet`

Economy data visibility depends on scan level:

| Scan Level | Visible Economy Data |
|------------|---------------------|
| `"none"` | Nothing — planet position and name only |
| `"basic"` | Owner only (existing behaviour) |
| `"detailed"` | Owner, population, mines, factories, surface minerals, concentrations |

Only the planet's owner sees full detail. Other players see data based on scanner coverage (PRD 11).

Extended `PlayerPlanet` fields (all optional):

```python
class PlayerPlanet(BaseModel):
    # ... existing fields ...
    mines: int | None = None                    # NEW
    factories: int | None = None                # NEW
    minerals: Minerals | None = None            # NEW — surface deposits
    concentrations: Minerals | None = None      # NEW — current concentrations
    resources: int | None = None                # NEW — this turn's total resources
    mining_rate: Minerals | None = None         # NEW — kT mined per type this turn
```

The `resources` field is a convenience for the UI — calculated from population + factories, included in the player state so the client doesn't need to know the formula.

The `mining_rate` field shows the current per-turn mining output per mineral, matching the Stars! UI which shows this in the mineral display.

**Note:** `mine_years` and `is_homeworld` are internal engine state — never exposed in the player state.

### Player State — Events

New event types for economy:

```json
{
  "type": "mining_complete",
  "turn": 5,
  "planet_id": "PLk8m3x2",
  "planet_name": "Earth",
  "ironium": 12,
  "boranium": 7,
  "germanium": 15
}
```

Mining events are generated per-planet per-turn when minerals are extracted. These are informational — the UI can show "Earth mined 12 Ir, 7 Bo, 15 Ge this turn."

## Turn 0 Generation Changes

When a new game is created, the turn 0 setup (PRD 05) is extended:

1. **Generate concentrations** for every planet using the seeded RNG
   - Each mineral type: uniform random integer in [1, 200]
   - Home planets: clamp to minimum 30 per mineral type
2. **Set home planet economy:**
   - `mines`: 10
   - `factories`: 10
   - `minerals`: `{ ironium: 300, boranium: 300, germanium: 300 }`
   - `mine_years`: `{ ironium: 0, boranium: 0, germanium: 0 }`
   - `is_homeworld`: true
3. All other planets: mines, factories, surface minerals, and mine-years start at 0; `is_homeworld`: false

## Resolution Pipeline Changes

The turn resolution pipeline (PRD 07) adds two steps, matching the Stars! resolution order (mining before production):

```
Step 1: Apply commands
Step 2: Move fleets
NEW → Step 3: Mining
NEW → Step 4: Calculate resources (for production — future PRD)
Step 5: Increment turn counter
```

### Step 3: Mining

For each planet with an owner and mines > 0:

1. Calculate `mines_operated = min(planet.mines, floor(population / 10000) × mines_per_10k_colonists)`
2. For each mineral type:
   a. `mined = floor(mines_operated × mine_rate × concentration[type] / 100)`
   b. Add `mined` to `planet.minerals[type]`
3. Apply concentration depletion (see "Concentration Depletion" above) — add `mines_operated` to each mineral's mine-year accumulator, then deplete as thresholds are reached
4. Generate `mining_complete` event for the planet owner

Processing order: planets sorted by planet ID (lexicographic), for determinism.

### Step 4: Calculate Resources

For each planet with an owner:

1. `population_resources = floor(population / colonists_per_resource)`
2. `factories_operated = min(planet.factories, floor(population / 10000) × factories_per_10k_colonists)`
3. `factory_resources = floor(factories_operated × factory_rate)`
4. `total_resources = population_resources + factory_resources`
5. Store `total_resources` for use by the production queue (future PRD)

Until the production queue is implemented, calculated resources are included in the player state for display but not spent. Unspent resources would normally go to research — that's also a future PRD.

## UI Considerations

This PRD does not define UI layout (that's PRD 08), but notes for the frontend:

- **Planet detail panel** should show: mines, factories, surface minerals (per type), concentrations (per type), mining rate (per type), resources per turn
- **Mineral colours** in the UI: Ironium = blue, Boranium = yellow, Germanium = white (matching Stars!)
- **Concentration display**: Show as a number (e.g. "97") or with a bar/gauge. Stars! used a bar chart with a diamond marker for concentration — either approach works.
- **Resources**: Show the total with a breakdown tooltip (population + factory contributions)
- **Mining rate**: Stars! shows a dark bar for "amount that will be mined next year" next to the bright bar for surface minerals — replicate this pattern
