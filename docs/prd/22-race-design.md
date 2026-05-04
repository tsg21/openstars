# PRD 22 — Race Design

## Overview

This document defines the **race** system for OpenStars! — the per-player bundle of identity, traits, environmental tolerances, and economic/scientific parameters that make one player's empire mechanically distinct from another's.

Until this PRD is implemented, every player is effectively a Jack-of-All-Trades clone: economy constants are hardcoded in the engine, habitability ranges are identical, and there is no mechanism for differentiating play styles. PRD 12 (Economy), PRD 14 (Population), and PRD 21 (Research) all explicitly reserve seats for race-derived values; this PRD fills those seats and adds the surrounding choice machinery.

The PRD covers the **simulation layer** — what a race is, how it is stored, how its parameters feed the rest of the engine, and how a balanced race is created. UI for the Custom Race wizard is referenced but specified separately.

---

## Design Philosophy

Race design follows the original Stars! model:

- **Race-as-data, not race-as-code** — a race is a structured record bundled into the player. Engine steps look up the record; they do not branch on player identity.
- **Six configuration steps** match the original game's wizard: identity, primary trait, lesser traits, habitability, economy, science.
- **Faithful traits** — all 10 primary racial traits (PRTs) and 14 lesser racial traits (LRTs) from the original are in scope. Asymmetric play is core to Stars!; we replicate the depth, not a simplification.
- **Server-authoritative balancing** — the advantage-points budget is enforced on the server. Clients can preview point cost as they edit, but a race is only saved if it nets ≥ 0 points.
- **Determinism preserved** — a race is set at turn-0 resolution and immutable for the life of the game. No mid-game race edits, no RNG in trait application.
- **Phased delivery** — the system is large. Not every trait ships in one go (see "Phased Implementation"), but the schema and validation are designed up front so later phases drop in without churn.

---

## Scope

### In scope (full race system, phased)

- Race identity (name, plural name, emblem).
- All 10 PRTs as a discriminated enum on the race record.
- All 14 LRTs as a set of independent boolean flags.
- Habitability ranges per environmental factor, with optional immunity per factor.
- Maximum colonist growth rate.
- Eight tunable economy parameters plus the germanium-saving factory toggle.
- Per-field research cost profile (`50% less` / `standard` / `75% extra`) plus the `start at tech 3` (or 4 for JOAT) accelerator.
- Leftover advantage point allocation (surface minerals, extra mines/factories/defenses, mineral concentration boost).
- A points budget formula that validates a race before it is saved.
- Predefined races as named immutable presets, including the seven player-selectable races from the original game.
- Custom Race wizard API — endpoints to load, save, and validate a custom race.
- Cross-PRD plumbing so the engine reads economy, habitability, growth, research-cost, population-cap, and miniaturisation values from the player's race record.

### MVP first slice (Phase A — see "Phased Implementation")

- Race identity, habitability ranges, growth rate, all eight economy parameters, race-points budget, JOAT as the only PRT, no LRTs, single race-cost profile per field.
- This is enough to deliver the backlog item *"MVP race implementation, including key traits: resources/colonist, resources/factory, resources to build factory, etc."* and to unblock players choosing differing economic builds.

### Out of scope (this PRD)

- Combat-side trait effects (e.g. WM weapons cost reduction, RS shield/armour adjustments, SS espionage). These are owned by the combat PRDs (80–82) and the component catalogue (PRD 20). This PRD declares the trait flag; the combat PRDs read it.
- The Custom Race wizard UI layout — owned by a future UI PRD; this PRD specifies the API contract.
- Mid-game race amendments. A race is locked at turn-0 resolution.
- Race file import/export across games. A race is saved per-game; a future PRD adds the player-account race library (see "Deferred follow-ups").
- Lobby-side race design. In MVP, race design happens only during a game's turn 0. Designing races outside an active game (account library, lobby drafts) is deferred — the data model and endpoint shape leave room for it.
- Tech trading, espionage payloads, and Mystery Trader interactions that depend on race traits — those PRDs will reference the trait flags this PRD declares.

---

## Race Identity

A race carries the following identity fields:

| Field          | Type   | Description                                                                                      |
|----------------|--------|--------------------------------------------------------------------------------------------------|
| `name`         | string | Singular race name (e.g. `"Humanoid"`).                                                          |
| `plural_name`  | string | Plural form (e.g. `"Humanoids"`).                                                                |
| `emblem`       | int    | `0..31`, indexes the standard race emblem set (matches the 32 icons in the original game).       |

Notes:

- The empire/race name on `Player` (PRD 05) is a duplicate display string. We retain it on `Player.name` for backwards compatibility but treat `Race.plural_name` as the canonical source. A migration sets `Race.plural_name = Player.name` for legacy global-state files.
- Emblem collision in multi-player games is allowed at the data level. The UI may surface a warning if two players in the same game pick the same emblem.
- The original game's password mechanism is intentionally omitted; OpenStars! authentication is account-based (PRD 06).

---

## Primary Racial Traits (PRTs)

Each race chooses exactly one PRT. The PRT defines the most distinctive mechanics, hulls, and components.

