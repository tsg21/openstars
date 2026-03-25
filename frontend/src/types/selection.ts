/** Represents what the player has selected on the galaxy map. */
export type Selection =
  | { kind: "planet"; id: string }
  | { kind: "fleet"; id: string }
  | null;
