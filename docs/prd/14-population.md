# PRD 14 — Population & Habitability

## Overview

This document defines the population growth model for OpenStars! — how planets are characterised by their environment, how race habitability ranges determine the desirability of a planet, and how population grows or dies each turn. Population is the foundation of the economy: more people means more resources, more mines, and more factories that can be operated.

This PRD covers the **simulation layer** — what the engine calculates each turn during the population phase. UI layout is addressed separately in PRD 08.

## Design Philosophy

Population mechanics faithfully reproduce the core Stars! model:

- **Three environmental axes** — gravity, temperature, radiation each contribute independently to habitability
- **Race-relative habitability** — a planet's value depends on who is asking; the same planet may be paradise to one race and lethal to another
- **Logistic growth** — population grows fast when small relative to capacity, slows near the cap
- **Killer planets** — colonists die on planets outside their habitable range; this is a strategic risk the player takes
- **Overcrowding kills** — exceeding capacity causes deaths and wasted productivity
- **Race-configurable parameters** — habitability ranges and max growth rate come from the player's race record (PRD 22)

The system is deterministic: given the same state and RNG seed, the same population results are produced every time.

---

## Planet Environment

### The Three Environmental Factors

Every planet has three environmental attributes that determine how hospitable it is to a given race:

| Factor      | Internal Range | Display Unit | Display Range    |
|-------------|---------------|--------------|------------------|
| Gravity     | 0–100 integer | g            | 0.12g – 8.00g    |
| Temperature | 0–100 integer | °C           | −200°C – +200°C  |
| Radiation   | 0–100 integer | mR           | 0 mR – 100 mR    |

The internal 0–100 representation is used for all engine calculations. Display conversions are:

```
gravity_g     = 0.12 × exp(ln(8.0 / 0.12) × internal / 100)
temperature_c = (internal − 50) × 4           # −200°C to +200°C, linear
radiation_mr  = internal                       # 0 to 100 mR, identity
```

Display conversions are UI-only. The engine stores and operates on 0–100 integers throughout.

### Generation

Planet environment values are generated at turn 0 using the game's seeded RNG (PRD 04):

- Each of the three factors is drawn as a **uniform random integer in [0, 100]**
- No minimum is enforced — all values are possible
- Generation is independent per factor and per planet

### Home Planet Environment

Each player's home planet is set to the **racial ideal** for all non-immune factors during turn-0 resolution (PRD 22), ensuring a 100% habitable starting world. For JOAT (the default race), the ideal is 50 for each factor. For factors the race is immune to, the planet keeps its random game-start value.

---

## Race Habitability

### Habitable Range

A race defines a **habitable range** `[low, high]` (0–100 internal units) for each environmental factor. The racial ideal is the midpoint of that range.

Planets with all three values inside their respective ranges are habitable (positive habitability). Planets with one or more values outside are hostile (negative habitability).

### Maximum Growth Rate

A race also defines a **maximum colonist growth rate per year** — the growth rate achieved on a 100%-habitable planet when below 25% of max capacity. This is a percentage.

### Race habitability parameters

Habitability ranges and the maximum growth rate come from the player's race (PRD 22). Engine resolve steps look up `player.race.habitability.<factor>.range`, `player.race.habitability.<factor>.immune`, and `player.race.max_growth_rate` per planet owner.

The Humanoid (JOAT) preset reproduces the values used here historically:

| Parameter             | Humanoid (JOAT) value | Notes                                       |
|-----------------------|-----------------------|---------------------------------------------|
| `gravity` range       | [15, 85]              | Internal units; ideal at 50 (≈ 1.0g)       |
| `temperature` range   | [15, 85]              | Internal units; ideal at 50 (0°C)          |
| `radiation` range     | [15, 85]              | Internal units; ideal at 50 (50 mR)        |
| `max_growth_rate`     | 15%                   | Growth rate on a 100% world at low pop      |
| `base_max_population` | 1,000,000             | Max pop on a 100%-habitable world (engine constant — not on the race record) |

A factor's `immune` flag short-circuits the per-factor habitability contribution to `+33.333` regardless of the planet's environment value. This is distinct from a max-width range whose endpoints still score `0`.

PRD 22 owns the per-parameter ranges, immunity semantics, and points-budget cost.

---

## Habitability Calculation

Habitability is computed from a planet's three environment values and the race's three habitable ranges. It is a signed integer percentage in the range **[−45, +100]**.

### Per-Factor Contribution

For each factor `f` with race range `[low_f, high_f]` and planet value `v_f`:

