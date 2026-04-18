# PRD 80 — Combat Fundamentals

## Overview

This document defines **cross-ruleset** requirements for combat in OpenStars!: who computes it, how randomness and ordering work, what is persisted, and how clients present it. It applies equally to **[PRD 81 — Classic combat](81-combat-classic.md)** and **[PRD 82 — Altair combat](82-combat-altair.md)**.

Mechanical specifics (grid size, scaling, movement geometry) live in those PRDs. This PRD is the contract between engine, API, persistence, and UI.

---

## Goals

1. **Server authority** — Combat outcomes are computed only on the server during turn resolution. Clients must not run authoritative combat simulation.
2. **Determinism** — Given the same global state, the same submitted commands for that turn, and the same **combat ruleset** configuration, resolution produces the same combat results and the same ordered event log. See **[PRD 04 — Engine Conventions](04-engine-conventions.md)** for global determinism, integer arithmetic, and RNG rules.
3. **Auditability** — A third party with access to the pre-turn state, commands, and ruleset can re-run resolution and verify outcomes.
4. **Replay** — The client can reconstruct a **presentation** of each battle from a persisted **combat log** (and ruleset id), without re-executing engine code.

---

## Combat Ruleset

Each game (or scenario template) selects a **combat ruleset**:

| Ruleset id   | Definition                          |
|-------------|--------------------------------------|
| `classic`   | [PRD 81](81-combat-classic.md)       |
| `altair`    | [PRD 82](82-combat-altair.md)       |

The ruleset id is part of **game configuration** carried in global state (or an equivalent scenario record) so that saves, replays, and tests know which geometry and constants apply.

Changing the ruleset is a **different game balance surface**; cross-ruleset outcome parity is not required.

---

## Resolution Placement

Combat runs during turn resolution at the point where the Stars! order of operations specifies battle resolution (see [`docs/references/stars-resolution-order.md`](../references/stars-resolution-order.md) and **[PRD 07 — Turn Mechanics](07-turn-mechanics.md)**). Exact pipeline step numbers will be updated when combat is wired into the resolver.

Inputs to a single combat resolution instance include at least:

- Relevant **fleet and starbase** snapshots (design references, stacks, battle plans, owners, positions at the location).
- **Location identity** (e.g. deep space tile vs orbit over a planet) for rules that depend on it.
- **Turn number** and **game seed** (for derived RNG streams).
- Active **combat ruleset** id and its **constants** (e.g. scale factor **`S`** for Altair).

Outputs include at least:

- **State mutations**: ships destroyed, damage remaining, fleet dispositions, salvage created, tech-trade side effects, and any other knock-on effects defined by later PRDs.
- **Combat log**: ordered, append-only list of events sufficient for replay and debugging (see below).

---

## Determinism and Randomness

Combat may use randomness (e.g. missile hit checks, initiative ties). All randomness must comply with PRD 04:

- **Seeded PRNG** only — no platform RNG or time-based entropy in combat logic.
- **Derived stream per combat** — e.g. `hash(gameSeed, turn, "combat", locationId, deterministicBattleKey)` so unrelated mechanics do not shift this battle’s dice.
- **Stable context strings** — changing derivation labels breaks save compatibility; version combat logs or rulesets if contexts must change.

Ordering that affects outcomes (fleet processing, token ordering, tie-breaks) must be **fully specified** in the ruleset PRDs and implemented with **explicit sorts** (e.g. lexicographic by entity id), never implicit iteration order.

---

## Server vs Client Responsibilities

| Responsibility | Server | Client |
|----------------|--------|--------|
| Decide who fights, when, and under which ruleset | Yes | No |
| Run damage, movement AI, and casualties | Yes | No |
| Persist combat log and resulting state | Yes | Display only |
| Animate or visualise battle | Optional preview API (non-authoritative) | Yes |
| “What-if” sandbox simulation | Optional dedicated tool with same engine build | Not for live games |

If the client offers a **preview**, it must be labelled non-authoritative unless it calls a server endpoint that runs the real resolver on a scratch state.

---

## Combat Log and Replay

### Purpose

The **combat log** is the canonical record of what happened in a battle. It enables:

- **Battle replay viewer** (see **[PRD 60 — UI Overview](60-ui-overview.md)**).
- **Bug reports** with a reproducible narrative (“round 7, slot 3 fired at token X”).
- **Partial transparency** under fog of war (see below).

### Requirements

1. **Ordered events** — Total order is part of the deterministic contract; two runs must emit the same sequence.
2. **Ruleset and version** — Each log references the combat ruleset id and a **ruleset schema version** so old logs remain interpretable.
3. **Sufficient for rendering** — Events carry enough data to animate movement, targeting, and hits without re-running AI (e.g. from/to positions or cells, weapon slot, target token id, damage breakdown).
4. **Integer-friendly** — Numeric fields use integers (or rational pairs where Stars! uses fractions), consistent with PRD 04.

The exact JSON schema for events is an implementation detail, but must be frozen per ruleset version.

### Client Replay

Replay **consumes** the log:

- The client steps through events and updates a local **presentation model** (ship sprites, beams, summaries).
- The client does **not** recompute hit chances or movement decisions.

If compression is needed, store a compact binary form alongside a documented mapping to the canonical event list.

---

## Fog of War and Player Knowledge

Global state after resolution reflects **truth**. Per-player state may **filter** combat detail:

- A player who was not present might see **no log**, or only a **summary** (“Battle at X: Player A lost N kt”).
- Participants might receive **full logs** for battles they were in, or a filtered view if the design goals require uncertainty.

The exact visibility rules should align with scanner and presence rules in **[PRD 11 — Scanners](11-scanners.md)** once combat intel is specified. This PRD only requires that the server **can** produce both full and redacted representations from the same stored log.

---

## Commands and Battle Plans

Players issue **battle plans** (target priorities, tactics, stances) through command types to be defined when combat commands land in the API. Combat resolution **reads** those plans from state; it does not accept ad-hoc client payloads during resolution.

Validation (legal targets, race filters) happens at command submission time where possible.

---

## Testing

- **Unit tests** — Pure functions: given a battle snapshot + derived RNG, exact event list and casualties.
- **Golden logs** — Store expected combat logs for fixed fixtures per ruleset; any engine change that alters ordering or dice must update them deliberately.
- **Cross-platform** — Same inputs produce the same log on all supported runtimes (PRD 04).

---

## What’s Out of Scope for This PRD

- Weapon stats, hull systems, minefields, carriers, and planetary bombardment specifics (later PRDs).
- Exact REST payloads for battle plans (future API PRD).
- Art direction for the replay viewer (UI PRDs).

---

## References

- **[PRD 04 — Engine Conventions](04-engine-conventions.md)** — Determinism, RNG derivation, integers
- **[PRD 81 — Classic combat](81-combat-classic.md)**
- **[PRD 82 — Altair combat](82-combat-altair.md)**
- **[Guts of the Battle Engine](../references/guts-of-the-battle-engine.md)** — Community reference for Stars! behaviour
- **[Elite-games Stars! docs](../references/elite-games-ru-en/README.md)** — Translated Russian Stars! documentation with detailed combat mechanics
- **[Appendix B — Technology Tables](../references/manual/chapters/appendix-b-technology-tables.md)** — Component stats from the original manual
