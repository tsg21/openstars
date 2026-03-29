import { describe, it, expect } from "vitest";
import { computeInitialCentre, FIXED_SCALE } from "./useViewport";
import type { Galaxy } from "../types";
import { PARSEC } from "../types";

// A minimal test galaxy
const testGalaxy: Galaxy = {
  galaxy: { name: "Test", size: "small", seed: 1 },
  planets: [
    { id: "PL000001", name: "A", x: 0, y: 0 },
    { id: "PL000002", name: "B", x: 100 * PARSEC, y: 0 },
    { id: "PL000003", name: "C", x: 0, y: 100 * PARSEC },
    { id: "PL000004", name: "D", x: 100 * PARSEC, y: 100 * PARSEC },
  ],
};

describe("computeInitialCentre", () => {
  it("centres on a specific planet when ID is provided", () => {
    const centre = computeInitialCentre(testGalaxy, "PL000002");
    expect(centre.centreX).toBe(100 * PARSEC);
    expect(centre.centreY).toBe(0);
  });

  it("falls back to galaxy centroid when no planet ID given", () => {
    const centre = computeInitialCentre(testGalaxy);
    expect(centre.centreX).toBe(50 * PARSEC);
    expect(centre.centreY).toBe(50 * PARSEC);
  });

  it("falls back to galaxy centroid when planet ID not found", () => {
    const centre = computeInitialCentre(testGalaxy, "PL_MISSING");
    expect(centre.centreX).toBe(50 * PARSEC);
    expect(centre.centreY).toBe(50 * PARSEC);
  });

  it("returns origin for empty galaxy", () => {
    const emptyGalaxy: Galaxy = {
      galaxy: { name: "Empty", size: "small", seed: 1 },
      planets: [],
    };
    const centre = computeInitialCentre(emptyGalaxy);
    expect(centre.centreX).toBe(0);
    expect(centre.centreY).toBe(0);
  });
});

describe("FIXED_SCALE", () => {
  it("is a positive number", () => {
    expect(FIXED_SCALE).toBeGreaterThan(0);
  });

  it("shows ~400 parsecs across 1000px", () => {
    const parsecsIn1000px = 1000 / (FIXED_SCALE * PARSEC);
    expect(parsecsIn1000px).toBeCloseTo(400, 0);
  });
});
