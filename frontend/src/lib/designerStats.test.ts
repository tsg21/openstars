import { describe, expect, it } from "vitest";
import { computeDerivedStats } from "./designerStats";
import { quickJump5, rhinoScanner, makeHull } from "../components/designer/testFixtures";

describe("computeDerivedStats", () => {
  it("returns hull-only stats for an empty fit", () => {
    const stats = computeDerivedStats(makeHull(), [quickJump5], new Map());
    expect(stats.cost).toEqual({ resources: 20, ironium: 12, boranium: 0, germanium: 17 });
    expect(stats.mass).toBe(25);
    expect(stats.cargoCapacity).toBe(70);
  });

  it("adds component mass and cost", () => {
    const stats = computeDerivedStats(
      makeHull(),
      [quickJump5],
      new Map([[1, { componentId: "quick_jump_5", componentCount: 1 }]]),
    );
    expect(stats.mass).toBe(29);
    expect(stats.cost).toEqual({ resources: 23, ironium: 13, boranium: 0, germanium: 18 });
  });

  it("uses maximum scanner range rather than summing repeated scanners", () => {
    const stats = computeDerivedStats(
      makeHull(),
      [rhinoScanner],
      new Map([[2, { componentId: "rhino_scanner", componentCount: 2 }]]),
    );
    expect(stats.scanner).toEqual({ normal: 120, penetrating: 0 });
  });

  it("keeps cargo capacity on the hull", () => {
    const stats = computeDerivedStats(
      makeHull(),
      [quickJump5],
      new Map([[1, { componentId: "quick_jump_5", componentCount: 1 }]]),
    );
    expect(stats.cargoCapacity).toBe(70);
  });
});
