# PRD 82 — OpenStars Combat (Scaled Integer Arena)

## Overview

This document defines the **openstars** combat ruleset: tactical combat on a **large integer coordinate** arena where **all spatial quantities are scaled** from the classic model so that **relative geometry is preserved** (see “Approach 1” in design discussions). Weapon ranges, movement budgets, disengage distances, and board extent are expressed in the **same integer units**; a single **scale factor** maps classic “squares” to OpenStars **arena units**.

**Parent contract:** **[PRD 80 — Combat Fundamentals](80-combat-fundamentals.md)**.

**Logical twin:** **[PRD 81 — Classic combat](81-combat-classic.md)** shares the same **non-spatial** rules where OpenStars does not explicitly diverge (attractiveness, initiative ordering within a **volley**, damage pipeline, battle orders, token model). OpenStars **replaces** classic’s single **movement+fire round** with **many short movement ticks** and **one shooting phase per volley**; see Time Structure below.

---

## Ruleset Identity

| Field | Value |
|-------|--------|
| Ruleset id | `openstars` |
| Geometry | Bounded integer coordinate arena |
| PRD | This document |

---

## Design Intent

1. **Open battle space** — Tokens have **integer positions** on a board large enough for finer manoeuvre and clearer replay animation than a 10×10 cell id.
2. **Scaled parity** — For a chosen scale `S`, one classic **square edge** corresponds to `S` arena units. A classic weapon range `R` squares becomes **`R × S` arena units** for **range radius** (see Distance). Movement **per classic-equivalent volley** scales the same way (see Movement).
3. **Same combat maths per volley** — When weapons **fire**, damage per salvo, shields, armour granularity, hit rolls, initiative order, and attractiveness use the **same algorithms** as classic unless noted here. Weapons do **not** fire every **tick**; they fire on **volley boundaries** so overall **damage over a battle** stays in line with classic (one full shooting pass per classic-equivalent round).
4. **Euclidean distance via `isqrt`** — OpenStars does **not** use Chebyshev or Manhattan grid distance. Range and movement geometry use the same **integer Euclidean** convention as fleet movement in **[PRD 10 — Fleet Movement](10-fleet-movement.md)** (`dist_sq = dx² + dy²`, `dist = isqrt(dist_sq)`). At a **large** `S`, the unresolved classic “one diagonal square” question matters far less than the width of the arena in internal units, so combat behaves like **smooth** tactical space rather than a 10×10 chessboard.
5. **Smooth time** — Classic has at most **16** rounds per battle; each round moves tokens (in grid phases) then **every weapon fires** (per slot, initiative order). OpenStars uses **`T` movement ticks per volley** (default **`T = 20`**) so paths are **many small steps**. **Thrusters and jets** remain in the **classic quarters formula** (so they still grant their **½ / ¼** square equivalents per volley); spreading **`budget_volley`** across **`T`** makes each **tick** a **small** nudge. **`Energy Dampener`** stays a **flat penalty** per volley (**see Movement**). No quarter-square **oscillation table**.
6. **No classic quarter-square round table** — OpenStars does **not** replicate the **8-round movement table** or phased grid stepping from PRD 81.

---

## Constants

### Scale Factor

- **`S`** — Positive integer, **ruleset constant**, stored with game/scenario configuration.
- **Default: `S = 1000`.** That yields a **`10 000 × 10 000`** arena (see below): enough internal resolution that positioning within a notional classic “cell” dominates edge cases, and ranges measured with **`isqrt`** behave smoothly rather than like a coarse grid.
- All players in a game use the same **`S`**.

### Arena Extent

- Classic spans **10** cells per axis. OpenStars arena spans **`10 × S` integer units** per axis (default), i.e. the same **relative** extent as classic but finer resolution.
- Coordinates are integers **`(x, y)`** with **`0 ≤ x < 10·S`** and **`0 ≤ y < 10·S`** (exact inclusive/exclusive bounds fixed in implementation and tests).

*Rationale:* Keeping the **10× classic span** avoids turning OpenStars into an unbounded kiting simulator while still allowing **`S` positions per classic “cell”** along each axis for movement and presentation.

### Ticks and volleys

| Symbol | Meaning | Default |
|--------|---------|---------|
| **`T`** | Movement **ticks** per **volley** (one classic-equivalent “round” for firing) | **`20`** |
| **`N_macro`** | Maximum **volleys** per battle (classic’s “16 rounds”) | **`16`** |

