# Altair combat updates — beam dissipation and movement AI

**Date:** 2026-04-18
**Goal:** Implement two Altair-specific combat changes from PRD 82 updates: (1) the Altair beam dissipation model (flat zone then linear drop to 90%), and (2) stop the movement AI advancing once all weapons are in range.
**Relevant PRDs:** [82 — Altair combat](docs/prd/82-combat-altair.md), [81 — Classic combat](docs/prd/81-combat-classic.md) (reference for classic dissipation)
**Depends on:** [2026-04-06-altair-combat-prototype](tasks/2026-04-06-altair-combat-prototype.md) (completed)

---

## Step 1 — Beam dissipation function

Add a `beam_dissipation_multiplier` function to `backend/openstars/combat/altair/geometry.py` implementing PRD 82 §Shooting beam dissipation:

- Returns the damage multiplier as an integer fraction (numerator, denominator) for PRD 04 integer arithmetic.
- **100% damage** when `dist ≤ R_eff // 10` (the flat zone — no benefit to closing further).
- **Linear drop to 90%** from the threshold to `R_eff` (the range limit).
- `R_eff = R_classic * S + starbase_bonus` where `starbase_bonus = S` for starbases, else `0`.
- Formula: `multiplier = (10 * (R_eff - threshold) - (dist - threshold)) / (10 * (R_eff - threshold))` when `dist > threshold`.

Unit tests in this step:
- [ ] At `dist = 0`: multiplier is 1 (full damage).
- [ ] At `dist = R_eff // 10`: multiplier is 1 (edge of flat zone).
- [ ] At `dist = R_eff`: multiplier is 9/10 (90%).
- [ ] At midpoint between threshold and R_eff: correct linear interpolation.
- [ ] Starbase bonus extends R_eff correctly.
- [ ] Range-0 weapons (`R_classic = 0`): handle without division by zero.

---

## Step 2 — Apply dissipation in shooting phase

Wire `beam_dissipation_multiplier` into `_run_shooting_phase` in `backend/openstars/combat/altair/engine.py`:

- [ ] Compute effective damage as `weapon_damage * numerator // denominator` (integer, rounds down).
- [ ] Use the dissipated damage value in `WeaponFiredEvent.damage` and when reducing target HP.
- [ ] Update `WeaponFiredEvent` model to include a `dissipation_pct` field (integer 0–100, for replay display).

Unit tests in this step:
- [ ] Two-token fixture at various distances: verify damage values match expected dissipated amounts.
- [ ] Token at point-blank (dist=0) deals full `weapon_damage`.
- [ ] Token at max range deals 90% of `weapon_damage`.
- [ ] Golden log fixture updated to reflect dissipation.

---

## Step 3 — Movement AI: stop advancing at max-damage range

Update `_move_toward` / movement tick logic in `backend/openstars/combat/altair/engine.py` so that a token **stops advancing** once it is within the flat dissipation zone (≤ 10% of max range) of its target — closing further gives no damage benefit.

- [ ] Before moving, check if `dist ≤ R_eff // 10` for the token's weapon. If so, skip movement (stay put rather than closing to point-blank).
- [ ] If `dist > R_eff` (out of range entirely), continue closing as before.
- [ ] If `threshold < dist ≤ R_eff` (in range but outside flat zone), close toward threshold, not toward the target position.

Unit tests in this step:
- [ ] Token already inside flat zone does not move.
- [ ] Token outside weapon range closes toward target.
- [ ] Token in range but outside flat zone closes to threshold distance, then stops.
- [ ] Two tokens with different weapon ranges behave independently.

---

## Step 4 — Lint, tests, and log schema

- [ ] `uv run ruff check .` and `uv run ruff format --check .` clean.
- [ ] `uv run pytest` passes, including updated golden log fixtures.
- [ ] Bump `ruleset_schema_version` to `"altair-v2"` in models.py and update `CURRENT_SCHEMA_VERSION`.

---

## Explicitly out of scope

- Classic combat engine dissipation (PRD 81 — unchanged, not yet implemented).
- Full battle-order AI (Maximise Damage Ratio, Disengage, etc.) — only the basic "advance toward target" AI is updated.
- Sapper-specific dissipation behaviour (follows beam model per PRD, but no sapper weapon type exists in v1).
- Frontend replay viewer changes for dissipation visualisation.
