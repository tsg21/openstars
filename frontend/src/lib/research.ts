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
  energy: "var(--color-research-energy)",
  weapons: "var(--color-research-weapons)",
  propulsion: "var(--color-research-propulsion)",
  construction: "var(--color-research-construction)",
  electronics: "var(--color-research-electronics)",
  biotechnology: "var(--color-research-biotechnology)",
};
