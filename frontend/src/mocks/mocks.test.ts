import { describe, it, expect } from "vitest";
import { mockGalaxy } from "./galaxy";
import { mockPlayerState } from "./playerState";
import { GALAXY_SIZES, PARSEC } from "../types";

// Entity ID format: 2 uppercase letters + 6 lowercase alphanumeric
const ID_PATTERN = /^[A-Z]{2}[a-z0-9]{6}$/;

describe("mock galaxy", () => {
  it("has valid galaxy metadata", () => {
    expect(mockGalaxy.galaxy.name).toBeTruthy();
    expect(mockGalaxy.galaxy.size).toBe("small");
    expect(mockGalaxy.galaxy.seed).toBeTypeOf("number");
  });

  it("has ~20 planets", () => {
    expect(mockGalaxy.planets.length).toBe(20);
  });

  it("all planet IDs have PL prefix and valid format", () => {
    for (const p of mockGalaxy.planets) {
      expect(p.id).toMatch(ID_PATTERN);
      expect(p.id.slice(0, 2)).toBe("PL");
    }
  });

  it("all planet IDs are unique", () => {
    const ids = mockGalaxy.planets.map((p) => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("all planet names are unique", () => {
    const names = mockGalaxy.planets.map((p) => p.name);
    expect(new Set(names).size).toBe(names.length);
  });

  it("all coordinates are within small galaxy range", () => {
    const maxCoord = 2 ** GALAXY_SIZES.small - 1;
    for (const p of mockGalaxy.planets) {
      expect(p.x).toBeGreaterThanOrEqual(0);
      expect(p.x).toBeLessThanOrEqual(maxCoord);
      expect(p.y).toBeGreaterThanOrEqual(0);
      expect(p.y).toBeLessThanOrEqual(maxCoord);
    }
  });

  it("all coordinates are within the placement region (middle 50%)", () => {
    const max = 2 ** GALAXY_SIZES.small - 1;
    const low = max * 0.25;
    const high = max * 0.75;
    for (const p of mockGalaxy.planets) {
      expect(p.x).toBeGreaterThanOrEqual(low);
      expect(p.x).toBeLessThanOrEqual(high);
      expect(p.y).toBeGreaterThanOrEqual(low);
      expect(p.y).toBeLessThanOrEqual(high);
    }
  });

  it("no two planets share coordinates", () => {
    const coords = mockGalaxy.planets.map((p) => `${p.x},${p.y}`);
    expect(new Set(coords).size).toBe(coords.length);
  });
});

describe("mock player state", () => {
  it("is for player tim at turn 3", () => {
    expect(mockPlayerState.player).toBe("tim");
    expect(mockPlayerState.turn).toBe(3);
  });

  it("all planet IDs reference valid galaxy planets", () => {
    const galaxyIds = new Set(mockGalaxy.planets.map((p) => p.id));
    for (const p of mockPlayerState.planets) {
      expect(galaxyIds.has(p.id)).toBe(true);
    }
  });

  it("planet coordinates match galaxy definition", () => {
    for (const sp of mockPlayerState.planets) {
      const gp = mockGalaxy.planets.find((p) => p.id === sp.id);
      expect(gp).toBeDefined();
      expect(sp.x).toBe(gp!.x);
      expect(sp.y).toBe(gp!.y);
    }
  });

  it("all fleet IDs have FL prefix and valid format", () => {
    for (const f of mockPlayerState.fleets) {
      expect(f.id).toMatch(ID_PATTERN);
      expect(f.id.slice(0, 2)).toBe("FL");
    }
  });

  it("all design IDs have DE prefix and valid format", () => {
    for (const d of mockPlayerState.designs) {
      expect(d.id).toMatch(ID_PATTERN);
      expect(d.id.slice(0, 2)).toBe("DE");
    }
  });

  it("fleet compositions reference valid designs", () => {
    const designIds = new Set(mockPlayerState.designs.map((d) => d.id));
    for (const f of mockPlayerState.fleets) {
      if (f.composition) {
        for (const c of f.composition) {
          expect(designIds.has(c.designId)).toBe(true);
        }
      }
    }
  });

  it("Tim owns at least 2 planets", () => {
    const owned = mockPlayerState.planets.filter((p) => p.owner === "tim");
    expect(owned.length).toBeGreaterThanOrEqual(2);
  });

  it("Tim has at least 1 fleet with waypoints", () => {
    const withWaypoints = mockPlayerState.fleets.filter(
      (f) => f.owner === "tim" && f.waypoints && f.waypoints.length > 0,
    );
    expect(withWaypoints.length).toBeGreaterThanOrEqual(1);
  });

  it("has at least one enemy fleet visible", () => {
    const enemy = mockPlayerState.fleets.filter((f) => f.owner !== "tim");
    expect(enemy.length).toBeGreaterThanOrEqual(1);
  });

  it("has turn events", () => {
    expect(mockPlayerState.events.length).toBeGreaterThan(0);
  });

  it("all events reference the current turn", () => {
    for (const e of mockPlayerState.events) {
      expect(e.turn).toBe(mockPlayerState.turn);
    }
  });

  it("has fleet_arrived and planet_scanned events", () => {
    const types = new Set(mockPlayerState.events.map((e) => e.type));
    expect(types.has("fleet_arrived")).toBe(true);
    expect(types.has("planet_scanned")).toBe(true);
  });

  it("design speeds are in reasonable parsec range", () => {
    for (const d of mockPlayerState.designs) {
      expect(d.speed).toBeGreaterThan(0);
      expect(d.speed).toBeLessThanOrEqual(20);
    }
  });

  it("scanner ranges are positive parsec values", () => {
    for (const d of mockPlayerState.designs) {
      expect(d.scanner.normal).toBeGreaterThan(0);
      expect(d.scanner.penetrating).toBeGreaterThanOrEqual(0);
    }
  });

  it("coordinate values are safe JS integers", () => {
    for (const p of mockPlayerState.planets) {
      expect(Number.isSafeInteger(p.x)).toBe(true);
      expect(Number.isSafeInteger(p.y)).toBe(true);
    }
    for (const f of mockPlayerState.fleets) {
      expect(Number.isSafeInteger(f.position.x)).toBe(true);
      expect(Number.isSafeInteger(f.position.y)).toBe(true);
      if (f.waypoints) {
        for (const w of f.waypoints) {
          expect(Number.isSafeInteger(w.x)).toBe(true);
          expect(Number.isSafeInteger(w.y)).toBe(true);
        }
      }
    }
  });

  it("PARSEC constant is 2^29", () => {
    expect(PARSEC).toBe(536_870_912);
  });
});
