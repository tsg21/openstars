import { createContext } from "react";
import type { PlayerCommand, PlayerState } from "../types";
import type { CommandScope } from "../lib/commandScope";

export interface GameCommandsContextValue {
  basePlayerState: PlayerState | null;
  addCommand: (command: PlayerCommand) => void;
  replaceCommands: (scope: CommandScope, commands: PlayerCommand[]) => void;
}

export const GameCommandsContext = createContext<GameCommandsContextValue | null>(null);
