export type ComponentType =
  | "engine"
  | "scanner"
  | "weapon"
  | "shield"
  | "armour"
  | "general_purpose";

export interface ComponentCost {
  resources: number;
  ironium: number;
  boranium: number;
  germanium: number;
}

export interface DesignerComponentEntry {
  id: string;
  name: string;
  componentType: ComponentType;
  cost: ComponentCost;
  mass: number;
  componentCountMin: number;
  componentCountMax: number | null;
  engine?: { maxWarp: number; isRamscoop: boolean };
  scanner?: { normal: number; penetrating: number };
  weapon?: { range: number; damage: number; initiative: number };
  shield?: { shieldPoints: number };
  armour?: { armourPoints: number };
  generalPurpose?: { cargoCapacity: number };
}

export type SlotCategory = ComponentType;

export interface HullSlotDefinition {
  slotId: string;
  slotCategories: SlotCategory[];
  capacity: number;
  required: boolean;
}

export interface HullDefinition {
  id: string;
  name: string;
  domain: "ship" | "starbase";
  engineRequiredSlots: number;
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
  speed: number;
  scanner?: { normal: number; penetrating: number };
  cargoCapacity?: number;
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
  slotId: string;
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
