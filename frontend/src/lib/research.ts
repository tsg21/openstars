export const RESEARCH_FIELDS = [
  "energy",
  "weapons",
  "propulsion",
  "construction",
  "electronics",
  "biotechnology",
] as const;

export type ResearchField = (typeof RESEARCH_FIELDS)[number];

export const RESEARCH_MAX_LEVEL = 26;

export const RESEARCH_FIELD_LABELS: Record<ResearchField, string> = {
  energy: "Energy",
  weapons: "Weapons",
  propulsion: "Propulsion",
  construction: "Construction",
  electronics: "Electronics",
  biotechnology: "Biotechnology",
};

export const RESEARCH_FIELD_COLOURS: Record<ResearchField, string> = {
  energy: "#fbbf24",
  weapons: "#ef4444",
  propulsion: "#3b82f6",
  construction: "#a3a3a3",
  electronics: "#22d3ee",
  biotechnology: "#22c55e",
};
