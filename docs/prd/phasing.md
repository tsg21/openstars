# Phasing Strategy

## Phase 1 — Bare Minimum Fleet Control
Build the game engine as a pure, framework-independent module. No UI, no server — just the engine with comprehensive tests. The goal is the simplest possible command-and-resolve loop: generate a galaxy, place fleets, set waypoints, resolve turns, watch them move.

Scope:
- Galaxy generation (star map with planets)
- Basic planet model (position, attributes — no economy simulation yet)
- Fleet movement (waypoints, fuel consumption, movement execution)
- Turn resolution pipeline (slimmed down to movement-relevant steps)
- Fog of war / scanner model (basic scanner range, filtered state per player)
- Basic server implementation (turn submission, resolution, state distribution)

## Phase 2 — Basic UI
Minimal web UI on top of the Phase 1 engine and server. The goal is to feel how the game plays — not polish, just enough to interact with the fleet control loop.

Scope:
- Star map visualisation (galaxy view, planets, fleets)
- Fleet selection and waypoint setting
- Turn submission and state refresh
- Basic fog of war rendering

## Phase 3 — Economy & Production
Layer in the planet economy and production systems on top of the working fleet control loop.

Scope:
- Planet economy (population, minerals, factories, mines, production queues)
- Technology research (6 fields, level progression, component unlocks)
- Ship design (hulls, components, slots)
- Race design (primary racial traits, lesser traits, habitability, growth, economy settings)
- Expanded turn resolution pipeline (production, population growth, mining)

## Phase 4 — Combat
Add the combat engine and related mechanics.

Scope:
- Combat engine (10×10 grid, tokens, targeting, damage)
- Bombing
- Battle plans and targeting orders

## Phase 5 — Multiplayer
Player accounts, game lobbies, turn notifications. Evolve the basic server into a full multiplayer platform.

## Phase 6 — Single Player
AI opponents for solo play.

## Phase 7 — Depth & Polish
Remaining mechanics (minefields, stargates, mass drivers, terraforming, diplomacy, random events). AI improvements. UI polish.
