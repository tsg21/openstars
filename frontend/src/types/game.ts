/**
 * OpenStars! TypeScript type definitions.
 *
 * These mirror the YAML schemas from PRDs 02, 03, 05, and 07.
 * Convention: YAML snake_case → TypeScript camelCase, except entity IDs
 * which keep their original format (e.g. "PLk8m3x2").
 */

import type { ResearchField } from "../lib/research";
import type { ShipDesignComponentAssignment } from "./designer";
import type { Race } from "./race";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** 1 light-year = 2^29 coordinate units */
export const LIGHT_YEAR = 2 ** 29; // 536_870_912

/** Galaxy size definitions (bit width per axis) */
export const GALAXY_SIZES = {
  small: 40,
  medium: 42,
  large: 44,
  huge: 46,
} as const;

export type GalaxySize = keyof typeof GALAXY_SIZES;

// ---------------------------------------------------------------------------
// Galaxy (static, from galaxy.yaml)
// ---------------------------------------------------------------------------

export interface GalaxyMetadata {
  name: string;
  size: GalaxySize;
  seed: number;
}

/** A planet's static properties (from galaxy.yaml). */
export interface GalaxyPlanet {
  id: string;
  name: string;
  x: number;
  y: number;
}

/** The full galaxy definition — immutable once generated. */
export interface Galaxy {
  galaxy: GalaxyMetadata;
  planets: GalaxyPlanet[];
}

// ---------------------------------------------------------------------------
// Global State (mutable, from global-state-T{N}.yaml)
// ---------------------------------------------------------------------------

export interface GameState {
  seed: number;
  turn: number;
  nextId: number;
}

export interface Player {
  username: string;
  name: string;
}

export interface Scanner {
  normal: number; // normal (non-penetrating) range in light-years
  penetrating: number; // penetrating range in light-years; always <= normal
}

export interface Design {
  id: string;
  owner: string;
  name: string;
  hull: string;
  components: ShipDesignComponentAssignment[];
  mass: number;
  fuelUsage: number[];
  fuelCapacity: number;
  scanner: Scanner;
  cargoCapacity: number;
  cost: DesignCost;
}

export interface DesignCost {
  resources: number;
  minerals: Minerals;
}

/** Mutable planet state (ownership, population). */
export interface PlanetState {
  id: string;
  owner: string | null;
  population: number;
}

export interface Position {
  x: number;
  y: number;
}

export interface Cargo {
  ironium: number;
  boranium: number;
  germanium: number;
  colonists: number;
}

export interface CargoOrder {
  action:
    | "load_all"
    | "load_amount"
    | "load_up_to"
    | "unload_all"
    | "unload_amount"
    | "unload_but";
  cargoType: "ironium" | "boranium" | "germanium" | "colonists" | null;
  amount?: number | null;
}

export interface WaypointTask {
  type: "transport" | "transfer" | "colonise";
  orders: CargoOrder[];
  fleetId?: string | null;
}

export interface Waypoint {
  x: number;
  y: number;
  warp: number;
  task?: WaypointTask | null;
}

export interface FleetComposition {
  designId: string;
  count: number;
}

export interface Fleet {
  id: string;
  owner: string;
  position: Position;
  composition: FleetComposition[];
  waypoints: Position[];
}

// ---------------------------------------------------------------------------
// Player State (filtered view sent to client — PRD 03)
// ---------------------------------------------------------------------------

/**
 * A planet as seen by the player — merges static galaxy data with mutable
 * state. Fields may be absent for planets only partially visible (scanner
 * range but not owned).
 */
export type ScanLevel = "none" | "basic" | "detailed";

export interface Minerals {
  ironium: number;
  boranium: number;
  germanium: number;
}

export type StarbaseType = "orbital_fort" | "space_station";
export type ProductionItemType = "mine" | "factory" | "starbase" | "ship" | "planetary_scanner";

export interface ProductionProgress {
  resourcesSpent: number;
  mineralsSpent: Minerals;
}

export interface PlayerProductionQueueItem {
  id: string;
  itemType: ProductionItemType;
  targetType?: StarbaseType | null;
  designId?: string | null;
  quantity: number;
  progress: ProductionProgress;
}

export interface PlayerPlanetStarbaseState {
  type: StarbaseType;
  canBuildShips: boolean;
}

export interface PlayerPlanetStarbaseSummary {
  present: boolean;
  type?: StarbaseType | null;
  canBuildShips?: boolean | null;
}

export interface PlayerPlanetScannerState {
  installed: boolean;
  name: string;
  normal: number;
  penetrating: number;
}

export interface PlayerPlanetScannerSummary {
  installed: boolean;
}

export interface Habitability {
  gravity: number;
  temperature: number;
  radiation: number;
}


