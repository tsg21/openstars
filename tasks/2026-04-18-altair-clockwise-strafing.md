# Altair combat updates — clockwise strafing at desired range

**Date:** 2026-04-18
**Goal:** Update the Altair movement AI so ships that have already reached their desired beam range strafe clockwise around their target instead of stopping dead.
**Relevant PRDs:** [82 — Altair combat](docs/prd/82-combat-altair.md)
**Depends on:** [2026-04-18-altair-combat-updates](tasks/2026-04-18-altair-combat-updates.md)

---

## Step 1 — PRD update

- [x] Document that tokens at desired beam range (`dist ≤ R_eff // 5`) strafe clockwise perpendicular to the target instead of continuing to close or sitting still.
- [x] Update testing expectations and balance notes to cover the new orbiting behaviour.

---

## Step 2 — Engine movement

- [x] Add a helper in `backend/openstars/combat/altair/engine.py` for clockwise perpendicular movement around a target.
- [x] Use that helper when a token is already within its desired beam range.
- [x] Keep out-of-range and close-to-threshold movement behaviour unchanged.

Unit tests in this step:
- [x] Token already inside desired range strafes clockwise.
- [x] Token outside weapon range still closes toward target.
- [x] Two tokens at desired range rotate around each other.
- [x] Tokens with different movement/range states behave independently.

---

## Step 3 — Schema, fixtures, and verification

- [x] Bump `ruleset_schema_version` and `CURRENT_SCHEMA_VERSION` to `"altair-v4"`.
- [x] Update affected Altair golden fixtures.
- [x] `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest` pass.
