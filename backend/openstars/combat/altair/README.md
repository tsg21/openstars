# Altair combat engine

**Ruleset id:** `altair`
**PRD:** [82 — Altair combat](../../../docs/prd/82-combat-altair.md)
**Parent contract:** [80 — Combat fundamentals](../../../docs/prd/80-combat-fundamentals.md)

## Scope

Deterministic tactical combat on a large integer-coordinate arena. Tokens
move over many ticks per round, then weapons fire once per round. All spatial
quantities are scaled from classic Stars! by a factor **S** (default 1000).

## Import policy

This package is **self-contained**. External imports are limited to:

- **`openstars.engine.util.isqrt`** — integer square root (shared with fleet
  movement).
- Python stdlib and Pydantic.

**Do not** import from `openstars.engine.models`, `openstars.engine.resolve*`,
`openstars.server`, or FastAPI inside this package.

## Public API

```python
from openstars.combat.altair import run_battle
from openstars.combat.altair.models import BattleSnapshot, AltairCombatConfig, CombatLog
```

## Event log schema

See `CombatLog` in `models.py`. Schema version is embedded in the log so
consumers can validate compatibility. Events are ordered and typed with a
discriminated `type` field:

| Event type | Payload fields |
|------------|---------------|
| `round_start` | `round_index` |
| `tick_start` | `round_index`, `tick_index` |
| `token_moved` | `token_id`, `from_pos`, `to_pos`, `round_index`, `tick_index` |
| `shooting_phase_start` | `round_index` |
| `weapon_fired` | `attacker_id`, `target_id`, `damage`, `hit`, `round_index` |
| `damage_applied` | `target_id`, `damage`, `remaining_hp`, `round_index` |
| `token_destroyed` | `token_id`, `round_index` |
| `round_end` | `round_index` |
| `battle_end` | `reason` |

## Implementation status

- [x] Package skeleton and public API
- [x] Config, geometry, distance
- [x] Token model and snapshot
- [x] Tick loop and movement (v1)
- [x] Shooting phase stub (v1)
- [x] CombatLog schema and versioning
- [ ] Full initiative / attractiveness
- [ ] Shield / armour split
- [ ] Energy Dampener
- [ ] Disengage / board edge exit
- [ ] Starbase range bonus
