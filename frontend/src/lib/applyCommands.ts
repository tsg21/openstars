import type { PlayerState, PlayerCommand } from "../types";

/**
 * Applies pending commands to a base player state, creating a "working view"
 * of the game state that includes local changes not yet submitted to the server.
 *
 * This is a pure function — it does not mutate the input state.
 *
 * @param playerState Base player state from the turn file
 * @param commands Array of pending commands to apply
 * @returns New player state with commands applied
 */
export function applyCommandsToPlayerState(
  playerState: PlayerState,
  commands: PlayerCommand[]
): PlayerState {
  // Clone the player state (shallow clone, but we'll replace modified arrays)
  const merged: PlayerState = {
    ...playerState,
    // Deep clone the fleets array since we'll be modifying fleet objects
    fleets: playerState.fleets.map((fleet) => ({ ...fleet })),
  };

  // Apply each command to the merged state
  for (const cmd of commands) {
    if (cmd.type === "set_waypoints") {
      const fleetIndex = merged.fleets.findIndex((f) => f.id === cmd.fleetId);
      if (fleetIndex !== -1) {
        merged.fleets[fleetIndex] = {
          ...merged.fleets[fleetIndex],
          waypoints: cmd.waypoints,
        };
      }
    }
    // Future command types will be handled here (e.g., planet production, fleet splits)
  }

  return merged;
}
