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
10. [10-fleet-movement.md](10-fleet-movement.md) — Fleet movement algorithm, warp speed, waypoint consumption, distance units (extracted from PRD 07)
11. [11-scanners.md](11-scanners.md) — Scanner types (normal/penetrating), visibility rules, fog of war, scan levels
12. [12-economy-and-resources.md](12-economy-and-resources.md) — Minerals, mines, factories, resources, concentration depletion
13. [13-production.md](13-production.md) — Per-planet production queues, queue editing, partial progress, mine/factory construction
14. [14-population.md](14-population.md) — Planet habitability, population growth and death, overcrowding
15. [15-freight-transport.md](15-freight-transport.md) — Cargo capacity, waypoint transport/transfer tasks, repeat routes, jettison
16. [16-colonisation.md](16-colonisation.md) — Colonize waypoint task, colony ship hull, ship dismantling, colony establishment
17. [17-starbases.md](17-starbases.md) — Starbase state, starter starbase designs, construction/upgrades, shipbuilding gate, refuelling
50. [50-api.md](50-api.md) — REST API schema, endpoints, error format
60. [60-ui-overview.md](60-ui-overview.md) — Design principles, technology, screen layout, colour system, phase 2 scope
61. [61-ui-galaxymap.md](61-ui-galaxymap.md) — Galaxy map rendering, zoom levels, pan/zoom controls, click interactions
62. [62-ui-planet-detail.md](62-ui-planet-detail.md) — Planet detail panel, scan levels, mineral display
63. [63-ui-fleet-detail.md](63-ui-fleet-detail.md) — Fleet detail panel, waypoint editor, turn flow
64. [64-ui-waypoint-orders.md](64-ui-waypoint-orders.md) — Fleet waypoint order UX, task editor, repeat routes, API payload mapping
80. [80-combat-fundamentals.md](80-combat-fundamentals.md) — Combat authority, determinism, RNG, combat log, replay, ruleset ids
81. [81-combat-classic.md](81-combat-classic.md) — Classic ruleset: 10×10 grid, tokens, rounds, movement/shooting (Stars!-faithful)
82. [82-combat-openstars.md](82-combat-openstars.md) — OpenStars ruleset: scaled integer arena, same combat maths, geometry at scale `S`


## Workflow

PRDs are written and reviewed before implementation begins. Changes to game mechanics or features should be reflected here first.
