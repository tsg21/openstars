import { useState, useCallback, useMemo } from "react";
import type {
  Galaxy,
  PlayerState,
  PlayerCommands,
  PlayerCommand,
} from "../types";
import { mockGalaxy } from "../mocks/galaxy";
import { mockPlayerState } from "../mocks/playerState";

export interface MockGameState {
  /** Static galaxy data (planet positions, names, metadata). */
  galaxy: Galaxy;
  /** Current player's filtered view of the game world. */
  playerState: PlayerState;
  /** Commands queued for submission. */
  commands: PlayerCommands;
  /** Add or replace a command. For set_waypoints, replaces by fleetId. */
  setCommand: (command: PlayerCommand) => void;
  /** Clear all queued commands. */
  clearCommands: () => void;
  /** Whether there are unsaved command changes. */
  isDirty: boolean;
  /** Mark commands as submitted (resets dirty flag). */
  submit: () => void;
}

/**
 * Provides all mock game data to the UI.
 *
 * In the future, this hook will be swapped for one that fetches from the
 * real backend API. The interface should remain the same — components
 * consume MockGameState without knowing where data comes from.
 */
export function useMockGameState(): MockGameState {
  const galaxy = useMemo(() => mockGalaxy, []);
  const playerState = useMemo(() => mockPlayerState, []);

  const [commands, setCommands] = useState<PlayerCommands>({ commands: [] });
  const [isDirty, setIsDirty] = useState(false);

  const setCommand = useCallback((command: PlayerCommand) => {
    setCommands((prev) => {
      // For set_waypoints: replace existing command for the same fleet
      if (command.type === "set_waypoints") {
        const filtered = prev.commands.filter(
          (c) =>
            c.type !== "set_waypoints" || c.fleetId !== command.fleetId,
        );
        return { commands: [...filtered, command] };
      }
      return { commands: [...prev.commands, command] };
    });
    setIsDirty(true);
  }, []);

  const clearCommands = useCallback(() => {
    setCommands({ commands: [] });
    setIsDirty(false);
  }, []);

  const submit = useCallback(() => {
    // In Phase 2, this just logs to console. Real submission comes with the backend.
    console.log(
      "Turn submitted:",
      JSON.stringify(commands, null, 2),
    );
    setIsDirty(false);
  }, [commands]);

  return {
    galaxy,
    playerState,
    commands,
    setCommand,
    clearCommands,
    isDirty,
    submit,
  };
}
