# Product Requirement Documents

This directory contains the PRDs for OpenStars!

## Completed

1. [01-overview.md](01-overview.md) — Vision, goals, scope, core architecture
2. [02-galaxy-map.md](02-galaxy-map.md) — Coordinate system, galaxy.json format, planet placement algorithm
3. [03-turn-lifecycle.md](03-turn-lifecycle.md) — Three-file turn cycle, player state derivation, command submission
4. [04-engine-conventions.md](04-engine-conventions.md) — Entity IDs (base36), determinism, game seed, RNG architecture, engine rules
5. [05-global-state.md](05-global-state.md) — Global state schema, turn 0 generation
6. [06-technical-platform.md](06-technical-platform.md) — GCP runtime, Docker strategy, CI/CD, local dev
7. [07-turn-mechanics.md](07-turn-mechanics.md) — Phase 1 resolution pipeline, fleet movement, player commands, Stars! reference order
8. [08-ui.md](08-ui.md) — UI design, galaxy map rendering, interactions, layout

10. [10-fleet-movement.md](10-fleet-movement.md) — Fleet movement algorithm, warp speed, waypoint consumption, distance units (extracted from PRD 07)
11. [11-scanners.md](11-scanners.md) — Scanner types (normal/penetrating), visibility rules, fog of war, scan levels
- [phasing.md](phasing.md) — Phase breakdown and roadmap
50. [50-api.md](50-api.md) — REST API schema, endpoints, error format
## TODO
- Race design — Primary racial traits, lesser racial traits, habitability, economy settings
- Planets — Planet properties, minerals, environment
- Economy & production — Population, mining, factories, research, production queues
- Ships & fleets — Hull types, ship designer, components, fleet management, movement
- Combat — Battle engine, grid, tokens, targeting, damage model
- Special mechanics — Minefields, stargates, mass drivers, terraforming, diplomacy, random events
- Turn resolution — Order of events pipeline, resolution steps
- UI & UX — Design principles, key screens, map, planet/fleet views

## Workflow

PRDs are written and reviewed before implementation begins. Changes to game mechanics or features should be reflected here first.