| ID     | Name                | Theme (full mechanic spec deferred to listed PRDs)                                                                                                                                                          |
|--------|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `HE`   | Hyper-Expansion     | Doubled effective growth rate (engine multiplier on race `max_growth_rate`); planet population cap halved; cannot build stargates; unique Mini-Colonizer and Meta Morph hulls, Settler's Delight engine, Flux Capacitor (Flux Capacitor's +20% beam-weapon boost vs the standard +10% Capacitor is consumed by the combat PRDs). |
| `SS`   | Super Stealth       | Free 75% cloak on all owned ships and starbases; espionage adds research per field; +1 safe minefield speed; unique Rogue and Stealth Bomber hulls; Pick Pocket / Robber Baron / Chameleon / Shadow tech.   |
| `WM`   | War Monger          | Weapons components cost −25%; +0.5 movement squares per round in battle (capped at 2.5); ground-attack bonus; cannot lay mines; planetary defenses limited to SDI/Missile; unique Battle Cruiser, Dreadnought.|
| `CA`   | Claim Adjuster      | Owned planets terraformed automatically each turn to the limit of current biotech; planets revert if abandoned/captured; unique Retro Bomb and Orbital Adjuster.                                            |
| `IS`   | Inner-Strength      | Colonists reproduce on freighters (½ rate, beam down on owned planets); 2× landing-defence; 1.5× repair; planetary defenses 40% cheaper; weapons cost +25%; no smart bombs; unique Super Freighter, Fuel Transport, Croby Sharmor, Fielded Kelarium, Jammer 10/50, Tachyon Detector, Mini Gun. |
| `SD`   | Space Demolition    | Mine-laying race: detonates own minefields, 2× safe minefield speed, minefields scan, decay 1%/yr instead of 4%/yr; unique Mini Mine Layer, Super Mine Layer, full Mine Dispenser/Heavy/Speed Trap series, Energy Dampener. |
| `PP`   | Packet Physics      | Two starting planets in non-tiny galaxies; cheaper, smaller mineral packets; packets scan with built-in penetrating scanner; unique Mass Driver 5/6/8/9/11/12/13; Energy Dampener; packets have terraforming chance. |
| `IT`   | Interstellar Traveler | Two starting planets with 100/250 stargates in non-tiny galaxies; 25% stargate discount; can gate cargo (mass ignored); reduced gate-loss probability; mass drivers half-effective when catching; unique Anti-Matter Generator. |
| `AR`   | Alternate Reality   | Lives in starbases, never on planet surfaces; no mines, factories, or planetary installations; population grows via starbase capacity; resources scale with energy tech; 3% colonist death/year in flight; 20% starbase discount (non-cumulative with ISB); unique Death Star, Orbital Construction Module. |
| `JOAT` | Jack of All Trades  | Population cap +20%; all six research fields start at tech level 3 unconditionally; built-in scanner on Scout/Frigate/Destroyer hulls (penetrating range `10 × electronics_level` ly, normal range `20 × electronics_level` ly — see "PRT-Driven Engine Coefficients"); the `Costs 75% Extra` accelerator promotes those fields to tech 4 (instead of tech 3 for other races); starting fleet: 2 scouts, 1 colony ship, 1 medium freighter (Privateer if Construction ≥ 4), 1 mini miner, 1 destroyer; no significant disadvantage. |

The exhaustive per-PRT mechanic specification (formulas, exact unique components, combat hooks) lives in the relevant cross-PRDs:

- Hulls/components: PRD 19 and PRD 20 catalogue entries gain `prt_required` lists; this PRD defines the field, those PRDs populate it.
- Combat hooks (movement, weapon discount, scan/cloak interactions): PRDs 80–82.
- Mine layout / scanning / detonation: future Minefields PRD (backlog).
- Stargates: future Stargates PRD (backlog).
- Mass packets: future Mass Drivers PRD (backlog).
- Terraforming: future Terraforming PRD (backlog).

This PRD owns the **flag** and the **schema**; downstream PRDs own the **mechanic**.

### PRT-Driven Engine Coefficients

A small number of PRT effects are simple enough to be encoded directly here, because they are read by engine steps that already exist:

| PRT     | Coefficient                                                                                                  | Read by              |
|---------|--------------------------------------------------------------------------------------------------------------|----------------------|
| `HE`    | `growth_multiplier = 2.0` applied to race `max_growth_rate` for population growth.                            | PRD 14 step          |
| `HE`    | `population_cap_factor = 0.5` applied to base max population.                                                 | PRD 14 step          |
| `JOAT`  | `population_cap_factor = 1.2`.                                                                                | PRD 14 step          |
| `AR`    | `population_cap_factor = 0` (planets do not host colonists; cap comes from starbase hull size — future PRD).  | PRD 14 step          |
| `AR`    | `disable_planetary_installations = true` (no mines, factories, planetary scanners, defenses).                | PRD 12, PRD 13 steps |
| `AR`    | Resource formula override: `annual_resources = floor(planet_value * sqrt(population * energy_level / 10))`.   | PRD 12 step          |
| `JOAT`  | `start_at_tech_offset = +1` for the `start_at_tech_3` accelerator (i.e. tech 4 instead of tech 3).            | PRD 22 race-creation |
| `JOAT`  | `joat_base_tech_level = 3` — all six research fields are initialised to tech 3 at turn-0 resolution, independently of the `start_at_tech_3` accelerator and independently of cost profile. | PRD 22 turn-0 step 8 |
| `JOAT`  | Built-in scanner on Scout, Frigate, and Destroyer hulls. Penetrating range = `10 × electronics_level` ly; normal (non-penetrating) range = `20 × electronics_level` ly. Active whether or not an explicit scanner component is fitted. Works even for races with `NAS` selected (per LRT table). | PRD 18/19 hull catalogue |

