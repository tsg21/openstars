# PRD 82 — Altair combat (scaled integer arena)

## Overview

This document defines the **Altair** combat model (ruleset id **`altair`**): tactical combat on a **large integer coordinate** arena where **all spatial quantities are scaled** from the classic model so that **relative geometry is preserved** (see “Approach 1” in design discussions). Weapon ranges, movement budgets, disengage distances, and board extent are expressed in the **same integer units**; a single **scale factor** maps classic “squares” to **Altair arena units**.

**Codename — Altair:** internal and code references use **Altair** for this model so it is not confused with the **OpenStars!** product name.

**Parent contract:** **[PRD 80 — Combat Fundamentals](80-combat-fundamentals.md)**.

**Logical twin:** **[PRD 81 — Classic combat](81-combat-classic.md)** shares the same **non-spatial** rules where Altair does not explicitly diverge (attractiveness, initiative ordering within a **round’s** shooting phase, damage pipeline, battle orders, token model). In **Altair**, each **combat round** is **many movement ticks** followed by **one shooting phase** (see **Combat rounds and ticks**). *Round* here is **battle time**, not the strategic **turn** (galaxy year — **[PRD 03 — Turn Lifecycle](03-turn-lifecycle.md)**).

---

## Ruleset Identity

| Field | Value |
|-------|--------|
| Ruleset id | `altair` |
| Geometry | Bounded integer coordinate arena |
| PRD | This document |

---

## Backend package layout

Combat implementations live under **`backend/openstars/combat/`**, one subdirectory per ruleset:

| Path | Ruleset |
|------|---------|
| `backend/openstars/combat/altair/` | This PRD (**`altair`**) |
| `backend/openstars/combat/classic/` | [PRD 81](81-combat-classic.md) (**`classic`**) — to be populated when the classic engine is implemented |

Shared helpers used by more than one ruleset may live in `backend/openstars/combat/` (e.g. a future `common` module). The **Altair** implementation may import **`openstars.engine.util.isqrt`** ([PRD 10](10-fleet-movement.md)); avoid coupling to turn resolution or full galaxy state.

---

## Design Intent

1. **Open battle space** — Tokens have **integer positions** on a board large enough for finer manoeuvre and clearer replay animation than a 10×10 cell id.
2. **Scaled parity** — For a chosen scale `S`, one classic **square edge** corresponds to `S` arena units. A classic weapon range `R` squares becomes **`R × S` arena units** for **range radius** (see Distance). Movement **per combat round** scales the same way (see Movement).
3. **Same combat maths per shooting phase** — When weapons **fire** (at the **end of each round**, after **T** ticks), damage per salvo, shields, armour granularity, hit rolls, initiative order, and attractiveness use the **same algorithms** as classic unless noted here. Weapons do **not** fire every **tick**; they fire **once per round** so overall **damage over a battle** stays in line with classic (one full shooting pass per Stars! combat round).
4. **Euclidean distance via `isqrt`** — Altair does **not** use Chebyshev or Manhattan grid distance. Range and movement geometry use the same **integer Euclidean** convention as fleet movement in **[PRD 10 — Fleet Movement](10-fleet-movement.md)** (`dist_sq = dx² + dy²`, `dist = isqrt(dist_sq)`). At a **large** `S`, the unresolved classic “one diagonal square” question matters far less than the width of the arena in internal units, so combat behaves like **smooth** tactical space rather than a 10×10 chessboard.
5. **Smooth time** — Classic has at most **16** rounds per battle; each round moves tokens (in grid phases) then **every weapon fires** (per slot, initiative order). Altair uses **`T`** movement ticks per **round** (default **`T = 20`**) so paths are **many small steps**. **Thrusters and jets** remain in the **classic quarters formula** (so they still grant their **½ / ¼** square equivalents **per round**); spreading **`budget_round`** across **`T`** makes each **tick** a **small** nudge. **`Energy Dampener`** stays a **flat penalty** per round (**see Movement**). No quarter-square **oscillation table**.
6. **No classic quarter-square round table** — Altair does **not** replicate the **8-round movement table** or phased grid stepping from PRD 81.

---

## Constants

### Scale Factor

- **`S`** — Positive integer, **ruleset constant**, stored with game/scenario configuration.
- **Default: `S = 1000`.** That yields a **`10 000 × 10 000`** arena (see below): enough internal resolution that positioning within a notional classic “cell” dominates edge cases, and ranges measured with **`isqrt`** behave smoothly rather than like a coarse grid.
- All players in a game use the same **`S`**.

### Arena Extent

