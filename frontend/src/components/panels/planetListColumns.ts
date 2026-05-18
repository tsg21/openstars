import type { ReactNode } from "react";
import type { PlayerPlanet, PlayerPlanetStarbaseState } from "../../types";
import type { PlanetListColumn } from "./PlanetList";
import { describeQueueItem, PRODUCTION_ITEM_LABELS } from "../../lib/productionSummary";
import type { DesignSummary } from "../../types/designer";

function starbaseLabel(planet: PlayerPlanet): string {
  if (!planet.starbase) return "None";
  const sb = planet.starbase;
  // Full state (own planet)
  if ("canBuildShips" in sb && sb.canBuildShips != null) {
    return (sb as PlayerPlanetStarbaseState).canBuildShips ? "Dock (+ships)" : "Dock";
  }
  return "Dock";
}

function starbaseRank(planet: PlayerPlanet): number {
  if (!planet.starbase) return 0;
  const sb = planet.starbase;
  if ("canBuildShips" in sb && (sb as PlayerPlanetStarbaseState).canBuildShips) return 2;
  return 1;
}

export const nameColumn: PlanetListColumn = {
  id: "name",
  header: "Name",
  sortable: true,
  sortValue: (p) => p.name,
  render: (p) => p.name,
};

export function ownerColumn(currentPlayer: string): PlanetListColumn {
  return {
    id: "owner",
    header: "Owner",
    sortable: true,
    sortValue: (p) => {
      if (p.owner === currentPlayer) return "\x00"; // sorts before any letter
      return p.owner ?? "Uncolonised";
    },
    render: (p): ReactNode => {
      if (p.owner === currentPlayer) return "You";
      return p.owner ?? "Uncolonised";
    },
  };
}

export const populationColumn: PlanetListColumn = {
  id: "population",
  header: "Pop",
  align: "right",
  sortable: true,
  sortValue: (p) => p.population ?? null,
  render: (p) => (p.population != null ? p.population.toLocaleString() : "—"),
};

export const resourcesColumn: PlanetListColumn = {
  id: "resources",
  header: "Res/turn",
  align: "right",
  sortable: true,
  sortValue: (p) => p.resources ?? null,
  render: (p) => (p.resources != null ? String(p.resources) : "—"),
};

export const minesColumn: PlanetListColumn = {
  id: "mines",
  header: "Mines",
  align: "right",
  sortable: true,
  sortValue: (p) => p.mines ?? null,
  render: (p) => (p.mines != null ? String(p.mines) : "—"),
};

export const factoriesColumn: PlanetListColumn = {
  id: "factories",
  header: "Factories",
  align: "right",
  sortable: true,
  sortValue: (p) => p.factories ?? null,
  render: (p) => (p.factories != null ? String(p.factories) : "—"),
};

export const starbaseColumn: PlanetListColumn = {
  id: "starbase",
  header: "Starbase",
  sortable: true,
  sortValue: (p) => starbaseRank(p),
  render: (p) => starbaseLabel(p),
};

export function queueHeadColumn(shipDesigns: DesignSummary[]): PlanetListColumn {
  return {
    id: "queue_head",
    header: "Building",
    sortable: true,
    sortValue: (p) => {
      const q = p.productionQueue;
      if (!q || q.length === 0) return null;
      return describeQueueItem(q[0], shipDesigns);
    },
    render: (p): ReactNode => {
      const q = p.productionQueue;
      if (!q || q.length === 0) return "—";
      return describeQueueItem(q[0], shipDesigns);
    },
  };
}

export const queueLengthColumn: PlanetListColumn = {
  id: "queue_length",
  header: "Q",
  align: "right",
  sortable: true,
  sortValue: (p) => p.productionQueue?.length ?? 0,
  render: (p) => String(p.productionQueue?.length ?? 0),
};

export const scannerColumn: PlanetListColumn = {
  id: "scanner",
  header: "Scanner",
  sortable: true,
  sortValue: (p) => (p.scanner?.installed ? 1 : 0),
  render: (p) => (p.scanner?.installed ? "Yes" : "—"),
};

// Re-export for convenience in tests that want the full label map
export { PRODUCTION_ITEM_LABELS };