- **Tick index** `t = 0, 1, …` counts **movement opportunities**. After every **`T` ticks**, the engine runs a **shooting phase** (full weapon cycle as in classic), then continues with the next tick unless the battle has ended.
- **Maximum length:** **`N_macro × T` ticks** before the battle is forced to end if not already resolved (same role as classic’s 16-round cap). Example: **`16 × 20 = 320`** ticks.
- **Round-scoped effects** in classic (e.g. `Regenerating Shields` **10%** per round, target re-selection cadence) advance **once per volley** (every **`T` ticks**), **not** once per movement tick — unless this PRD is later amended.

*Rationale:* In Stars!, **each weapon can fire once per combat round**. OpenStars **decouples** **motion** (fine-grained) from **fire** (coarse-grained): firing stays **once per volley** so balance and maths stay comparable to classic; only **positioning** becomes smoother.

### Distance (`isqrt`)

OpenStars uses **integer Euclidean distance** in arena units, matching the engine’s existing helper (see **`isqrt`** in **[PRD 10 — Fleet Movement](10-fleet-movement.md)** and `openstars.engine.util.isqrt`):

```text
dx = x_a - x_b
dy = y_a - y_b
dist_sq = dx² + dy²
dist = isqrt(dist_sq)
```

- **`isqrt(n)`** is the largest integer `r` with `r² ≤ n` (deterministic, no floats).

**In range:** a weapon with classic range **`R`** squares is in range when:

```text
dist ≤ R × S + starbase_bonus
```

where **`starbase_bonus = S`** if the firer is a starbase with the classic `+1` range bonus, else **`0`**. Range `0` (“same square only”) is **`dist = 0`** (same integer coordinates — tokens may stack).

This deliberately **differs** from **[PRD 81](81-combat-classic.md)** grid metrics (Chebyshev / Manhattan / etc.). OpenStars targets **large `S`** so that tactical geometry is **approximately continuous**; classic grid parity is not a goal for this ruleset.

---

## Positions and Tokens

- Each **token** has an **integer position** `(x, y)` in arena coordinates.
- **Multiple tokens may share the same coordinates** (stacking in the same “point” of space), preserving the classic rule that many tokens can occupy one cell.
- **Token limit (256)** and **per-race fair sharing** behave as in classic; only position representation changes.

---

## Movement

### Budget per volley (classic stats, smooth ticks)

OpenStars does **not** copy classic’s quarter-square **oscillation table**. Hull, engines, weight, **`Overthruster`**, and **`Maneuvering Jet`** still matter through the **same Stars! combat movement formula** as classic (see **[PRD 81](81-combat-classic.md)** and the manual): those components already enter as **quarter-squares per classic round** (**`+½`** per thruster, **`+¼`** per jet, etc.). OpenStars treats **one volley** as **one classic round** for that formula, then spreads the result across **`T` ticks**, so each tick’s step is **small** even when the **volley** total matches classic.

1. **Quarters per volley** — Compute **`quarters_volley`** with the **full** classic formula (all components except effects handled below), capped at **10** quarter-squares (**2½** classic squares), same as Stars!.
2. **Convert to arena units:**

   ```text
   base_volley_units = (quarters_volley × S) // 4
   ```

3. **`Energy Dampener`** — If classic rules say the battle is dampened, subtract **`dampen_units`** arena units **per token per volley** (mirrors **−1** classic square per round). Default **`dampen_units = S`**. Not additive per extra dampener ship, same as classic.

4. **Volley movement budget**

   ```text
   budget_volley = max(0, base_volley_units − dampener_penalty)
   ```

   where **`dampener_penalty = dampen_units`** if the dampener applies to that token, else **`0`**.

If playtesting shows thruster/jet contributions should be **weaker or stronger** than classic’s embedded quarters, adjust via **ruleset data** (e.g. scale **`quarters_volley`** after the formula, or use a stripped base plus explicit bonuses) — but **do not** double-count the same component twice.

### Budget per tick (smooth stepping)

For each token, split **`budget_volley`** across the **`T` ticks** of the current volley **deterministically**:

```text
b = budget_volley // T
r = budget_volley % T
```

For tick **`k`** within the volley (`k = 0 … T−1`):

```text
budget_tick(k) = b + (1 if k < r else 0)
```

So the **sum** of **`budget_tick`** over one volley equals **`budget_volley`** exactly (no drift).

### Per tick: motion only

- **Order within a volley** — At **volley start** (before tick `k = 0`): perform classic **per-round** setup that applies **once per volley** — e.g. all tokens **choose / refresh primary targets** per battle plans (Stars! round step 1). Then run ticks **`k = 0 … T − 1`** (movement only). Then **shooting phase**. (Exact mirror of classic **choose → move → fire**, with **move** subdivided into **`T` steps.)
- **Each tick** — Every token **may move once** to any **integer** position in the arena with **`isqrt(dx² + dy²) ≤ budget_tick(k)`** for that tick.
- **No movement** on ticks that do not exist; **no** classic phased sub-steps within a tick.

