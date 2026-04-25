import { describe, expect, it } from "vitest";
import {
  RESEARCH_FIELDS,
  RESEARCH_FIELD_COLOURS,
  RESEARCH_FIELD_LABELS,
} from "./research";

describe("research constants", () => {
  it("contains canonical fields in order", () => {
    expect(RESEARCH_FIELDS).toEqual([
      "energy",
      "weapons",
      "propulsion",
      "construction",
      "electronics",
      "biotechnology",
    ]);
  });

  it("contains labels for all fields", () => {
    for (const field of RESEARCH_FIELDS) {
      expect(RESEARCH_FIELD_LABELS[field]).toBeTruthy();
    }
  });

  it("contains colours for all fields", () => {
    for (const field of RESEARCH_FIELDS) {
      expect(RESEARCH_FIELD_COLOURS[field]).toBe(`var(--color-research-${field})`);
    }
  });
});
