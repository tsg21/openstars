# Altair combat tokens — multi-weapon tokens and fleet conversion

**Date:** 2026-04-21
**Goal:** Rework the Altair combat `Token` so it references a design, carries a ship count, and aggregates identical weapons into a list. Add a function that derives tokens from a `Fleet` using a design + component catalogue lookup.
**Relevant PRDs:** [82 — Altair combat](docs/prd/82-combat-altair.md)
**Depends on:** [2026-04-18-altair-combat-updates](tasks/2026-04-18-altair-combat-updates.md) (completed)

---

## Step 1 — TokenWeapon and restructured Token

Update `backend/openstars/combat/altair/models.py`:

- [x] Add `TokenWeapon` with fields: `component_id: str`, `weapon_type: Literal["beam"]`, `count: int` (≥1), `damage: int` (≥0), `range_classic: int` (≥0), `initiative: int` (≥0). Only beam is supported in v1; the `weapon_type` discriminator leaves room for torpedoes later.
- [x] Replace `Token.weapon_damage` / `Token.weapon_range_classic` with `weapons: list[TokenWeapon]` (default empty).
- [x] Add `design_id: str | None` (optional — hand-built fixtures may omit it) and `ship_count: int` (default 1, ≥1).
- [x] Bump `CURRENT_SCHEMA_VERSION` / `ruleset_schema_version` default to `"altair-v5"`.

Unit tests in this step:
- [x] `Token` JSON round-trip with multiple weapons preserves `weapons`, `ship_count`, `design_id`.
- [x] A token with no weapons is valid (non-combatant or damaged fleet).
- [x] `CombatLog.schema_version` defaults to `altair-v5`.

---

## Step 2 — Engine: shoot once per weapon group

Update `backend/openstars/combat/altair/engine.py`:

- [x] `_run_shooting_phase` iterates each alive attacker and each of its `weapons`, firing one `WeaponFiredEvent` per weapon group. Aggregated damage per group = `weapon.damage * weapon.count * numerator // denominator`. Range / initiative / dissipation come from each weapon, not the token.
- [x] Within an attacker, sort weapon groups deterministically (by `initiative` desc, then `component_id`) to keep logs stable.
- [x] Movement AI picks the token's longest-range weapon for in-range / flat-zone / closing decisions. A token with no weapons never has a threshold and always closes toward its target (but still stops at distance 0 via existing clamp).
- [x] `WeaponFiredEvent` gains a `component_id: str` field so replays can distinguish weapon groups.

Unit tests in this step:
- [x] Two weapon groups on the same attacker produce two `weapon_fired` events in one round.
- [x] Aggregated damage = `damage * count` at point-blank; still applies dissipation at range.
- [x] Movement AI uses the longer of two weapon ranges when deciding where to stop.
- [x] Existing dissipation / point-blank / max-range shooting tests still pass against the new `weapons=[...]` shape.

---

## Step 3 — `tokens_from_fleet` helper

New module `backend/openstars/combat/fleet_to_tokens.py` (lives outside the altair package so it can import from `openstars.engine.models` and the catalogue without breaking altair's self-contained import policy):

- [x] `tokens_from_fleet(fleet, designs_by_id, catalogue, *, token_id_prefix=None) -> list[Token]`.
- [x] One `Token` per `FleetComposition` entry; skip entries whose design is unknown.
- [x] Aggregate identical weapon components across slots on the design: sum `component_count` per `component_id`, then multiply by `ship_count`. Each becomes a `TokenWeapon`.
- [x] Skip non-beam weapons for v1 with a TODO (no such weapons exist yet, but the catalogue could grow).
- [x] `hp` = `(hull.armour_points + Σ armour_component.armour_points × slot_count) × ship_count`. Shield components are ignored in v1 (separate pool, not yet modelled).
- [x] `movement_quarters` stays at the default (`4`) — battle-speed derivation is out of scope.
- [x] Token ids: `{prefix}-{fleet.id}-{composition_index}` so ids are stable and unique across a battle.

Unit tests in this step:
- [x] Fleet with one design and one beam weapon → one token, one weapon group, count = slot_count × ship_count.
- [x] Two ships sharing the same beam in different slots aggregate to a single weapon group with summed count.
- [x] Unknown design_id is skipped, not raised.
- [x] Armour components add to `hp`.
- [x] Token id prefix used when provided.

---

## Step 4 — Lint, tests, and golden log

- [x] `uv run ruff check .` and `uv run ruff format --check .` clean.
- [x] Regenerate `backend/tests/combat/altair/fixtures/minimal_battle.json` against the new Token shape (old fixture deleted, re-emitted by `test_golden_file`).
- [x] `uv run pytest` passes end-to-end.

---

## Explicitly out of scope

- Torpedo weapons, sappers, gattling — only beam weapons are modelled; `weapon_type` leaves the door open.
- Shields as a separate pool.
- Initiative-based firing order across tokens (PRD 82 deferred) — only per-attacker weapon ordering is deterministic.
- Battle-speed derivation from engine/hull — `movement_quarters` stays a snapshot input for now.