export interface PlayerStateResearch {
  levels: Record<ResearchField, number>;
  progress: Record<ResearchField, number>;
  currentField: ResearchField;
  nextField: ResearchField | null;
  allocationPercent: number;
  remainingCost: Record<ResearchField, number>;
  reservableResourcesThisTurn: number;
}

export interface PlayerPlanet {
  id: string;
  name: string;
  x: number;
  y: number;
  owner?: string | null;
  population?: number | null;
  scanLevel: ScanLevel;
  scanAge: number;
  mines?: number | null;
  factories?: number | null;
  minerals?: Minerals | null;
  concentrations?: Minerals | null;
  resources?: number | null;
  miningRate?: Minerals | null;
  productionQueue?: PlayerProductionQueueItem[] | null;
  habitability?: Habitability | null;
  maxPopulation?: number | null;
  popGrowth?: number | null;
  starbase?: PlayerPlanetStarbaseState | PlayerPlanetStarbaseSummary | null;
  scanner?: PlayerPlanetScannerState | PlayerPlanetScannerSummary | null;
  contributeOnlyLeftoverToResearch?: boolean | null;
}

/** A fleet as seen by the player. Enemy fleets have limited info. */
export interface PlayerFleet {
  id: string;
  owner: string;
  name?: string | null;
  position: Position;
  /** Own fleets have full composition; enemy fleets may have partial or none. */
  composition?: FleetComposition[];
  /** Only present for own fleets. */
  waypoints?: Waypoint[];
  /** Whether the fleet repeats its route. Only present for own fleets. */
  repeat?: boolean | null;
  /** Current cargo. Only present for own fleets. */
  cargo?: Cargo | null;
  /** Maximum cargo capacity. Only present for own fleets. */
  cargoCapacity?: number | null;
  /** Current fuel in mg. Only present for own fleets. */
  fuel?: number | null;
  /** Total fuel capacity in mg across all ships. Only present for own fleets. */
  fuelCapacity?: number | null;
  /** Direction of travel in degrees (0=north, clockwise). */
  bearing?: number | null;
}

// ---------------------------------------------------------------------------
// Turn Events (PRD 03)
// ---------------------------------------------------------------------------

export interface GameEvent {
  owner: string;
  sourceId: string | null;
  code: string;
  values: Array<string | number>;
}

// ---------------------------------------------------------------------------
// Player State (complete package the UI receives)
// ---------------------------------------------------------------------------

export interface PlayerState {
  player: string;
  turn: number;
  race?: Race | null;
  planets: PlayerPlanet[];
  fleets: PlayerFleet[];
  designs: Design[];
  events: GameEvent[];
  research?: PlayerStateResearch | null;
}

// ---------------------------------------------------------------------------
// Player Commands (PRD 07)
// ---------------------------------------------------------------------------

export interface SetWaypointsCommand {
  type: "set_waypoints";
  fleetId: string;
  waypoints: Waypoint[];
  repeat?: boolean | null;
}

export interface RenameFleetCommand {
  type: "rename_fleet";
  fleetId: string;
  name: string;
}


export interface MergeSplitFleetEntry {
  fleetId: string;
  name?: string | null;
  ships: FleetComposition[];
}

export interface MergeSplitFleetsCommand {
  type: "merge_split_fleets";
  fleets: MergeSplitFleetEntry[];
}


export interface SetResearchCommand {
  type: "set_research";
  currentField?: ResearchField;
  nextField?: ResearchField | null;
  allocationPercent?: number;
}

export interface SetPlanetProductionModeCommand {
  type: "set_planet_production_mode";
  planetId: string;
  contributeOnlyLeftoverToResearch: boolean;
}

export interface AddProductionItemCommand {
  type: "add_production_item";
  planetId: string;
  itemType: ProductionItemType;
  targetType?: StarbaseType | null;
  designId?: string | null;
  quantity: number;
  insertAfterItemId?: string | null;
}

export interface MoveProductionItemCommand {
  type: "move_production_item";
  planetId: string;
  itemId: string;
  insertAfterItemId?: string | null;
}

export interface RemoveProductionItemCommand {
  type: "remove_production_item";
  planetId: string;
  itemId: string;
  quantity: number;
}

export interface ClearProductionQueueCommand {
  type: "clear_production_queue";
  planetId: string;
}

export interface SelectRaceCommand {
  type: "select_race";
  predefinedId?: string | null;
  race?: Race | null;
}

export type PlayerCommand =
  | SetWaypointsCommand
  | RenameFleetCommand
  | MergeSplitFleetsCommand
  | SetResearchCommand
  | SetPlanetProductionModeCommand
  | AddProductionItemCommand
  | MoveProductionItemCommand
  | RemoveProductionItemCommand
  | ClearProductionQueueCommand
  | SelectRaceCommand;

export interface PlayerCommands {
  commands: PlayerCommand[];
}

export type WaypointDraftState = {
  command: SetWaypointsCommand;
  dirty: boolean;
  validationErrors: Record<string, string>;
};
