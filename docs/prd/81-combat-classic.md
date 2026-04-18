# PRD 81 — Classic Combat (10×10 Grid)

## Overview

This document defines the **classic** combat ruleset for OpenStars!: a faithful implementation of Stars!-style **tactical battle** on a **10×10 discrete grid**. It is intended to preserve the original’s **geometry, tempo, and tactical trade-offs** so that veterans recognise the same constraints (ranges, rounds, token limits, movement quirks).

**Parent contract:** **[PRD 80 — Combat Fundamentals](80-combat-fundamentals.md)** (server authority, determinism, logs, replay).

**Reference material:** [`docs/references/guts-of-the-battle-engine.md`](../references/guts-of-the-battle-engine.md), [`docs/references/elite-games-ru-en/`](../references/elite-games-ru-en/README.md) (translated Russian Stars! docs), and the original Stars! documentation community sources linked from **[PRD 01 — Overview](01-overview.md)**.

---

## Ruleset Identity

| Field | Value |
|-------|--------|
| Ruleset id | `classic` |
| Geometry | 10×10 cell grid |
| PRD | This document |

**Backend package:** `backend/openstars/combat/classic/` — classic engine code lives here alongside **`altair`** under the shared `combat/` parent ([PRD 82](82-combat-altair.md)).

---

## Goals

1. **Mechanical fidelity** — Same structural rules as Stars!: tokens, rounds, movement/shooting phases, initiative order, attractiveness-based targeting, battle orders, weapon-type differences (beams, torpedoes, capital missiles, sappers), starbase range bonus, salvage and tech-from-battle hooks (exact formulas in follow-on PRDs as economy/combat stats land).
2. **Deterministic outcomes** — All tie-breaks and random checks documented and testable (PRD 80 / PRD 04).
3. **Explicit parity targets** — Where the original has documented implementation quirks, this PRD states whether OpenStars **replicates** them for byte-level behavioural parity or **fixes** them with a changelog entry (default: replicate unless classified as a crash or security issue).

---

## Battlefield

### Grid

- The arena is a **10×10** array of **cells**.
- Coordinates are **integer pairs** `(x, y)` with bounds defined in implementation (e.g. `0..9` inclusive). The exact origin corner is an implementation choice but must be **fixed and documented**; tests use the documented convention.
- **Distance** between cells for range checks and movement limits uses the **same metric as Stars!** for battle squares. *Implementation note:* verify against original or authoritative community reverse-engineering; document as **orthogonal (4-way)**, **king (8-way / Chebyshev)**, or **Manhattan** once confirmed. PRD 82 (Altair) scales this metric when porting concepts; Altair itself uses Euclidean `isqrt` distance — see that PRD.

### Starting Positions