All other PRT effects are implemented in their owning PRDs and are referenced but not duplicated here.

---

## Lesser Racial Traits (LRTs)

Each race has an independent boolean flag for each of the 14 LRTs. LRTs may be combined freely; the UI surfaces incompatible combinations as warnings only (e.g. ARM + OBRM is legal but pointless).

| ID    | Name                       | Brief effect                                                                                                                                                     |
|-------|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `IFE` | Improved Fuel Efficiency   | Fuel consumption ×0.85; unlocks Fuel Mizer (and Galaxy Scoop unless `NRSE`); +1 starting Propulsion level.                                                       |
| `TT`  | Total Terraforming         | Unlocks ±3 / ±5 / ±10 / ±15 / ±20 / ±25 / ±30 terraforming at biotech 0 / 6 / 9 / 13 / 17 / 22 / 25; terraforming costs −30%.                                    |
| `ARM` | Advanced Remote Mining     | Unlocks Midget Miner / Miner / Ultra-Miner hulls and Robo-Midget / Robo-Ultra-Miner robots; starting fleet gains two Midget Miners.                              |
| `ISB` | Improved Starbases         | Unlocks Space Dock and Ultra Station hulls; all starbases auto-cloak 20%; starbase build cost −20% (does not stack with the AR PRT discount).                    |
| `GR`  | Generalized Research       | 50% of research goes to current field, 15% to each of the other five.                                                                                            |
| `UR`  | Ultimate Recycling         | Scrapping at a starbase recovers 90% minerals + 70% resources; at a planet 45% / 35%. Planet-side recovery uses the formula `recovered = (P × E)/(P + E)` (production × extra). |
| `MA`  | Mineral Alchemy            | Resource→mineral conversion is 4× more efficient (25 res = 1 kT each, instead of 100 res).                                                                       |
| `NRSE`| No Ramscoop Engines        | All ramscoop engines forbidden except Fuel Mizer (if IFE) and Enigma Pulsar (Mystery Trader); unlocks Interspace-10.                                             |
| `CE`  | Cheap Engines              | Engines cost ×0.5; warp >6 has 10% chance of failure to engage; +1 starting Propulsion level.                                                                    |
| `OBRM`| Only Basic Remote Mining   | Mining-ship hulls limited to Mini-Miner; mining robots limited to Robo-Mini-Miner; planet population cap +10% (additive with HE/JOAT modifiers).                 |
| `NAS` | No Advanced Scanners       | All penetrating scanners forbidden (except Chameleon/Robber Baron/JOAT-built-in/MT scanners); normal scanner ranges ×2.                                          |
| `LSP` | Low Starting Population    | Starting homeworld population is 70% of normal (17,500 instead of 25,000 with default JOAT homeworld setup).                                                     |
| `BET` | Bleeding Edge Technology   | New tech costs ×2 until all prerequisites are exceeded by 1 level; miniaturisation profile becomes 5%/level capped at 80% (instead of 4%/75%).                   |
| `RS`  | Regenerating Shields       | Shields ×1.4 strength and regenerate 10% per round; armour rated strength ×0.5.                                                                                  |

As with PRTs, the formulas owned by other PRDs are mentioned only briefly here. Each downstream PRD reads `race.lrts.contains(<id>)` rather than re-implementing detection.

---

## Habitability

A race defines a habitable range per environmental factor. PRD 14 already exposes the field shape; this PRD makes them per-race.

For each of `gravity`, `temperature`, `radiation`:

| Field        | Type                | Description                                                                          |
|--------------|---------------------|--------------------------------------------------------------------------------------|
| `immune`     | bool                | `true` ⇒ race ignores this factor; every value yields full per-factor +33 contribution.|
| `range`      | `[low, high]` ints  | `0..100` internal units. Ignored when `immune == true`.                              |
| `ideal`      | derived             | `floor((low + high) / 2)`. Used for homeworld ideal-environment override.            |

Constraints:

- `0 <= low <= high <= 100` when not immune.
- When `immune == true`, the per-factor habitability contribution is always `+33.333` (matching the manual: immunity treats every value as ideal, distinct from a max-width range whose endpoints still score 0).

The range width and offset both affect the points budget (see "Advantage Points").

### Maximum Growth Rate

A race carries `max_growth_rate: int` in the integer percent range `[1, 20]` — the maximum colonist growth per year on a 100%-habitable planet at low population. PRD 14 reads this value (currently hardcoded `15`) and applies the standard logistic curve.

The HE PRT applies a ×2 multiplier inside PRD 14's `population_growth` step (see "PRT-Driven Engine Coefficients"). The race's stored `max_growth_rate` is the unscaled value; HE displays the doubled effective rate in UI but stores the raw setting.

---

## Economy Settings

A race has eight tunable economy parameters plus one boolean. PRD 12 currently hardcodes JOAT defaults at the top of `economy.py` — those constants are removed and read from the player's race instead.

