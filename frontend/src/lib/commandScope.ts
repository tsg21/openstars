import type { PlayerCommand } from "../types";

export type CommandScope =
  | { kind: "fleet"; id: string }
  | { kind: "planet"; id: string };

export function commandMatchesScope(command: PlayerCommand, scope: CommandScope): boolean {
  if (scope.kind === "fleet") {
    return "fleetId" in command && command.fleetId === scope.id;
  }

  return "planetId" in command && command.planetId === scope.id;
}