At battle start, all tokens of the same race begin in a **single cell** determined by a fixed layout that depends on the **number of participating races** and their **player order** within the game. Starting position diagrams are defined per race count (2, 3, 4, … up to the game's player limit). Which slot a race occupies is determined by sorting the participating races by their global player order — the first race in game order gets position 1, the second gets position 2, etc.

*Implementation note:* The exact cell coordinates for each race count must be extracted from the original Stars! behaviour or community reverse-engineering and documented as test fixtures. The elite-games reference confirms this is a deterministic mapping, not random.

### Tokens (Stacks)

- Each **token** is one ship **design** in one **fleet** (or starbase) at this location; token size = ship count of that design.
- Multiple tokens may **occupy the same cell**.
- **Maximum 256 tokens** per battle across all races, with **fair sharing** of slots per race when the cap is exceeded (see reference article). Deterministic **eviction order** when trimming must be specified in implementation (reference: highest fleet numbers trimmed first with per-race quotas).

### Round Structure

- Up to **16 rounds** per battle.
- Each round has **movement** then **shooting** (reference order).
- Battle ends when: **round limit**, **one side remains** with hostile intent, or **no mutual hostility** remains (exact termination predicates aligned with Stars!).

---

## Movement

### Combat Maneuvering Speed Formula

Each token's combat maneuvering speed is computed from its design and components. The formula (from the elite-games reference) is:

```text
speed = (ideal_engine_speed - 4) / 4
      - mass_kT / 70 / 4 / engine_count
      + 0.25 * maneuvering_jet_count
      + 0.50 * overthruster_count
```

Where:
- **`ideal_engine_speed`** is the engine's highest safe warp (the maximum warp where fuel usage ≤ 100%).
- **`mass_kT`** is the total mass of the ship design in kT.
- **`engine_count`** is the number of engines fitted.
- **War Monger (WM) racial trait** adds **+0.5** to the result.

The result is **capped at 2.5** and **rounded to the nearest 0.25**. The minimum speed for a ship is **0.5** (starbases have speed **0**).

*Implementation note:* For integer arithmetic (PRD 04), compute in **quarter-squares** — multiply all terms by 4 to get an integer `quarters_round` in the range `[2, 10]`, then use the round table below. The rounding and capping happen before entering the table.

### Speed and Movement Budget

- Each token has a **speed rating** in quarter-squares that maps to **0–3 cells** of movement per round, following a fixed **8-round repeating pattern** (the “round table”):

| Speed | Q | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | Rounds to leave |
|-------|---|----|----|----|----|----|----|----|----|-----------------|
| 0.50  | 2 | 1  | 0  | 1  | 0  | 1  | 0  | 1  | 0  | 13              |
| 0.75  | 3 | 1  | 1  | 0  | 1  | 1  | 1  | 0  | 1  | 9               |
| 1.00  | 4 | 1  | 1  | 1  | 1  | 1  | 1  | 1  | 1  | 7               |
| 1.25  | 5 | 2  | 1  | 1  | 1  | 2  | 1  | 1  | 1  | 5               |
| 1.50  | 6 | 2  | 1  | 2  | 1  | 2  | 1  | 2  | 1  | 5               |
| 1.75  | 7 | 2  | 2  | 1  | 2  | 2  | 2  | 1  | 2  | 4               |
| 2.00  | 8 | 2  | 2  | 2  | 2  | 2  | 2  | 2  | 2  | 4               |
| 2.25  | 9 | 3  | 2  | 2  | 2  | 3  | 2  | 2  | 2  | 3               |
| 2.50  |10 | 3  | 2  | 3  | 2  | 3  | 2  | 3  | 2  | 3               |

After 8 rounds, the pattern repeats (rounds 9–16 follow the same sequence as 1–8).

- **`Q`** = `quarters_round` (the integer quarter-square speed value).
- **Rounds to leave** = the number of rounds of disengage movement required to exit the battlefield. Disengage requires accumulating **7 cells** of qualifying movement — faster tokens leave sooner.

- Movement proceeds in **stages** each round: all tokens with 3 cells of movement this round move one step, then all with 2+, then all with 1+. **Implementation must document the exact phase order** in code comments and tests.
- **[PRD 82 — Altair](82-combat-altair.md)** deliberately **omits** the quarter-square **round table** and **multi-phase** grid stepping; classic retains them for parity.

### Movement Order

- Within each movement sub-step, **heavier tokens move first** when weight difference is large; when difference is small (within ~**15%** by mass), **lighter token may move first** with a **probability** derived from the deterministic RNG stream.
- **Tie-breaks** when weight is equal: explicit sort key (e.g. token id, fleet id, design id) so behaviour is reproducible.

### Battle Orders (Movement AI)

The six movement tactics from Stars! drive where a token attempts to move each sub-step. The tactic rule is re-evaluated **every time a token tries to move 1 cell**. The AI does not consider multi-cell lookahead, weapon initiative consequences, or possible enemy movements — it is purely greedy per step. If two cells are equally good, the choice is made by the deterministic RNG.

- **Disengage** — Move away from all enemies. If in enemy weapon range but unable to increase distance, maintain distance. If unable to maintain distance, move randomly. If out of enemy range, move randomly. Accumulate 7 cells of qualifying movement to leave the battlefield (see round table above for how many rounds this takes at each speed).
- **Disengage if Challenged** — *Source conflict:* The “Guts of the Battle Engine” community reference says this behaves like **Maximise Damage** until the token **takes damage**, then switches to Disengage. The elite-games reference says it uses **Maximise Damage Ratio** until **all targets are destroyed**, then switches to Disengage. **Implementation decision required** — pick one interpretation and document it as a test fixture. Default recommendation: follow the “takes damage” trigger from the guts reference (more commonly cited in the English-speaking community), using **Maximise Damage Ratio** as the pre-switch tactic.
- **Minimise Damage to Self** — If within enemy weapon range, move away. If out of range or unable to move away, try to get in range of the best target without moving closer to enemies.
- **Maximise Net Damage** — Move toward the most attractive target. If out of range with any weapon, close distance. If in range with all weapons, move to maximise `damage_dealt − damage_taken`. In practice: longer-range weapons → stay at max range; same range → random movement while staying in range; shorter range beams → close to zero range.
- **Maximise Damage Ratio** — As Maximise Net Damage, but considers only the **longest-range weapon** when deciding positioning.
- **Maximise Damage** — Move toward the most attractive target. Close until all weapons are in range. If using beam weapons, attempt to close to range 0 (for minimum dissipation). If using only missiles/torpedoes and in range, move randomly while staying in range.

**Unarmed ships** always receive the **Disengage** tactic regardless of their fleet's battle plan. They will attempt to leave the battlefield immediately.

### Disengage and Leaving the Board

- A disengaging token accumulates qualifying movement cells. After accumulating **7 cells**, the token **exits** the battle at the **end of the round** in which it reached 7 — it cannot be targeted or damaged after that point. See the “Rounds to leave” column in the speed table for how many rounds this takes at each speed.

### Starbase Movement

- Starbases **do not move** (speed = 0) but receive **+1 weapon range** (and related rules such as sweeping where applicable).

### Documented Classic Quirk (Parity)

- The reference notes a **starbase range bug**: movement AI may ignore the +1 range when deciding whether it is safe. **Default for `classic`:** replicate unless a game flag or later errata PRD explicitly switches to “fixed AI”.

---

## Combat (Shooting)

### Target Eligibility

- Battle plans specify **primary / secondary target types**, **legitimate races**, and **tactic**.
- Ships only fire on **legitimate** targets; **race escalation** (if any race attacks you, they become legitimate) per reference.
- If a token’s primary and secondary targets are all destroyed or absent, the token does not fire — it will not attack ship types not listed in its battle plan even if those ships are attacking it.

### Attractiveness

- Targets are ranked by **attractiveness** (cost / effective defence), varying by weapon type (beams, sappers, torpedoes, capital missiles). Shields/armour depletion updates attractiveness during the battle.
- **Cost** for attractiveness = `resources + boranium` of the ship design (ironium and germanium do not contribute).
- **Defence** varies by weapon type: shields + armour dp, modified by effective torpedo accuracy (after computers/jammers) for torpedoes and capital missiles, by double-damage-to-unshielded for capital missiles, and by deflector percentage for beams.
- Movement and firing both consult attractiveness; firing picks **in-range** targets according to plan precedence (primary, then secondary).

### Initiative and Salvo Order

- Each weapon slot’s **effective initiative** = hull base initiative + weapon initiative + sum of all computer initiative bonuses on the ship.
- **Initiative cap: 63.** If the computed initiative exceeds 63, it is clamped to 63.
- Weapons fire **by slot initiative** (highest first).
- **Initiative ties** are broken in order:
  1. **Smaller weapon range fires first** (elite-games reference).
  2. If range is also equal, **deterministic random priority** established at battle start (persists for the whole battle) using the battle’s derived RNG stream.
- Within a token, all weapons of the **same slot** fire **atomically** as a single salvo (see Salvo Atomicity below).

### Salvo Atomicity

The grouping of fire into salvos differs by weapon type and has mechanical consequences:

- **Beam weapons:** All weapons in a token that share the **same initiative and type** fire together as a single atomic salvo. If the salvo destroys a target, **remaining damage spills over** to the next most attractive target within range. Beams always damage shields first; only after the token’s entire shield pool is depleted does damage reach armour.
- **Missiles and torpedoes:** Each **weapon slot** fires as a separate salvo. Within each slot salvo, individual missiles/torpedoes are resolved **one by one** — each hit/miss is checked, damage applied, and ships potentially destroyed before the next projectile in the same salvo. This means **2+2 slots are less effective than 1 slot of 4** (each smaller salvo wastes overkill on individual ships and has a separate damage calculation).
- **Gatling weapons** (Mini Gun, Gatling Gun, Gatling Neutrino Cannon, Big Mutha Cannon): fire a single shot at **all enemy tokens within range**, not just the most attractive target. Each token in range receives one hit. This makes gatling weapons area-of-effect.
- **Sapper weapons** (Pulsed Sapper, Phased Sapper, Synchro Sapper): damage **shields only** — they cannot damage armour. They follow beam mechanics otherwise (range dissipation, capacitor bonuses).

### Damage Application

#### Beam Weapons

- **Base damage** = weapon dp × weapon count in slot × ship count in token.
- **Range dissipation:** damage decreases linearly with distance, up to **10% reduction** at maximum range. At range 0: full damage. At range `r` of a weapon with max range `R`: damage × `(1 − 0.10 × r / R)`. For **starbases**, the dissipation over the extended `R+1` range is slightly higher (**~11–12%** at max range rather than 10%), applied only over the bonus range cell.
- **Capacitor bonus:** Each Energy Capacitor adds **+10%** to beam damage; each Flux Capacitor adds **+20%**. Capacitor bonuses are **additive** with each other (e.g. two Energy Capacitors = +20%). **Maximum total multiplier: 250%** (2.5×) — the beam damage bonus is hard-capped regardless of how many capacitors are fitted.
- **Deflector reduction:** Each Beam Deflector on the **target** reduces incoming beam damage by **10%**. Deflectors stack **multiplicatively**: 2 deflectors → damage × `(1 − 0.10)²` = 81% of nominal; 3 deflectors → 72.9%, etc.
- **Spillover:** If a beam salvo destroys its target (shields and all ships in the token), remaining damage redirects to the next most attractive in-range target.

#### Missiles and Torpedoes

- Per-missile **hit chance** = weapon base accuracy + sum of computer accuracy bonuses on the firing ship − sum of jammer values on the target.
- **Hit:** damage = weapon dp. If shields remain, **half** goes to shields and **half** to armour. If shields are gone, **all** goes to armour.
- **Miss:** if the target has shields, **1/8** of weapon dp damages shields. If the target has **no shields**, a miss does **zero** damage.

#### Capital Missiles

- Same hit/miss rules as torpedoes.
- **Double armour damage:** when a capital missile hits a target whose shields are down, the armour damage is **doubled** (2× weapon dp to armour).

#### Whole-Ship Kills and Token Damage

- **Shields** are tracked as a **single pool** across the entire token (all ships share one shield total).
- **Armour** is tracked as a **per-ship fraction** within the token, stored in **1/512ths** of total armour (the armour "damage percentage" has ~0.2% granularity). All ships in a token share the same damage percentage.
- **Whole-ship kills** from a salvo: total armour damage from the salvo ÷ remaining armour per ship = number of complete ships destroyed (integer division). Remaining damage is distributed evenly among surviving ships as fractional armour damage.
- **Rounding direction** for the 1/512 armour granularity: rounds **up** (damage is never lost to rounding). This can be exploited with many small weapon slots each doing tiny damage — each still removes at least 1/512 of armour.

### Range and Line of Sight

- Range is measured in **grid cells** per weapon. Starbases: **+1 range** to all weapons.

---

## Post-Battle

- **Salvage** — Minerals at battle location from destroyed ships (reference: fraction of mineral cost); decay or planetary deposit rules in economy PRDs.
- **Tech gain** — Participants with survivors may gain tech from destroyed enemy tech; exact formulas in a future PRD (reference: “Guts of Tech Trading”).

---

## Relationship to OpenStars Ruleset

**[PRD 82 — Altair](82-combat-altair.md)** uses the **same** initiative, damage, attractiveness, and battle-order logic where possible; only **geometry** (positions, distances, movement budgets in arena units) differs, with **scaled constants** and Euclidean distance — see that PRD.

Classic is the **reference** for interpreting weapon stats and hull equipment expressed in “squares” in design data.

---

## Source Conflicts

The following points have conflicting descriptions across reference sources. Implementation should pick one interpretation, document it, and build test fixtures that lock in the chosen behaviour.

| Topic | Guts of the Battle Engine | Elite-games reference | Recommendation |
|-------|--------------------------|----------------------|----------------|
| Disengage if Challenged — pre-switch tactic | Maximise Damage | Maximise Damage Ratio | Use Maximise Damage Ratio (see Battle Orders above) |
| Disengage if Challenged — switch trigger | Token takes damage | All targets destroyed | Use "takes damage" trigger (more commonly cited) |
| Mole-skin Shield dp | Not specified | 20 dp (28 with RS) | Manual appendix B says 25 dp — verify against game binary if possible |

---

## Testing Expectations

- **Starting positions** — fixtures per race count confirming deterministic cell assignments.
- **Movement formula** — tests for the combat speed formula across a range of hull masses, engine types, and MJ/OT counts; verify cap at 2.5 and rounding to nearest 0.25.
- **Round table** — assert exact cells-moved per round for each speed level across a full 8-round cycle.
- **Initiative** — verify the cap at 63 with high-initiative weapon + computer stacking; verify tie-break order (range first, then RNG).
- **Salvo atomicity** — beam spillover to secondary targets; missile slot-by-slot vs grouped beam firing.
- **Armour granularity** — 1/512 rounding-up behaviour; verify that tiny-damage weapons still remove at least 1/512.
- **Deflector stacking** — verify multiplicative reduction (81% for 2, 72.9% for 3).
- **Capacitor cap** — verify damage multiplier does not exceed 250%.
- **Disengage timing** — verify rounds-to-leave matches the speed table for each speed level.
- **Unarmed tokens** — verify they always disengage regardless of fleet battle plan.
- Fixtures that assert **exact** token positions per round, **initiative tie** ordering, **rounding** on stacked tokens, and **256-token** trimming quotas.
- Regression tests for **starbase range** behaviour (both weapon range application and movement-AI parity quirk if enabled).
- Regression tests for **starbase beam dissipation** (~11-12% at extended range vs 10% for ships).

---

## What’s Out of Scope for This PRD

- Complete numeric tables for every component (see [`docs/references/manual/chapters/appendix-b-technology-tables.md`](../references/manual/chapters/appendix-b-technology-tables.md) for reference values; component catalogue in [`backend/openstars/data/components/`](../../backend/openstars/data/components/)).
- Battle plan command JSON schema (API PRD).
- Carrier fighter sub-battles, minefield combat overlap, and simultaneous multi-location wars (future PRDs).
- Tech-from-battle formulas (future PRD; reference: "Guts of Tech Trading").
- Exact starting position grid coordinates per race count (to be reverse-engineered and added as test data).
