import type { ResearchField } from "../lib/research";

export type Prt = "JOAT" | "HE" | "SS" | "WM" | "CA" | "IS" | "SD" | "PP" | "IT" | "AR";

export type Lrt =
  | "IFE"
  | "TT"
  | "ARM"
  | "ISB"
  | "GR"
  | "UR"
  | "MA"
  | "NRSE"
  | "CE"
  | "OBRM"
  | "NAS"
  | "LSP"
  | "BET"
  | "RS";

export type ResearchCostProfile = "cheap" | "standard" | "expensive";
export type LeftoverBonusKind = "surface_minerals" | "mines" | "factories" | "defenses" | "concentrations";

export interface RaceHabitabilityFactor {
  immune: boolean;
  range: [number, number];
}

export interface RaceHabitability {
  gravity: RaceHabitabilityFactor;
  temperature: RaceHabitabilityFactor;
  radiation: RaceHabitabilityFactor;
}

export interface RaceEconomy {
  colonistsPerResource: number;
  factoryOutputPer10: number;
  factoryCostResources: number;
  factoriesPer10kColonists: number;
  factoriesSaveGermanium: boolean;
  mineOutputPer10: number;
  mineCostResources: number;
  minesPer10kColonists: number;
  arResourceDivisor: number;
}

export interface RaceResearch {
  fieldProfile: Record<ResearchField, ResearchCostProfile>;
  startAtTech3: boolean;
}

export interface LeftoverBonus {
  kind: LeftoverBonusKind;
  points: number;
}

export interface Race {
  name: string;
  pluralName: string;
  emblem: number;
  prt: Prt;
  lrts: Lrt[];
  habitability: RaceHabitability;
  maxGrowthRate: number;
  economy: RaceEconomy;
  research: RaceResearch;
  leftoverBonus: LeftoverBonus | null;
}

export interface RaceCostBreakdown {
  prt: number;
  lrts: number;
  habitability: number;
  growth: number;
  economy: number;
  research: number;
  leftover: number;
  total: number;
  pointsLeft: number;
}

export interface RacePreviewResponse {
  costBreakdown: RaceCostBreakdown;
  pointsLeft: number;
}

export interface SavedRaceResponse {
  race: Race | null;
  costBreakdown: RaceCostBreakdown | null;
}

export interface PredefinedRace {
  id: string;
  race: Race;
}

export const DEFAULT_RACE: Race = {
  name: "Humanoid",
  pluralName: "Humanoids",
  emblem: 0,
  prt: "JOAT",
  lrts: [],
  habitability: {
    gravity: { immune: false, range: [15, 85] },
    temperature: { immune: false, range: [15, 85] },
    radiation: { immune: false, range: [15, 85] },
  },
  maxGrowthRate: 15,
  economy: {
    colonistsPerResource: 1000,
    factoryOutputPer10: 10,
    factoryCostResources: 10,
    factoriesPer10kColonists: 10,
    factoriesSaveGermanium: false,
    mineOutputPer10: 10,
    mineCostResources: 5,
    minesPer10kColonists: 10,
    arResourceDivisor: 10,
  },
  research: {
    fieldProfile: {
      energy: "standard",
      weapons: "standard",
      propulsion: "standard",
      construction: "standard",
      electronics: "standard",
      biotechnology: "standard",
    },
    startAtTech3: false,
  },
  leftoverBonus: null,
};

export const HAB_DISPLAY: Record<keyof RaceHabitability, (value: number) => string> = {
  gravity: (value) => `${(0.22 * Math.pow(4.4 / 0.22, value / 100)).toFixed(2)}g`,
  temperature: (value) => {
    const temp = Math.round(-140 + value * 2.8);
    return `${temp >= 0 ? "+" : ""}${temp} C`;
  },
  radiation: (value) => `${Math.round(value)} mR`,
};