| Parameter                        | Range                  | Default (JOAT) | Description                                                                              |
|----------------------------------|------------------------|----------------|------------------------------------------------------------------------------------------|
| `colonists_per_resource`         | `700..2500`            | `1000`         | `N` colonists generate 1 resource per turn. Lower = more resource per population.        |
| `factory_output_per_10`          | `5..15`                | `10`           | 10 factories produce `N` resources per turn.                                             |
| `factory_cost_resources`         | `5..25`                | `10`           | Resources to build one factory.                                                          |
| `factories_per_10k_colonists`    | `5..25`                | `10`           | Operating cap: factories ≤ `floor(pop/10000) × N`.                                       |
| `factories_save_germanium`       | bool                   | `false`        | When `true`, factory germanium cost drops from 4 kT to 3 kT (the "g-box").              |
| `mine_output_per_10`             | `5..25`                | `10`           | 10 mines produce up to `N` kT of each mineral per turn at concentration 100.             |
| `mine_cost_resources`            | `2..15`                | `5`            | Resources to build one mine.                                                             |
| `mines_per_10k_colonists`        | `5..25`                | `10`           | Operating cap: mines ≤ `floor(pop/10000) × N`.                                           |

### AR economy

If the race's PRT is `AR`, all eight settings above are ignored and the planet contributes:

```
annual_resources = floor(planet_value * sqrt(population * energy_level / 10))
```

with the divisor `10` being a single tunable parameter `ar_resource_divisor: int`, range `5..25`, default `10`. Mining is performed by population directly: each 100 colonists in orbit acts as one mine equivalent at the 10 kT / 10-mines rate. AR races cannot toggle planetary settings (mines, factories, defenses, planetary scanners); these UI controls are disabled.

### Population cap modifiers

Final population cap on a habitable planet:

```
base_max_population = 1_000_000
cap = base_max_population * effective_hab_pct / 100
cap *= population_cap_factor                       # PRT: HE 0.5, JOAT 1.2, AR 0, others 1.0
cap *= 1.10 if race.lrts.contains("OBRM") else 1.0  # additive intent: stacks multiplicatively above
```

Existing PRD 14 logic stays; the only new step is multiplying by these factors.

### Mineral output

PRD 12's `mine_minerals` formula becomes:

```
minerals_mined[type] = floor(mines_operated * (mine_output_per_10 / 10) * concentration[type] / 100)
```

The current code uses a fixed `MINE_RATE = 1.0`; that constant becomes `race.mine_output_per_10 / 10`. JOAT default of `mine_output_per_10 = 10` reproduces today's behaviour exactly.

---

## Research Cost Profile

PRD 21 reserves a per-field cost multiplier for race traits. This PRD slots in three discrete options per field:

| Profile        | Multiplier on `cost(L, total_levels)` |
|----------------|----------------------------------------|
| `cheap`        | 0.5                                    |
| `standard`     | 1.0                                    |
| `expensive`    | 1.75                                   |

A race assigns one of `{cheap, standard, expensive}` to each of the six fields independently. Default for all fields is `standard`.

A race may also opt in to the `start_at_tech_3` accelerator (`bool`, default `false`):

- When `true`, every field marked `expensive` starts the game at tech level 3 instead of 0 (or 4 if the PRT is `JOAT`).
- A field that already starts above the accelerated level (e.g. via PRT starting bonuses) is unchanged.
- The accelerator costs a fixed advantage-point fee regardless of how many fields it covers.

When the GR LRT is selected, the PRD 21 research-resolution loop additionally distributes 15% of incoming resources to each of the five non-current fields (rounded up). Total spend per turn is therefore 50% + 5×15% = 125% of the player's research budget — GR is a net research bonus, not a redistribution. The `cheap`/`expensive` multipliers apply per-field as the resources arrive. (The original manual erroneously prints "115%"; the autohost guide and elite-games references both confirm 125%.)

When the BET LRT is selected, PRD 21's miniaturisation formula is replaced for that race: `discount = min(excess, 16) * 0.05`, capped at `0.80` (instead of `min(excess, 19) * 0.04` capped at `0.75`). New tech costs ×2 until the player exceeds **all** prerequisites of the item by ≥1 level — this is checked at the build-time miniaturisation evaluation.

---

## Leftover Advantage Bonuses

Any unspent advantage points (up to 50) at the end of race creation may be invested in a single starting bonus. The choice is part of the race record and applied during turn 0 generation.

| Bonus              | Effect                                                                                         |
|--------------------|------------------------------------------------------------------------------------------------|
| `surface_minerals` | +10 kT of the homeworld's lowest-concentration mineral per leftover point.                     |
| `mines`            | +1 starting mine per 2 leftover points (odd points are wasted).                                |
| `factories`        | +1 starting factory per 5 leftover points (the remainder is wasted; <5 points yields nothing). |
| `defenses`         | +1 starting defense installation per 10 leftover points (defense system is future PRD).         |
| `concentrations`   | +1% concentration on the homeworld's lowest-concentration mineral per 3 leftover points. Capped at 200. Note: the homeworld floor of 30 means concentrations starting below 30 see no practical mining benefit until raised above 30 — see PRD 12. |

Notes:

- AR races may select only `surface_minerals` or `concentrations`; selecting `mines`, `factories`, or `defenses` is a validation error (matches the manual: those bonuses are no-ops for AR).
- A race that goes into MVP without spent leftovers stores `bonus: null`. The leftover-points cap is exactly 50 — points beyond 50 are simply not spent and yield no bonus.
- "Lowest-concentration mineral" ties are broken by ascending mineral key order (`ironium`, then `boranium`, then `germanium`) to keep turn 0 deterministic.

