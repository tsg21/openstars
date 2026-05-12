import type { PlayerState } from "../../types";
import type { ScanLevel } from "../../types/game";

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
  planet: { owner: string | null; scanLevel: ScanLevel; scanAge: number },
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
  const isOwnedByPlayer = planet.owner === playerState.player;
  const isStale = planet.scanAge > 0;

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
    dotAlpha: isStale ? 0.5 : 1.0,
    labelAlpha: showPlanetNames ? (isStale ? 0.45 : 0.65) : 0,
  };
}
