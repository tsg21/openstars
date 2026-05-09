export type ComponentType =
  | "engine"
  | "scanner"
  | "weapon"
  | "torpedo"
  | "shield"
  | "armour"
  | "electrical"
  | "mechanical"
  | "bomb"
  | "mine_layer"
  | "robot_miner"
  | "planetary";

export interface ComponentCost {
  resources: number;
  ironium: number;
  boranium: number;
  germanium: number;
}

export interface TechRequirements {
  energy: number;
  weapons: number;
  propulsion: number;
  construction: number;
  electronics: number;
  biotechnology: number;
}

export interface DesignerComponentEntry {
  id: string;
  name: string;
  componentType: ComponentType;
  cost: ComponentCost;
  mass: number;
  techRequirements?: TechRequirements;
  engine?: { fuelUsage: number[]; isRamscoop: boolean };
  scanner?: { normal: number; penetrating: number };
  weapon?: { range: number; damage: number; initiative: number };
  shield?: { shieldPoints: number };
  armour?: { armourPoints: number };
  electrical?: { ability: number };
  mechanical?: { ability: number };
  torpedo?: { range: number; initiative: number; damage: number; hitChance: number };
  planetary?: { ability: number };
}

export type SlotCategory = ComponentType | "general_purpose" | "orbital";

export interface GridPosition {
  x: number;
  y: number;
}

export interface GridSize {
  w: number;
  h: number;
}

export interface GridRect extends GridPosition, GridSize {}

export interface HullSlotDefinition {
  slotNumber: number;
  slotCategories: SlotCategory[];
  capacity: number;
  required: boolean;
  position?: GridPosition;
  size?: GridSize;
}

export interface HullDefinition {
  id: string;
  name: string;
  cost: ComponentCost;
  mass: number;
  techRequirements?: TechRequirements;
  domain: "ship" | "starbase";
  fuelCapacity: number;
  cargoCapacity: number;
  dockCapacity: number;
  armourPoints: number;
  initiative: number;
  layoutGrid?: GridSize;
  cargoLayout?: GridRect;
  dockLayout?: GridRect;
  slots: HullSlotDefinition[];
}

export interface DesignsReferenceDataResponse {
  domain: "ship" | "starbase";
  hulls: HullDefinition[];
  components: DesignerComponentEntry[];
}

export interface DesignSummary {
  id: string;
  name: string;
  hull: string;
  fuelCapacity: number;
  cost: {
    resources: number;
    minerals: {
      ironium: number;
      boranium: number;
      germanium: number;
    };
  };
}

export interface DesignSummaryListResponse {
  designs: DesignSummary[];
}

export interface ShipDesignComponentAssignment {
  slotNumber: number;
  componentId: string;
  componentCount: number;
}

export interface CreateDesignRequest {
  name: string;
  hull: string;
  components: ShipDesignComponentAssignment[];
}

export type DesignerReferenceData = DesignsReferenceDataResponse;
export type DesignerReferenceHull = HullDefinition;
export type DesignerCreateDesignComponent = ShipDesignComponentAssignment;
export type DesignerCreateDesignRequest = CreateDesignRequest;
export type DesignerCreateDesignResponse = { design: import("./game").Design };
export type DesignerDesignDetailResponse = { design: import("./game").Design };
export type DesignerDesignSummary = DesignSummary;
