import type { PlayerState } from "../types";
import type { ScanLevel } from "../types/game";

const PLANET_RADIUS = 4;

function planetColour(
  owner: string | null,
  currentPlayer: string,
  selfColor: string,
  enemyColor: string,
  uncolonisedColor: string,
): string {
  if (owner === currentPlayer) return selfColor;
  if (owner !== null) return enemyColor;
  return uncolonisedColor;
}

export function getPlanetRenderStyle(
  planet: { owner: string | null; scanLevel: ScanLevel },
  playerState: Pick<PlayerState, "player">,
  colors: {
    self: string;
    selfEdge: string;
    enemy: string;
    uncolonised: string;
  },
  showPlanetNames = true,
): {
  colour: string;
  edgeColour: string | null;
  dotRadius: number;
  dotAlpha: number;
  labelAlpha: number;
} {
  void planet.scanLevel;
  const isOwnedByPlayer = planet.owner === playerState.player;

  return {
    colour: planetColour(
      planet.owner,
      playerState.player,
      colors.self,
      colors.enemy,
      colors.uncolonised,
    ),
    edgeColour: isOwnedByPlayer ? colors.selfEdge : null,
    dotRadius: PLANET_RADIUS,
    dotAlpha: 1.0,
    labelAlpha: showPlanetNames ? 0.65 : 0,
  };
}