```python
ideal_f      = (low_f + high_f) / 2
half_width_f = (high_f - low_f) / 2

if low_f <= v_f <= high_f:
    # Inside habitable range: scale from +33.33 at ideal to 0 at edge
    contribution_f = (1.0 - abs(v_f - ideal_f) / half_width_f) * 33.333

elif v_f < low_f:
    # Below range: penalty proportional to distance below low_f
    distance = low_f - v_f
    denominator = max(low_f, 1)          # avoids div/0 when low_f = 0
    contribution_f = -(distance / denominator) * 15.0

else:  # v_f > high_f
    # Above range: penalty proportional to distance above high_f
    distance = v_f - high_f
    denominator = max(100 - high_f, 1)   # avoids div/0 when high_f = 100
    contribution_f = -(distance / denominator) * 15.0
```

**Properties:**
- Maximum in-range contribution: **+33.33** per factor × 3 = **+100** total
- Maximum out-of-range penalty: **−15** per factor × 3 = **−45** total
- The out-of-range penalty reaches −15 only when the planet value is at the extreme end of the spectrum

### Combined Habitability

```python
habitability = round(contribution_gravity + contribution_temperature + contribution_radiation)
```

The result is a signed integer, clamped to [−45, +100].

Habitability is **not stored in global state** — it is computed on demand from environment values and race parameters. It is included in `PlayerPlanet` as a convenience field.

### Special Cases

- **Minimum positive:** planets with habitability in [1, 4] are treated as **5%** when computing max population only. The displayed value is unchanged.
- **Zero habitability:** no growth and no death. Max population is 50,000 (the 5% floor).
- **Immune factor (future):** a race immune to a factor always receives +33 for that factor. Not implemented until race design.

---

## Maximum Population

```python
effective_hab = max(habitability, 5) if habitability > 0 else habitability
max_population = base_max_population * effective_hab / 100
```

Only valid for positive habitability; killer planets have no max population concept.

**Examples (JOAT defaults):**

| Habitability | Max Population          |
|-------------|-------------------------|
| 100%        | 1,000,000               |
| 50%         | 500,000                 |
| 10%         | 100,000                 |
| 3%          | 50,000 (5% floor)       |
| 0%          | 50,000 (5% floor)       |
| −9%         | n/a — killer planet     |

---

## Population Growth

Population changes are resolved in **step 6** of the pipeline (after production), matching the original Stars! turn order.

### Positive Habitability: Growth

For planets with `habitability >= 0` and `0 < population <= max_population`:

```python
growth_rate = (habitability / 100) * max_growth_rate   # e.g. 50% hab × 15% = 0.075

if population <= 0.25 * max_population:
    # Below 25% capacity: full exponential rate
    growth = floor(population * growth_rate)
else:
    # Above 25% capacity: logistic slowdown toward zero at max_population
    remaining = (max_population - population) / (0.75 * max_population)
    growth = floor(population * growth_rate * max(remaining, 0.0))

population = min(population + growth, max_population)
```

**Key properties:**
- Below 25% capacity: growth is purely exponential at the full rate
- Between 25% and 100%: growth rate scales down linearly; reaches zero when population hits the cap
- Population never exceeds `max_population` through natural growth

### Negative Habitability: Colonist Death

For planets with `habitability < 0` and `population > 0`:

```python
death_rate = abs(habitability) / 10 / 100    # e.g. −10% hab → 1% death rate per year
deaths = floor(population * death_rate)
population = max(population - deaths, 0)

if population == 0:
    owner = null                              # planet becomes uncolonised
```

**Example:** habitability −10%, population 2,000 → `deaths = floor(2000 × 0.01) = 20` colonists per year.

**Non-viable outposts:** A colony with fewer than **100 colonists** on a hostile world (`habitability < 0`) is wiped out in a single turn. Such an outpost is too small to sustain itself, and this prevents tiny populations lingering indefinitely under the rounding floor. Larger hostile colonies still have a minimum of 1 death per turn enforced, so they always trend toward zero rather than stalling on fractional rates.

### Overcrowding

Overcrowding occurs when `population > max_population`. This can happen when colonists are transported to an already-full planet. The engine handles it as follows:

**Overcrowding deaths (applied during population step):**

```python
overcrowding_ratio = population / max_population    # > 1.0 when overcrowded

if overcrowding_ratio <= 1.0:
    overcrowding_deaths = 0
elif overcrowding_ratio <= 4.0:
    # Death rate scales from 0% at 100% capacity to 12% at 400% capacity
    death_rate = (overcrowding_ratio - 1.0) / 3.0 * 0.12
    overcrowding_deaths = floor(population * death_rate)
else:
    overcrowding_deaths = floor(population * 0.12)   # maximum 12% per year

population -= overcrowding_deaths
```