---

## Advantage Points

A race must net ≥ 0 advantage points before it can be saved. The server enforces this; the client previews live as the user edits.

The total cost of a race is:

```
total_cost = identity_cost            # always 0
           + prt_cost                  # per-PRT integer
           + sum(lrt_cost)             # per-LRT integer
           + hab_cost                  # function of immunity flags + range geometry
           + growth_cost               # function of max_growth_rate
           + economy_cost              # sum across the eight economy parameters + factories_save_germanium
           + research_cost             # sum across the six fields + start_at_tech_3 accelerator fee
points_budget = 1650                   # the original game's starting budget
points_left   = points_budget - total_cost - leftover_bonus_cost
```

`points_left` must be ≥ 0 at save time. If `points_left ≤ 50` and the race has selected a leftover bonus, those points fund the bonus; points above 50 are wasted.

### Cost tables

The original Stars! cost values are not published in any reference we have verbatim; they are reverse-engineered by the AutoHost community. We follow PRD 21's pattern: define the **structure** here as authoritative, and ship a **balance constants table** as a single Python module that we iterate on if play-testing surfaces issues.

The structure is:

- `prt_cost: dict[PRT, int]` — fixed integer cost per PRT.
- `lrt_cost: dict[LRT, int]` — fixed integer cost per LRT (often **negative**, meaning the LRT pays the player back).
- `economy_cost(parameter, value) -> int` — a piecewise-linear function with documented turning points (see "Breakpoint anchors" below).
- `hab_cost(factor, immune, range)` — built from a documented base immunity cost (~75 per immune factor) and a width-and-offset table; moving the band more than 15 clicks off-centre yields back diminishing returns.
- `growth_cost(max_growth_rate)` — monotone increasing in growth rate. Notable breakpoint: 19→20% costs nearly twice as much as 18→19%.
- `research_cost(field, profile)` — `expensive ⇒ −150`, `standard ⇒ 0`, `cheap ⇒ +175` per field (the literal numbers anchor the canonical race-points table; tune in the constants module).
- `accelerator_cost = 60` for `start_at_tech_3` (flat regardless of how many fields are marked expensive).

#### Breakpoint anchors

These come from community-verified Stars! breakpoints and are the anchors the constants module must hit when calibrated. They are documented here so the PRD survives the constants module being retuned.

| Setting / move                                            | Marginal cost (pts)         |
|-----------------------------------------------------------|-----------------------------|
| Growth rate 18→19%                                        | ~50–70                      |
| Growth rate 19→20%                                        | ~100–150 (cliff at 20%)     |
| `colonists_per_resource` 1000→900                          | ~200 (cliff below 1000)     |
| `colonists_per_resource` 1000→1100                          | gain ~40                    |
| `factory_output_per_10` 10→11                              | ~43                         |
| `factory_output_per_10` 11→12                              | ~40                         |
| `factory_output_per_10` 12→13                              | ~62 (cliff at 12)           |
| `factory_cost_resources` 9→8                                | ~60 (cliff at 9)            |
| `mine_cost_resources` 4→3                                   | ~22                         |
| `mine_cost_resources` 3→2                                   | ~134 (cliff at 3)           |
| `factories_save_germanium` (toggle)                         | ~58                         |
| `start_at_tech_3` accelerator (flat)                        | 60                          |

The exact numbers live in `backend/openstars/engine/race/costs.py` so they can evolve without a PRD bump. PRD 22 owns the **shape**; the constants module owns the **balance dial**.

### Validation

Race selection is submitted as a turn-0 command through the normal `POST /api/v1/games/{game_id}/commands` endpoint. The command has `type: "select_race"` and accepts either a `predefined_id` (e.g. `humanoid`) or a full custom race record (`race`). The command shape leaves room for a future `account_race_id` field that will reference an account-level race library entry (see "Deferred follow-ups") without breaking the MVP shape; that input is purely additive.

On submission the server:

1. Validates each individual setting against its declared range / enum.
2. Computes `total_cost` and `points_left` using the constants module.
3. Rejects with `RACE_OVERSPENT` if `points_left < 0`.
4. Rejects with `RACE_INVALID_BONUS` if the leftover bonus is incompatible with the PRT (e.g. `mines` for AR) or if `bonus_amount > points_left`.
5. Records the selection on the player's turn-0 command set. The race is **not** yet copied onto `Player.race` — that happens at turn-0 resolution.

The same validation re-runs at turn-0 resolution against the *current* cost constants. A previously-saved selection that no longer validates (because the constants module has been retuned in the meantime) blocks resolution with `RACE_REVALIDATION_FAILED`; the affected player must amend their selection before the host can resolve.

A successful command submission returns through the normal command-submission response. The currently saved race selection can be read with `GET /api/v1/games/{game_id}/race`, which returns the canonical race record plus the recomputed `points_left`; after turn 0 resolves, the same endpoint reads the immutable `Player.race` snapshot. Live-preview during editing uses a separate dry-run endpoint, `POST /api/v1/race/preview`, that accepts a race and returns the same costs without saving or recording a turn-0 command.

---

## Schema Changes

