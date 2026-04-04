# PRD 63 — Fleet Detail Panel

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Fleet View

Fleets in orbit around a planet are selected via the planet detail panel, not by clicking directly on the map. Once selected, the fleet detail panel behaves identically to a deep-space fleet.

When a fleet is selected:

**Own fleet:**
- Fleet name as the primary title
- Rename button aligned to the right of the fleet name
- Fleet ID as secondary metadata only (for debugging/support use, not the primary label)
- Current position (planet name if at a planet, or coordinates)
- Composition — list of ship designs and counts
- Speed — effective speed (slowest design)
- Waypoint list — ordered destinations with:
  - Planet name or coordinates
  - Estimated turns to arrival
  - Remove button per waypoint
  - Drag to reorder (future nicety)
- *(Future: fuel, cargo, battle plan)*

**Other player's fleet (in scanner range):**
- Fleet owner
- No fleet name field is shown; enemy fleet names are hidden by fog of war
- Position
- Bearing — direction of travel shown as an angle or compass direction (e.g. "Heading NE"), derived from the `bearing` field (PRD 11). Null if stationary.
- *(Future: estimated composition based on scanner quality)*

## Fleet Naming

Fleet names are player-facing labels. For owned fleets, the UI should use the fleet name anywhere the player is identifying or choosing between their own fleets. Raw fleet IDs remain available in the data model and may appear in low-emphasis metadata or diagnostics, but should not be the default visible label in normal play.

New fleets start with an auto-generated name from the backend (for example `Fleet #1`), and the player may rename them at any time during the command phase.

### Rename Interaction

- The fleet detail header shows the fleet name on the left and a `Rename` button on the right.
- Clicking `Rename` switches the title area into an inline editing state.
- The edit control is prefilled with the current fleet name.
- `Enter` saves, `Escape` cancels, and clicking away also cancels unless the player explicitly confirms save.
- Saving issues a `rename_fleet` command for that fleet; the rename is treated like any other turn command and is not authoritative until the server accepts the submitted turn.
- While unsaved, the edited name appears immediately in the fleet detail panel and other local UI surfaces that reference the same owned fleet.
- If the server rejects the command, the panel keeps the player's draft value visible alongside an inline error so they can correct and resubmit.

## Waypoint Editor

The waypoint editor is embedded in the fleet detail panel. It shows:

```
┌─────────────────────────────┐
│  Fleet #1      [Rename]     │
│  ID: FL9qb7w1               │
│  Scout × 1  |  Speed: 6 pc │
│                             │
│  Waypoints:                 │
│  ① Sol (current)            │
│  ② Alpha Centauri  ~14 turns│
│  ③ Sirius           ~8 turns│
│                             │
│  [Clear All]                │
│                             │
│  Click the map to add       │
│  waypoints.                 │
└─────────────────────────────┘
```

Estimated turns are calculated client-side from distance and fleet speed — this is display-only, not authoritative. The server resolves actual movement.

## Turn Flow

The player's session within a single turn:

1. **Load** — game opens, player state is fetched, map renders
2. **Review** — player sees updated positions, reads events ("Fleet arrived at Alpha Centauri"), inspects planets/fleets
3. **Command** — player selects fleets, sets/adjusts waypoints. Changes are tracked locally as unsaved commands.
4. **Submit** — player clicks Submit Turn. Commands are sent to the server. Button changes to "Submitted ✓" state. Player can resubmit if they change their mind (PRD 03).
5. **Wait** — top bar shows who hasn't submitted yet. After a player submits, the client polls a lightweight turn-status endpoint every 10 seconds to detect when the next turn has been generated without re-fetching full turn data. When all players submit (or deadline passes), the server resolves the turn.
6. **Next turn** — new player state arrives. Events populate. Map updates. Back to step 2.