- Classic spans **10** cells per axis. The Altair arena spans **`10 × S` integer units** per axis (default), i.e. the same **relative** extent as classic but finer resolution.
- Coordinates are integers **`(x, y)`** with **`0 ≤ x < 10·S`** and **`0 ≤ y < 10·S`** (exact inclusive/exclusive bounds fixed in implementation and tests).

*Rationale:* Keeping the **10× classic span** avoids turning Altair battles into an unbounded kiting simulator while still allowing **`S` positions per classic “cell”** along each axis for movement and presentation.

### Combat rounds and ticks

| Symbol | Meaning | Default |
|--------|---------|---------|
| **`T`** | Movement **ticks** per **combat round** (before the shooting phase) | **`20`** |
| **`N_rounds`** | Maximum **combat rounds** per battle (same cap as classic’s **16** rounds) | **`16`** |

- **Tick index** `t = 0, 1, …` counts **movement steps within the current round**. After every **`T` ticks**, the engine runs a **shooting phase** (full weapon cycle as in classic), then starts the **next round** at tick **`0`** unless the battle has ended.
- **Maximum length:** **`N_rounds × T` ticks** before the battle is forced to end if not already resolved (same role as classic’s 16-round cap). Example: **`16 × 20 = 320`** ticks.
- **Round-scoped effects** in classic (e.g. `Regenerating Shields` **10%** per round, target re-selection cadence) advance **once per combat round** (every **`T` ticks**), **not** once per movement tick — unless this PRD is later amended.

*Rationale:* In Stars!, **each weapon can fire once per combat round**. Altair **decouples** **motion** (fine-grained **ticks**) from **fire** (once at **round** end): balance stays comparable to classic; only **positioning** becomes smoother.

### Distance (`isqrt`)

Altair uses **integer Euclidean distance** in arena units, matching the engine’s existing helper (see **`isqrt`** in **[PRD 10 — Fleet Movement](10-fleet-movement.md)** and `openstars.engine.util.isqrt`):

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

This deliberately **differs** from **[PRD 81](81-combat-classic.md)** grid metrics (Chebyshev / Manhattan / etc.). Altair targets **large `S`** so that tactical geometry is **approximately continuous**; classic grid parity is not a goal for this ruleset.

---

## Positions and Tokens

- Each **token** has an **integer position** `(x, y)` in arena coordinates.
- **Multiple tokens may share the same coordinates** (stacking in the same “point” of space), preserving the classic rule that many tokens can occupy one cell.
- **Token limit (256)** and **per-race fair sharing** behave as in classic; only position representation changes.

---

## Movement

### Budget per round (classic stats, smooth ticks)

Altair does **not** copy classic’s quarter-square **oscillation table**. Hull, engines, weight, **`Overthruster`**, and **`Maneuvering Jet`** still matter through the **same Stars! combat movement formula** as classic (see **[PRD 81](81-combat-classic.md)** and the manual): those components already enter as **quarter-squares per classic round** (**`+½`** per thruster, **`+¼`** per jet, etc.). **Each Altair combat round** uses **one** application of that formula for movement budget, then spreads the result across **`T` ticks**, so each tick’s step is **small** even when the **round** total matches classic.