### Global state — `Player`

`Player` (PRD 05) gains a single field:

| Field   | Type            | Description                                                                                                                                                              |
|---------|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `race`  | object \| null  | The full race record described below. `null` from game-start generation through the turn-0 command phase; populated when turn-0 resolution snapshots the player's selection. |

The in-flight turn-0 race selection lives on the player's turn-0 command set, not on `Player.race`. Snapshotting at resolution preserves immutability for the life of the game even if a future account-level race library lets the source race change between games.

### `Race` record

The race record has the following nested shape:

- `name: string`
- `plural_name: string`
- `emblem: int` (`0..31`)
- `prt: enum` (one of the 10 IDs above)
- `lrts: set<enum>` (subset of the 14 LRT IDs)
- `habitability: object`
  - `gravity: { immune: bool, range: [int, int] }`
  - `temperature: { immune: bool, range: [int, int] }`
  - `radiation: { immune: bool, range: [int, int] }`
- `max_growth_rate: int` (`1..20`)
- `economy: object`
  - `colonists_per_resource: int`
  - `factory_output_per_10: int`
  - `factory_cost_resources: int`
  - `factories_per_10k_colonists: int`
  - `factories_save_germanium: bool`
  - `mine_output_per_10: int`
  - `mine_cost_resources: int`
  - `mines_per_10k_colonists: int`
  - `ar_resource_divisor: int` (only meaningful when `prt == "AR"`)
- `research: object`
  - `field_profile: { energy: enum, weapons: enum, propulsion: enum, construction: enum, electronics: enum, biotechnology: enum }` where the value is one of `cheap | standard | expensive`
  - `start_at_tech_3: bool`
- `leftover_bonus: object | null`
  - `kind: enum` (`surface_minerals | mines | factories | defenses | concentrations`)
  - `points: int` (`1..50`)

Implementation note: Python enum member names should be descriptive (`JACK_OF_ALL_TRADES`,
`IMPROVED_FUEL_EFFICIENCY`, etc.), while the API and persisted JSON use the compact Stars!
IDs above (`"JOAT"`, `"IFE"`, etc.).

### Player state

`PlayerState` (PRD 03) gains the viewer's own race as `race: Race | null`. During the turn-0 command phase the value is `null`, and the rest of the player state is deliberately sparse: planets are visible only as name/coordinate records, fleets and designs are empty, events are empty, and research is `null`. After turn 0 resolves, the viewer's own race is fully visible.

Other players' race records are partially visible to a viewer:

- Always public: `name`, `plural_name`, `emblem`, `prt`.
- Hidden until detected: `lrts`, `habitability`, `max_growth_rate`, economy, research, leftover bonus.

Detection of LRTs follows the original game's heuristics (Mineral Alchemy is rarely useful to detect, IFE is detectable from observed fuel consumption, etc.). Fully spec'd intel mechanics are out of scope for MVP — for now, only the public fields are exposed to non-owners.

### Component / hull catalogue (PRD 19, PRD 20)

Each catalogue entry gains two optional list fields:

- `prt_required: list<PRT>` — empty list (default) means available to all PRTs. A non-empty list restricts the entry to races whose `race.prt` is in the list (e.g. `["HE"]` for the Mini-Colonizer hull).
- `prt_forbidden: list<PRT>` — entries forbidden to the listed PRTs (e.g. WM cannot build any hull tagged with `mine_layer == true`; this is structural, not catalogue-tagged).
- `lrt_required: list<LRT>` — analogous restriction tied to lesser traits (e.g. `["ARM"]` on Midget Miner).
- `lrt_forbidden: list<LRT>` — analogous (e.g. `["NRSE"]` on every ramscoop engine except Fuel Mizer).

These fields are read at design-creation time (PRD 18) and at build time (PRD 13). Validation rejects designs that include components or hulls the player's race cannot build.

### Events

New event codes (registered in PRD 51):

- `race.saved` — emitted in the player's per-turn event log at turn-0 resolution, when the chosen race is snapshotted onto `Player.race`. Carries the PRT and LRT set for client display.

No further race-related events are introduced; trait-driven events (e.g. `combat.shields_regenerated`) belong to their owning PRDs.

---

## Race Creation Flow

### When the race is chosen

A race is chosen during **turn 0**, the dedicated race-selection phase. The host starts the game; the galaxy is generated at game-start; turn 0 opens with no homeworlds yet materialised. Each player owes the server one decision before turn 0 can resolve: *which race am I playing?*

Turn 0 is structurally a normal command/resolution turn with these restrictions:

- The only legal submitted command at `POST /api/v1/games/{game_id}/commands` is `{"type": "select_race", ...}`. Any other order submitted during turn 0 is rejected with `COMMAND_TURN_ZERO_RACE_ONLY`.
- There is no turn-0 timer in MVP; the host triggers resolution once every player has submitted a selection. A turn-0 resolve attempted with any player still missing a selection fails with `TURN_ZERO_INCOMPLETE`.
- Players may freely revise their selection until resolution; the most recent successful submission wins.

The flow:

