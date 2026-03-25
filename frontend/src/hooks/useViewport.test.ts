import { describe, it, expect } from "vitest";
import { computeFitViewport } from "./useViewport";
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

describe("computeFitViewport", () => {
  it("centres on the middle of all planets", () => {
    const vp = computeFitViewport(testGalaxy, 800, 600);
    expect(vp.centreX).toBe(50 * PARSEC);
    expect(vp.centreY).toBe(50 * PARSEC);
  });

  it("returns a positive scale", () => {
    const vp = computeFitViewport(testGalaxy, 800, 600);
    expect(vp.scale).toBeGreaterThan(0);
  });

  it("scale is constrained by the smaller canvas dimension", () => {
    // Galaxy is square (100×100 parsecs + padding), so with a wide canvas
    // height constrains, and with a square canvas both are equal.
    const vpWide = computeFitViewport(testGalaxy, 2000, 600);
    const vpSquare = computeFitViewport(testGalaxy, 600, 600);

    // Wide canvas: constrained by height (600) → same scale as square
    // because the galaxy extent + padding is the same in both axes
    expect(vpWide.scale).toBe(vpSquare.scale);

    // But a canvas that's wider AND taller gives a bigger scale
    const vpBig = computeFitViewport(testGalaxy, 2000, 1200);
    expect(vpBig.scale).toBeGreaterThan(vpWide.scale);
  });

  it("larger canvas produces larger scale", () => {
    const vpSmall = computeFitViewport(testGalaxy, 400, 300);
    const vpLarge = computeFitViewport(testGalaxy, 1600, 1200);
    expect(vpLarge.scale).toBeGreaterThan(vpSmall.scale);
  });

  it("includes 20-parsec padding", () => {
    // With only one planet, the extent is 0 so the viewport should be
    // centred on that planet and scale based on padding only
    const singlePlanet: Galaxy = {
      galaxy: { name: "Solo", size: "small", seed: 1 },
      planets: [{ id: "PL000001", name: "Lone", x: 5 * PARSEC, y: 5 * PARSEC }],
    };
    const vp = computeFitViewport(singlePlanet, 800, 800);
    expect(vp.centreX).toBe(5 * PARSEC);
    expect(vp.centreY).toBe(5 * PARSEC);
    // Scale should be canvas / (2 * 20 * PARSEC) = 800 / (40 * PARSEC)
    const expectedScale = 800 / (40 * PARSEC);
    expect(vp.scale).toBeCloseTo(expectedScale, 20);
  });
});
