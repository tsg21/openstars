# PRD 81 — Classic Combat (10×10 Grid)

## Overview

This document defines the **classic** combat ruleset for OpenStars!: a faithful implementation of Stars!-style **tactical battle** on a **10×10 discrete grid**. It is intended to preserve the original’s **geometry, tempo, and tactical trade-offs** so that veterans recognise the same constraints (ranges, rounds, token limits, movement quirks).

**Parent contract:** **[PRD 80 — Combat Fundamentals](80-combat-fundamentals.md)** (server authority, determinism, logs, replay).

**Reference material:** [`docs/references/guts-of-the-battle-engine.md`](../references/guts-of-the-battle-engine.md) and the original Stars! documentation community sources linked from **[PRD 01 — Overview](01-overview.md)**.

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

### Speed and Movement Budget

- Each token has a **speed rating** that maps to **0–3 cells** of movement per round, plus **fractional-speed bonus squares** on a fixed schedule (¼, ½, ¾ bonuses as in the reference).
- Movement proceeds in **stages**: e.g. all 3-speed tokens move one step, then 2+, then 1+, per the reference article. **Implementation must document the exact phase order** in code comments and tests.
- **[PRD 82 — Altair](82-combat-altair.md)** deliberately **omits** the quarter-square **round table** and **multi-phase** grid stepping; classic retains them for parity.

### Movement Order

- Within each movement sub-step, **heavier tokens move first** when weight difference is large; when difference is small, **lighter token may move first** with a **probability** derived from the deterministic RNG stream (reference describes ~15% threshold behaviour).
- **Tie-breaks** when weight is equal: explicit sort key (e.g. token id, fleet id, design id) so behaviour is reproducible.

### Battle Orders (Movement AI)

The six movement tactics from Stars! drive where a token attempts to move each sub-step:

- Disengage  
- Disengage if Challenged  
- Minimise Damage to Self  
- Maximise Net Damage  
- Maximise Damage Ratio  
- Maximise Damage  

Exact behaviour must match the reference descriptions; edge cases (no valid move, multiple equidistant targets) need **deterministic tie-break rules** in implementation.

### Disengage and Leaving the Board

- **Disengage** requires accumulating enough **movement away** to **exit** the battle (reference: seven squares of movement to leave). Exact definition of “off board” and how partial progress carries between rounds must match Stars! and be tested.

### Starbase Movement

- Starbases **do not move** but receive **+1 weapon range** (and related rules such as sweeping where applicable).  

### Documented Classic Quirk (Parity)

- The reference notes a **starbase range bug**: movement AI may ignore the +1 range when deciding whether it is safe. **Default for `classic`:** replicate unless a game flag or later errata PRD explicitly switches to “fixed AI”.

---

## Combat (Shooting)

### Target Eligibility

- Battle plans specify **primary / secondary target types**, **legitimate races**, and **tactic**.
- Ships only fire on **legitimate** targets; **race escalation** (if any race attacks you, they become legitimate) per reference.

### Attractiveness

- Targets are ranked by **attractiveness** (cost / effective defence), varying by weapon type (beams, sappers, torpedoes, capital missiles). Shields/armour depletion updates attractiveness during the battle.
- Movement and firing both consult attractiveness; firing picks **in-range** targets according to plan precedence (primary, then secondary).

### Initiative and Salvo Order

- Weapons fire **by slot initiative** (highest first).
- **Initiative ties**: deterministic ordering established at battle start (reference: random priority that **persists for the whole battle**) using the battle’s derived RNG stream.

### Damage Application

- **Beams:** slot damage × ships × weapon dp, **range dissipation** along beam range, **capacitors / deflectors** modifiers per Stars! rules.
- **Missiles / torpedoes:** per-missile **hit roll** (accuracy, computers, jammers); misses do **partial shield damage**; hits split between shields and armour per rules.
- **Capital missiles:** **double damage to armour** when shields are down on target (reference).
- **Whole-ship kills** from a salvo use **armour per ship** and **token damage accounting**; armour granularity (e.g. 1/512 fractions) and **rounding direction** must match Stars! for classic parity.

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

## Testing Expectations

- Fixtures that assert **exact** token positions per round, **initiative tie** ordering, **rounding** on stacked tokens, and **256-token** trimming quotas.
- Regression tests for **starbase range** behaviour (both weapon range application and movement-AI parity quirk if enabled).

---

## What’s Out of Scope for This PRD

- Complete numeric tables for every component (handled with ship-combat stats PRDs).
- Battle plan command JSON schema (API PRD).
- Carrier fighter sub-battles, minefield combat overlap, and simultaneous multi-location wars (future PRDs).