1. **Quarters per round** — Compute **`quarters_round`** with the **full** classic formula (see **[PRD 81 — Combat Maneuvering Speed Formula](81-combat-classic.md#combat-maneuvering-speed-formula)**; all components except effects handled below), capped at **10** quarter-squares (**2½** classic squares, speed 0.5 = 2 quarters minimum for ships), same as Stars!.
2. **Convert to arena units:**

   ```text
   base_round_units = (quarters_round × S) // 4
   ```

3. **`Energy Dampener`** — If classic rules say the battle is dampened, subtract **`dampen_units`** arena units **per token per round** (mirrors **−1** classic square per Stars! round). Default **`dampen_units = S`**. Not additive per extra dampener ship, same as classic.

4. **Round movement budget**

   ```text
   budget_round = max(0, base_round_units − dampener_penalty)
   ```

   where **`dampener_penalty = dampen_units`** if the dampener applies to that token, else **`0`**.

If playtesting shows thruster/jet contributions should be **weaker or stronger** than classic’s embedded quarters, adjust via **ruleset data** (e.g. scale **`quarters_round`** after the formula, or use a stripped base plus explicit bonuses) — but **do not** double-count the same component twice.

### Budget per tick (smooth stepping)

For each token, split **`budget_round`** across the **`T` ticks** of the current round **deterministically**:

```text
b = budget_round // T
r = budget_round % T
```

For tick **`k`** within the round (`k = 0 … T−1`):

```text
budget_tick(k) = b + (1 if k < r else 0)
```

So the **sum** of **`budget_tick`** over one round equals **`budget_round`** exactly (no drift).

### Per tick: motion only

- **Order within a round** — At **round start** (before tick `k = 0`): perform classic **per-round** setup — e.g. all tokens **choose / refresh primary targets** per battle plans (Stars! round step 1). Then run ticks **`k = 0 … T − 1`** (movement only). Then **shooting phase**. (Mirror of classic **choose → move → fire**, with **move** subdivided into **`T` steps.)
- **Each tick** — Every token **may move once** to any **integer** position in the arena with **`isqrt(dx² + dy²) ≤ budget_tick(k)`** for that tick.
- **No movement** on ticks that do not exist; **no** classic phased sub-steps within a tick.

### Movement AI and Order

- **Same battle orders** and **same high-level movement AI** as classic (tactics, attractiveness, targeting). **Primary target** choice follows classic **once per round** (at round start); within the round, the AI picks a **destination each tick** within **`budget_tick(k)`** toward that target (or tactic equivalent) as positions update.
- **Altair max-damage strafing** — Once a token has reached its desired beam range (the flat dissipation threshold, **`dist ≤ R_eff // 5`**), it does **not** continue closing. Instead it spends its movement tick on a **clockwise perpendicular strafe** relative to the target, approximating an orbit at roughly constant range. This produces visible circling in two-token engagements while preserving the “no incentive to ram closer” design goal.
- **Movement order** — Each tick, tokens move in **weight order** with the same **±15%** jitter and deterministic tie-breaks as PRD 81.

### End of round: shooting

- After **`T` ticks** have completed (movement only on each), run **one shooting phase**: same structure as classic — initiative, slot order, full salvos, spillover, etc. Weapons **do not** fire on intermediate ticks.
- Then increment **`round_index`**; if **`round_index ≥ N_rounds`**, end the battle per classic termination rules; otherwise start the **next round** at tick **`k = 0`** with a fresh **`budget_round`** (recompute if battle effects ever change speed).

### Disengage and Board Edge

- Classic **”seven squares”** to leave becomes **`7 × S` arena units** of qualifying movement toward **exiting the bounded arena**, with exit predicates mirroring classic **off-board** semantics at scale.
- In classic, the number of **rounds** to accumulate 7 cells varies by speed (see PRD 81 speed table). In Altair, the token accumulates **arena units** of disengage movement per tick; once the total reaches **`7 × S`**, the token exits at the end of the current round.
- **Unarmed tokens** always disengage regardless of battle plan (same as classic — see PRD 81).

### Starbases

- **Immobile**; **+1 classic square** weapon range becomes **`+S`** to the **`R × S`** radius threshold (see Distance).

---

## Shooting

- **Cadence** — All shooting happens at **round end** (after each block of **`T` ticks**), **not** every tick. One pass through weapons (per classic rules) ≈ one Stars! combat **round** for output purposes.
- **Range:** use **`dist`** and **`R × S + starbase_bonus`** as in Distance; do **not** use a separate “range units” accumulator unless needed for display.
- **Beam dissipation** — Altair preserves classic's **10% total dissipation** but with a **flat zone** at close range to remove the incentive to close to point-blank. Beams deal **100% damage** at distances up to **20%** of the weapon's maximum range, then damage decreases **linearly to 90%** at the range limit. For a weapon with effective range `R_eff = R × S + starbase_bonus`:

  ```text
  threshold = R_eff // 5
  if dist ≤ threshold:
      damage_multiplier = 1                                           # full damage
  else:
      damage_multiplier = 1 − (dist − threshold) / (10 × (R_eff − threshold))   # 1 → 0.9
  ```

  For integer arithmetic (PRD 04), scale numerator and denominator to avoid fractions: multiply damage by `10 × (R_eff − threshold) − (dist − threshold)`, then divide by `10 × (R_eff − threshold)`. This matches classic's overall dissipation budget (10% at max range) while **removing the incentive to close to point-blank range** — there is no benefit below 20% of max range.
- **Destroyed before firing** — As in classic, if a token is destroyed during a round’s shooting phase before its slots fire, it does not fire later that round.

---

## Replay and Presentation

- Logs record **tick index** (within round), **`round_index`**, **integer positions**, and **scaled ranges** so the client can animate **smooth** motion between shooting phases without re-running AI.
- Optional display: overlay a **10×10 classic grid** for players who think in squares (`cellX = floor(x / S)`, etc.); optional **“fast-forward to next round”** (skip to shooting) for viewers who only care about shots.

---

## Balance Notes

- Altair is **not** outcome-identical to classic: **Euclidean** range is a different shape than a Chebyshev or Manhattan “diamond/square” in grid space. **`S = 1000`** makes local geometry **smooth enough** that players optimise in continuous terms; it does **not** restore classic grid parity.
- **Beam dissipation** matches classic's 10% total reduction but introduces a **flat zone** below 20% of max range where closing further yields no benefit, removing the classic incentive for beam ships to ram to point-blank.
- **Clockwise strafing at desired range** is an Altair-only readability/behaviour tweak; it is not intended to reproduce classic cell-by-cell movement exactly.
- **Micro-positioning** within the arena can differ from “cell-centred” tokens; large **`S`** limits how much one integer step changes relative range.
- **`T`** and **`dampen_units`** are primary levers if **motion feels too choppy or too fast** relative to **time between shooting phases**; **`quarters_round`** from the classic formula should remain the starting point so total movement **per round** matches one Stars! round before tuning.

---

## Integration with turn resolution

Altair is invoked by the main game's combat resolve step (**[PRD 07](07-turn-mechanics.md)** §Step 3) whenever `game.combat_ruleset == "altair"`. The integration layer — not the engine itself — is responsible for building the `BattleSnapshot` and applying its output back to fleet state.

### Building the snapshot

- Participating fleets come from the battle-site group detected by the resolver (see PRD 80).
- Tokens are materialised via `openstars.combat.fleet_to_tokens.tokens_from_fleet` using the game's design registry and component catalogue.
- **Arena entry positions** — place each owner's fleets at a deterministic entry point on a circle around the arena centre. For an ordered list of participating owners `o_0, o_1, …, o_{N-1}` (sorted lexicographically by username), entry point for owner `o_i` is:

  ```text
  cx = arena_size // 2
  cy = arena_size // 2
  R  = arena_size * 4 // 10
  θ_i = 2π · i / N        # computed with integer-friendly sin/cos lookups or scaled fixed point
  entry_i = (cx + round(R · cos θ_i), cy + round(R · sin θ_i))
  ```

  For the default `S = 1000` (arena 10 000) this places combatants at radius 4 000 — comfortably outside beam range at start. All of one owner's tokens share the same entry point (stacking is permitted, see §Positions and Tokens). Integer trigonometry uses the same scaled-integer convention as elsewhere in the engine; exact pivot values are fixed in implementation and tests.

- `AltairCombatConfig` values (`S`, `T`, `N_rounds`) come from game configuration; `ruleset_schema_version` comes from the engine build.

### Casualty mapping back to fleets

The engine does not mutate `Fleet` models directly. The integration layer consumes the final token HPs from the log (or an engine-returned survivor list) and applies the proportional rule defined in **[PRD 80 §Casualty mapping](80-combat-fundamentals.md#casualty-mapping)**. Because every token id has the form `{prefix}-{fleet_id}-{composition_index}`, each surviving token can be mapped back to its originating `FleetComposition` entry unambiguously.

## Testing Expectations

- **`isqrt` parity** — Match **[PRD 10](10-fleet-movement.md)** / `openstars.engine.util.isqrt` test vectors (already in the codebase).
- **Tick budget sum** — Over each round, **`sum_k budget_tick(k) == budget_round`** for every token.
- **Firing count** — For a battle that lasts **`R` rounds**, each surviving weapon fires **at most `R` times** (same cap scale as **`R` Stars! combat rounds**).
- **Monotonicity** — For fixed token positions, increasing **`S`** scales **`R × S`**; for positions on a fixed bearing from the firer, in-range status should follow the Euclidean threshold predictably.
- **Beam dissipation** — Verify 100% damage at ≤20% of max range, 90% at max range, and correct linear interpolation between. Test integer rounding at boundary distances. Confirm sapper weapons also use the Altair dissipation model.
- **In-range movement** — Verify tokens at desired beam range strafe clockwise instead of stopping dead, and that two-token fights show opposite vertical movement consistent with circling.
- **Classic ruleset** — Grid-metric golden tests belong to **`classic`** (PRD 81), not **`altair`**.

---

## What’s Out of Scope for This PRD

- Obstacles, terrain, or three-dimensional combat.
- Changing damage **per salvo** or initiative **within a round’s shooting phase** — belongs in shared combat stats PRDs or PRD 81.
- **Partial charging** or **cooldowns per weapon in ticks** (everything fires at **round end** unless classic rules already restrict it).
- Non-integer positions or floating-point geometry (forbidden by PRD 04 for authoritative state).

---

## References

- **[PRD 10 — Fleet Movement](10-fleet-movement.md)** — `isqrt`, squared distance, determinism
- **[PRD 80 — Combat Fundamentals](80-combat-fundamentals.md)**
- **[PRD 81 — Classic combat](81-combat-classic.md)** — Combat speed formula, initiative rules, damage pipeline
- **[Guts of the Battle Engine](../references/guts-of-the-battle-engine.md)**
- **[Elite-games Stars! docs](../references/elite-games-ru-en/README.md)** — Translated Russian Stars! documentation
