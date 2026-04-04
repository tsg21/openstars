/**
 * OpenStars! TypeScript type definitions.
 *
 * These mirror the YAML schemas from PRDs 02, 03, 05, and 07.
 * Convention: YAML snake_case → TypeScript camelCase, except entity IDs
 * which keep their original format (e.g. "PLk8m3x2").
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** 1 parsec = 2^29 coordinate units */
export const PARSEC = 2 ** 29; // 536_870_912

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
  normal: number; // normal (non-penetrating) range in parsecs
  penetrating: number; // penetrating range in parsecs; always <= normal
}

export interface Design {
  id: string;
  owner: string;
  name: string;
  hull: string;
  speed: number;
  scanner: Scanner;
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

export type ProductionItemType = "mine" | "factory";

export interface ProductionProgress {
  resourcesSpent: number;
  mineralsSpent: Minerals;
}

export interface PlayerProductionQueueItem {
  id: string;
  itemType: ProductionItemType;
  quantity: number;
  progress: ProductionProgress;
}

export interface Habitability {
  gravity: number;
  temperature: number;
  radiation: number;
}

export interface PlayerPlanet {
  id: string;
  name: string;
  x: number;
  y: number;
  owner?: string | null;
  population?: number | null;
  scanLevel: ScanLevel;
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
  /** Direction of travel in degrees (0=north, clockwise). Only for detected enemy fleets. */
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
  planets: PlayerPlanet[];
  fleets: PlayerFleet[];
  designs: Design[];
  events: GameEvent[];
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

export interface AddProductionItemCommand {
  type: "add_production_item";
  planetId: string;
  itemType: ProductionItemType;
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

export type PlayerCommand =
  | SetWaypointsCommand
  | RenameFleetCommand
  | AddProductionItemCommand
  | MoveProductionItemCommand
  | RemoveProductionItemCommand
  | ClearProductionQueueCommand;

export interface PlayerCommands {
  commands: PlayerCommand[];
}

export type WaypointDraftState = {
  command: SetWaypointsCommand;
  dirty: boolean;
  validationErrors: Record<string, string>;
};
