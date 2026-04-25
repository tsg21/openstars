import type { PlayerCommand } from "../types";

export type CommandScope =
  | { kind: "fleet"; id: string }
  | { kind: "planet"; id: string }
  | { kind: "research" };

export function commandMatchesScope(command: PlayerCommand, scope: CommandScope): boolean {
  if (scope.kind === "fleet") {
    return "fleetId" in command && command.fleetId === scope.id;
  }

  if (scope.kind === "planet") {
    return "planetId" in command && command.planetId === scope.id;
  }

  return command.type === "set_research";
}
