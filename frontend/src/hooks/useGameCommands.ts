import { useContext } from "react";
import { GameCommandsContext, type GameCommandsContextValue } from "../contexts/gameCommandsContext";

export function useGameCommands(): GameCommandsContextValue {
  const context = useContext(GameCommandsContext);
  if (!context) {
    throw new Error("useGameCommands must be used within a GameCommandsProvider");
  }
  return context;
}
