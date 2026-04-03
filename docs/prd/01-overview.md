# PRD 01 — Overview

## Vision

OpenStars! is a modern web reimagining of Stars! (1995) — a deeply complex turn-based 4X space strategy game. The original game cultivated a devoted play-by-email community that kept playing for decades, but its 16-bit Windows client is increasingly difficult to run, and no faithful successor was ever released.

OpenStars! aims to bring those mechanics to the browser — faithful to the depth of the original, with a contemporary UI and native web-based multiplayer.

## Core Architecture: Commands & Resolution

The game follows a **simultaneous-turn, command-and-resolve** model — the same fundamental architecture as the original Stars!

### How a Turn Works

1. **Command Phase (Client)** — Each player uses the UI to issue orders for the upcoming year:
   - Set fleet waypoints and waypoint tasks (load, unload, colonise, patrol, etc.)
   - Manage planet production queues (factories, mines, defences, ships, starbases, research)
   - Allocate research spending across technology fields
   - Design new ship blueprints
   - Set battle plans and diplomacy postures
   - Configure mineral packet launches, mine laying, terraforming orders

   The UI is essentially an **order editor**. It helps the player understand the current game state and compose their commands, but it does not simulate or resolve anything.

2. **Submission** — Once satisfied, the player submits their orders. In the original game this was a `.x` turn file sent by email. In OpenStars!, it's submitted to the server via the web client.

3. **Resolution Phase (Server)** — Once all players have submitted (or a deadline passes), the server **resolves the turn**. This is a deterministic pipeline that processes all players' commands simultaneously, in a strict fixed order (see PRD 07 for the full Stars! resolution order and the Phase 1 subset).

   The resolution engine takes the previous game state plus all players' orders and produces the next game state. It is **deterministic** — the same inputs always produce the same outputs. It is **authoritative** — the server is the single source of truth.

4. **New State Distribution** — The server generates a new game state for each player, filtered by what their scanners can see (fog of war). Players load the new state, review what happened, and begin composing their next set of orders.

### Why This Model

- **Asynchronous multiplayer** — players don't need to be online at the same time. Submit your orders whenever you're ready.
- **No waiting for opponents** — unlike sequential-turn games, everyone acts simultaneously. Deadlines (e.g. one turn per day) keep things moving.
- **Deterministic resolution** — the engine is a pure function: `(previousState, allOrders) → newState`. No hidden randomness beyond what's explicitly in the rules (combat accuracy rolls, random events). This makes it testable, reproducible, and auditable.
- **Server authority** — clients never resolve game logic. This prevents cheating and ensures consistency.
- **Faithful to the original** — this is exactly how Stars! worked, just with email replaced by a web client and a host program replaced by a server.

## Goals

1. **Mechanical fidelity** — replicate the depth and interlocking systems of the original Stars! game. Race design, ship customisation, the economic model, combat, minefields, stargates, mass drivers — the works.
2. **Modern platform** — runs in any browser, no installation, no Wine, no virtual machines.
3. **Native async multiplayer** — the web is the natural home for the PBEM model. Turn submission, notifications, game lobbies, player communication — all built in.
4. **Open source** — the original died because it was closed. OpenStars! stays open.

## Non-Goals (for now)

- Real-time gameplay — this is a turn-based game
- Mobile-first UI — desktop browser is the primary target (mobile can come later)
- Simplified mechanics — the depth is the point, not a problem to solve
- AI opponents — important eventually, but not in the first playable version

## Original Game Reference

- [Stars! FAQ](http://www.starsfaq.com/) — battle engine, minefields, turn order
- [Stars! AutoHost Wiki](http://wiki.starsautohost.org/) — community knowledge base
- [Official Strategy Guide](http://starsautohost.org/strategy/guidef/SSG.htm)
- [Wikipedia](https://en.wikipedia.org/wiki/Stars!)
- [MobyGames](https://www.mobygames.com/game/2021/stars/)
