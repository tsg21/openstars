import type { PlayerCommand } from "../types";

export type CommandScope =
  | { kind: "fleet"; id: string }
  | { kind: "planet"; id: string }
  | { kind: "research" }
  | { kind: "race" };

export function commandMatchesScope(command: PlayerCommand, scope: CommandScope): boolean {
  if (scope.kind === "fleet") {
    return "fleetId" in command && command.fleetId === scope.id;
  }

  if (scope.kind === "planet") {
    return "planetId" in command && command.planetId === scope.id;
  }

  if (scope.kind === "research") {
    return command.type === "set_research";
  }

  return command.type === "select_race";
}