1. Host creates and starts the game; the galaxy is generated; turn 0 opens.
2. Each player submits a race selection command — either a predefined preset (`predefined_id`) or a full custom race record. The server validates the submission against the current cost constants (see "Validation"), then stores it on the player's turn-0 command set.
3. `POST /api/v1/race/preview` is available throughout for live cost feedback during custom-race editing.
4. Once every player has a saved selection, the host triggers turn-0 resolution. Each player's selection is **snapshotted** onto `Player.race`, homeworlds materialise, and the game begins in earnest. The race is immutable from this point onward.

The command payload is shaped to accept a future `account_race_id` referring to a saved race in an account-level library (see "Deferred follow-ups"); adding that input is purely additive and does not change MVP behaviour.

### Predefined races

Seven player-selectable presets are available out of the box, mirroring the original game:

| ID            | PRT  | LRTs                          | Notes                                              |
|---------------|------|-------------------------------|----------------------------------------------------|
| `humanoid`    | JOAT | —                             | 15% growth, 1-in-2 worlds, all standard tech.      |
| `insectoid`   | WM   | ISB, CE, RS                   | 10% growth, 1-in-3 worlds, biotech expensive.      |
| `rabbitoid`   | IT   | IFE, TT, CE, NAS              | 20% growth, 1-in-9 worlds.                         |
| `nucleotid`   | SS   | ARM, ISB                      | 10% growth, all worlds; everything expensive.      |
| `silicanoid`  | HE   | IFE, UR, BET, OBRM            | 6% growth, immune to all hab factors.              |
| `antethereal` | SD   | ARM, MA, CE, NAS, NRSE        | 7% growth, 1-in-12 worlds.                         |

Five additional AI-only presets (Robotoids, Turindrones, Rototills, Automitrons, Cybertrons, Macinti) are out of MVP scope; they will be added when an AI player exists.

### Predefined races are presets, not locks

Selecting a preset is equivalent to copying its full race record into the player's turn-0 selection. The player may then edit any field and resubmit; the preset link is broken on the first edit. This matches the original game's "select then customise" flow.

---

## Cross-PRD Updates

This PRD modifies the following existing PRDs. Each is updated in place to remove "hardcoded JOAT defaults" prose and replace it with "read from `player.race`" prose.

| PRD                              | Update                                                                                                            |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------|
| PRD 05 — Global State            | `Player` gains `race: Race`. Migration path documented.                                                          |
| PRD 12 — Economy & Resources     | `colonists_per_resource`, `factory_*`, `mine_*` constants moved to `race.economy`. AR PRT handled as a branch.    |
| PRD 13 — Production              | Factory and mine costs read from `race.economy`. Defense build queue (when added) consults `race.lrts`/`race.prt`.|
| PRD 14 — Population & Habitability | Habitability range, growth rate, population cap factor read from `race`. HE growth doubling applied at this step. |
| PRD 16 — Colonisation            | Initial colonist count computed against `race.lrts` (LSP halves to 17,500 with a 30% reduction on starting pop).   |
| PRD 17 — Starbases               | ISB unlocks Space Dock / Ultra Station; AR unlocks Death Star. 20% discount applied where ISB or AR is set.       |
| PRD 18 — Ship Design             | Design creation rejects hulls/components blocked by the player's PRT/LRT restrictions.                            |
| PRD 19 — Hull Slot Definitions   | Hull entries gain `prt_required` / `prt_forbidden` / `lrt_required` / `lrt_forbidden`.                            |
| PRD 20 — Components Catalogue    | Same set of optional fields per component entry.                                                                  |
| PRD 21 — Research & Technology   | Per-field cost multiplier slot filled by `race.research.field_profile`. BET miniaturisation, GR distribution.     |

Existing tests that assert against the hardcoded JOAT constants continue to pass because the JOAT defaults match exactly. The change is structural: the engine reads the same values from a new place.

---

## Turn 0 Generation

Turn 0 splits across two distinct phases: **game-start generation** (runs automatically when the host starts the game) and **turn-0 resolution** (runs after every player has submitted a race selection). PRD 05 §"Turn 0 Generation" is amended in line with the split.

### Game-start generation

Runs once when the host starts the game:

1. Generate the galaxy per PRD 11 — stars, planets, environment values, mineral concentrations.
2. Create an unowned `T=0` planet state for every generated planet. No planet is assigned as a homeworld, no owner is set, and no player-specific visibility is granted.
3. Open turn 0. `Player.race` is `null` for every player, `PlayerState.race` is `null`, and the player-visible state is the sparse command-phase state described above.

No homeworld assignment, starting fleet, or starting tech setup happens in this phase — all of it is race-dependent and waits for resolution.

### Turn-0 resolution

Runs once every player has submitted a turn-0 race selection. Each player's selection is re-validated against the current cost constants (see "Validation") before any state mutation; if any player's selection no longer validates, resolution is blocked.

1. Compute homeworld assignments using the deterministic game-seed algorithm and assign one homeworld per player.
2. For each player, snapshot the selected race onto `Player.race`. Resolution is blocked with `TURN_ZERO_INCOMPLETE` if a player is missing a selection.
3. Set the homeworld's environment values to the racial ideal for each non-immune factor; for immune factors, leave the value generated at game-start in place.
4. Set the homeworld's starting population:
   - `25_000` baseline
   - `× 0.7` if `race.lrts.contains("LSP")` ⇒ `17_500`