### Movement AI and Order

- **Same battle orders** and **same high-level movement AI** as classic (tactics, attractiveness, targeting). **Primary target** choice follows classic **once per volley** (at volley start); within the volley, the AI picks a **destination each tick** within **`budget_tick(k)`** toward that target (or tactic equivalent) as positions update.
- **Movement order** — Each tick, tokens move in **weight order** with the same **±15%** jitter and deterministic tie-breaks as PRD 81.

### Volley boundary: shooting

- After **`T` ticks** have completed (movement only on each), run **one shooting phase**: same structure as classic — initiative, slot order, full salvos, spillover, etc. Weapons **do not** fire on intermediate ticks.
- Then increment the **volley index**; if **`volley_index ≥ N_macro`**, end the battle per classic termination rules; otherwise start the next volley at tick **`k = 0`** with a fresh **`budget_volley`** (recompute if battle effects ever change speed).

### Disengage and Board Edge

- Classic **“seven squares”** to leave becomes **`7 × S` arena units** of qualifying movement toward **exiting the bounded arena**, with exit predicates mirroring classic **off-board** semantics at scale.

### Starbases

- **Immobile**; **+1 classic square** weapon range becomes **`+S`** to the **`R × S`** radius threshold (see Distance).

---

## Shooting

- **Cadence** — All shooting happens at **volley boundaries** (after each block of **`T` ticks**), **not** every tick. One pass through weapons (per classic rules) ≈ one classic combat **round** for output purposes.
- **Range:** use **`dist`** and **`R × S + starbase_bonus`** as in Distance; do **not** use a separate “range units” accumulator unless needed for display.
- **Beam dissipation** — Prorate using **effective classic distance**: at least **`ceil(dist / S)`** or a finer mapping from **`dist`** to a dissipation index in **quarter-squares** if needed to match classic decay curves. Integer rounding rules must be **fixed and tested**; large **`S`** reduces sensitivity to off-by-one in **`dist / S`**.
- **Destroyed before firing** — As in classic, if a token is destroyed during a volley’s shooting phase before its slots fire, it does not fire later that volley.

---

## Replay and Presentation

- Logs record **tick index**, **volley index**, **integer positions**, and **scaled ranges** so the client can animate **smooth** motion between volleys without re-running AI.
- Optional display: overlay a **10×10 classic grid** for players who think in squares (`cellX = floor(x / S)`, etc.); optional **“fast-forward to next volley”** for viewers who only care about shots.

---

## Balance Notes

- OpenStars is **not** outcome-identical to classic: **Euclidean** range is a different shape than a Chebyshev or Manhattan “diamond/square” in grid space. **`S = 1000`** makes local geometry **smooth enough** that players optimise in continuous terms; it does **not** restore classic grid parity.
- **Micro-positioning** within the arena can differ from “cell-centred” tokens; large **`S`** limits how much one integer step changes relative range.
- **`T`** and **`dampen_units`** are primary levers if **motion feels too choppy or too fast** relative to **time between volleys**; **`quarters_volley`** from the classic formula should remain the starting point so total movement per volley matches one classic round before tuning.

---

## Testing Expectations

- **`isqrt` parity** — Match **[PRD 10](10-fleet-movement.md)** / `openstars.engine.util.isqrt` test vectors (already in the codebase).
- **Tick budget sum** — Over each volley, **`sum_k budget_tick(k) == budget_volley`** for every token.
- **Firing count** — For a battle that lasts **`V` volleys**, each surviving weapon fires **at most `V` times** (same cap scale as **`V` classic rounds**).
- **Monotonicity** — For fixed token positions, increasing **`S`** scales **`R × S`**; for positions on a fixed bearing from the firer, in-range status should follow the Euclidean threshold predictably.
- **Classic ruleset** — Grid-metric golden tests belong to **`classic`** (PRD 81), not OpenStars.

---

## What’s Out of Scope for This PRD

- Obstacles, terrain, or three-dimensional combat.
- Changing damage **per salvo** or initiative **within a volley** — belongs in shared combat stats PRDs or PRD 81.
- **Partial charging** or **cooldowns per weapon in ticks** (everything fires each volley unless classic rules already restrict it).
- Non-integer positions or floating-point geometry (forbidden by PRD 04 for authoritative state).

---

## References

- **[PRD 10 — Fleet Movement](10-fleet-movement.md)** — `isqrt`, squared distance, determinism
- **[PRD 80 — Combat Fundamentals](80-combat-fundamentals.md)**
- **[PRD 81 — Classic combat](81-combat-classic.md)**
- **[Guts of the Battle Engine](../references/guts-of-the-battle-engine.md)**