**Overcrowding productivity penalty** (applied during resource calculation, PRD 12):
- Population between `max_population` and `3 × max_population`: the excess portion works at **50% efficiency**
- Population above `3 × max_population`: that portion contributes **0 resources**

---

## Schema Changes

### `PlanetState` (global state)

Add a `Habitability` object with three integer fields (0–100 internal units):

- `gravity: int`
- `temperature: int`
- `radiation: int`

`PlanetState` gains: `habitability: Habitability` (default all zeros).

These values are set at turn 0 and remain constant until terraforming is implemented (future PRD).

#### Example: Home Planet at Turn 0 (JOAT)

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
  "is_homeworld": true,
  "habitability": { "gravity": 50, "temperature": 50, "radiation": 50 }
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
  "is_homeworld": false,
  "habitability": { "gravity": 72, "temperature": 31, "radiation": 58 }
}
```

### `PlayerPlanet` (player state)

New fields:

- `habitability: Habitability | None` — visible at detailed scan level
- `max_population: int | None` — owner only
- `pop_growth: int | None` — population change this turn; owner only

**Visibility rules:**

| Scan Level   | Visible Fields                                                  |
|--------------|-----------------------------------------------------------------|
| `"none"`     | Nothing                                                         |
| `"basic"`    | `owner` only                                                    |
| `"detailed"` | `owner`, `population`, `habitability`                           |
| owner        | All of the above, plus `max_population`, `pop_growth`           |

The `habitability` object (raw environment values) is the same for everyone. The derived habitability score is not stored — it is computed by each client from the environment values and their own race parameters.

### Player State Events

New event types for population:

```json
{
  "type": "colonists_died",
  "turn": 5,
  "planet_id": "PLr2j5b8",
  "planet_name": "Sirius",
  "previous_population": 5000,
  "new_population": 4950,
  "deaths": 50,
  "cause": "hostile_environment"
}
```

```json
{
  "type": "planet_abandoned",
  "turn": 5,
  "planet_id": "PLr2j5b8",
  "planet_name": "Sirius"
}
```

---

## Turn 0 Generation Changes

Turn 0 is split — see PRD 05 and PRD 22.

**Game-start generation** rolls environment values:

1. **Generate environment values** for every planet using the seeded RNG
   - Each of gravity, temperature, radiation: uniform random integer in [0, 100]

**Turn-0 resolution** overrides home-planet environment per the player's race (after race selection):

1. For each non-immune factor, override the home-planet value to the racial ideal `floor((low + high) / 2)`.
2. For each immune factor, leave the random game-start value in place.
3. Home-planet population is set to `25,000` (Humanoid baseline; PRT/LRT-driven adjustments arrive with their owning traits).

Generation order at game-start: environment values are generated **after** mineral concentrations to preserve RNG sequence compatibility with PRD 12.

---

## Resolution Pipeline Changes

The turn resolution pipeline (PRD 07) adds one step after production:

```
Step 1: Apply commands
Step 2: Move fleets
Step 3: Mining
Step 4: Calculate resources
Step 5: Production
Step 6: Population growth / death    ← NEW
Step 7: Increment turn counter
```

### Step 6: Population Growth / Death

For each planet with `owner != null`:

1. Retrieve the planet's `habitability` (the `Habitability` object with `gravity`, `temperature`, `radiation`)
2. Look up owner's race parameters from `player.race` (PRD 22)
3. Compute `habitability`
4. Compute `max_population`
5. Apply growth, death, or overcrowding as described above
6. If population dropped to 0, set `owner = null` and clear `mines`, `factories`, `production_queue`
7. Emit the appropriate population event

Processing order: planets sorted by planet ID (lexicographic), for determinism.

---

## UI Considerations

This PRD does not define UI layout (PRD 08), but notes for the frontend:

- **Planet detail panel:** show habitability %, max population, current population, and growth/death per turn
- **Habitability sign:** display with explicit sign — `+50%` for positive, `−9%` for negative
- **Colour coding in scanner:** green dot = positive habitability, red dot = negative, yellow = currently negative but terraformable to positive (future)
- **Environment bars:** show all three factors from the `habitability` object with the race's habitable range highlighted and the planet value marked — Stars! used a coloured bar with a dot marker; replicate this pattern
- **Killer planet warning:** if a player owns a negative-habitability planet, show the annual death rate prominently in the detail panel
- **Growth indicator:** small `+2,400 / turn` annotation next to population count