5. Apply leftover bonuses (if any):
   - `surface_minerals` ⇒ add `points × 10` kT to the rarest mineral.
   - `concentrations` ⇒ add `floor(points / 3)` to the rarest mineral concentration (capped at 200, then re-applies the homeworld floor of 30).
   - `mines` / `factories` / `defenses` ⇒ add the homeworld's installed count.
6. Apply PRT-specific starting fleets and tech levels (referenced from PRT table — actual fleet composition lives in PRD 18 design registry seeding logic).
7. PP and IT in non-tiny galaxies: assign a second homeworld and seed it with the appropriate starbase per PRT. The second world materialises as part of this same resolution.
8. Apply per-field starting tech levels in two passes:
   - **Pass 1 (PRT base level):** If `race.prt == JOAT`, initialise all six fields to level 3.
   - **Pass 2 (accelerator):** If `race.research.start_at_tech_3 == true`, raise every field whose profile is `expensive` to level 3 (or 4 for JOAT). A field already at or above the target is unchanged.
9. Emit `race.saved` in each player's per-turn event log.

Determinism: all random selections during turn-0 resolution use the existing seeded RNG (PRD 04). The order of operations above is the canonical sequence; a regression test in `backend/tests/engine/test_turn_zero_race.py` (TBD) freezes a known seed and asserts the resulting state.

---

## Phased Implementation

The PRD is large; we ship in five phases. Each phase ends with a runnable, tested game.

### Phase A — MVP race economy & habitability (the backlog item)

Ship the schema, JOAT-only PRT, no LRTs, full economy parameters, full habitability ranges, points budget validation. Predefined-race endpoint returns only Humanoid (JOAT). No leftover bonuses yet.

Turn-0 plumbing: the dedicated race-selection phase, the `COMMAND_TURN_ZERO_RACE_ONLY` and `TURN_ZERO_INCOMPLETE` enforcement, and the split between game-start generation (galaxy only) and turn-0 resolution (homeworld materialisation). Frontend surfaces a minimal preset picker plus a basic custom-race form on the turn-0 screen; the polished six-step wizard ships in Phase E.

Cross-PRD updates: PRD 05, 12, 14 only.

### Phase B — Habitability & growth differentiation, leftover bonuses

Players can set non-JOAT habitability, growth, and leftover bonuses. AR-specific economy still gated.

### Phase C — Primary racial traits

Add the remaining nine PRTs as data: enum, point cost, engine coefficients, hull/component catalogue tags. Combat-side effects gated until combat ships.

### Phase D — Lesser racial traits

Add the 14 LRT flags, GR/BET/MA/UR economy effects, NAS/IFE/CE/NRSE engine effects, ISB starbase effects.

### Phase E — Custom Race wizard UI + remaining presets

Polished turn-0 race-selection UI (full six-step custom-race wizard), ship the remaining player presets, and surface intel rules for trait detection. The same UI is the basis for the future account-level race library and lobby-side race design (see "Deferred follow-ups").

The PRD is the canonical view at the end of Phase E. Earlier phases simply leave later sections of the schema unread.

---

## Deferred follow-ups

- AI-only predefined races (Robotoids, Turindrones, etc.) — gated on AI players existing.
- Tech-trading and espionage payloads keyed off SS / GR.
- Mid-game race amendment (currently impossible; the data model supports it but no command is exposed).
- Account-level race library: save and reuse races across games. The turn-0 `select_race` command is shaped to accept an additional `account_race_id` input when this lands; no schema churn expected. A companion feature is lobby-side race design — drafting and validating races without an active turn-0 phase, then picking from the library at game start.
- Trait-detection intel mechanics (which LRTs/PRTs leak through observation, and at what scan level).
- Combat-side trait formulas that depend on the trait flag (WM weapon discount, RS shields, IS landing defence) — owned by combat PRDs, listed here for traceability.

---

## Reference Notes

Primary sources used for this PRD:

- `docs/references/manual/chapters/20-designing-custom-races.md` — wizard step structure, PRT/LRT lists, leftover bonus mechanics, miniaturisation profile distinctions (BET vs standard).
- `docs/references/manual/chapters/21-predefined-races.md` — strategy notes per predefined race; useful for sanity-checking preset construction.
- `docs/references/elite-games-ru-en/translated-markdown/race/race_creating.md` — wizard flow.
- `docs/references/elite-games-ru-en/translated-markdown/race/prt.md` and `race/<prt>.md` — per-PRT effects.
- `docs/references/elite-games-ru-en/translated-markdown/race/lrt.md` — LRT effects and detection heuristics.
- `docs/references/elite-games-ru-en/translated-markdown/race/hab.md` — habitability formula, max-population modifiers, growth-rate formula.
- `docs/references/elite-games-ru-en/translated-markdown/race/economic.md` — economy parameter ranges and turning points (informs `economy_cost` constants).
- `docs/references/elite-games-ru-en/translated-markdown/race/science.md` — research cost profile structure.
- `docs/references/elite-games-ru-en/translated-markdown/race/predefined_races.md` — exact composition of each preset (ported into the Predefined Races table).
- `docs/references/stars-auto-host/basic_race_design.html` — Stars! Strategy Guide, Chapter 2 "Basic Race Design" (mirror of `https://starsautohost.org/strategy/guidef/SSG02frm.htm`). Source of the breakpoint anchors and the corrected `start_at_tech_3` accelerator cost (60 points, not the earlier-cited 240); also resolves the manual's "115% / 125%" typo for GR.
