import { describe, it, expect } from "vitest";
import { mockGalaxy } from "./galaxy";
import { mockPlayerState } from "./playerState";
import { GALAXY_SIZES, PARSEC } from "../types";

/** Validates entity ID format: 2 uppercase letters + 6 lowercase alphanumeric */
function isValidEntityId(id: string, prefix: string): boolean {
  const re = new RegExp(`^${prefix}[a-z0-9]{6}$`);
  return re.test(id);
}

describe("Mock Galaxy", () => {
  it("has valid galaxy metadata", () => {
    expect(mockGalaxy.galaxy.name).toBeTruthy();
    expect(mockGalaxy.galaxy.size).toBe("small");
    expect(mockGalaxy.galaxy.seed).toBeTypeOf("number");
  });

  it("has ~20 planets", () => {
    expect(mockGalaxy.planets.length).toBe(20);
  });

  it("all planet IDs follow the PL prefix format", () => {
    for (const planet of mockGalaxy.planets) {
      expect(isValidEntityId(planet.id, "PL")).toBe(true);
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

  it("all coordinates are within 40-bit range", () => {
    const maxCoord = 2 ** GALAXY_SIZES.small - 1;
    for (const planet of mockGalaxy.planets) {
      expect(planet.x).toBeGreaterThanOrEqual(0);
      expect(planet.x).toBeLessThanOrEqual(maxCoord);
      expect(planet.y).toBeGreaterThanOrEqual(0);
      expect(planet.y).toBeLessThanOrEqual(maxCoord);
    }
  });

  it("all coordinates are within the placement region (middle 50%)", () => {
    const maxCoord = 2 ** GALAXY_SIZES.small - 1;
    const lo = maxCoord * 0.25;
    const hi = maxCoord * 0.75;
    for (const planet of mockGalaxy.planets) {
      expect(planet.x).toBeGreaterThanOrEqual(lo);
      expect(planet.x).toBeLessThanOrEqual(hi);
      expect(planet.y).toBeGreaterThanOrEqual(lo);
      expect(planet.y).toBeLessThanOrEqual(hi);
    }
  });

  it("no two planets share the same coordinates", () => {
    const coords = new Set(
      mockGalaxy.planets.map((p) => `${p.x},${p.y}`),
    );
    expect(coords.size).toBe(mockGalaxy.planets.length);
  });
});

describe("Mock Player State", () => {
  it("is for player tim at turn 3", () => {
    expect(mockPlayerState.player).toBe("tim");
    expect(mockPlayerState.turn).toBe(3);
  });

  it("all fleet IDs follow the FL prefix format", () => {
    for (const fleet of mockPlayerState.fleets) {
      expect(isValidEntityId(fleet.id, "FL")).toBe(true);
    }
  });

  it("all design IDs follow the DE prefix format", () => {
    for (const design of mockPlayerState.designs) {
      expect(isValidEntityId(design.id, "DE")).toBe(true);
    }
  });

  it("planet IDs in player state exist in the galaxy", () => {
    const galaxyIds = new Set(mockGalaxy.planets.map((p) => p.id));
    for (const planet of mockPlayerState.planets) {
      expect(galaxyIds.has(planet.id)).toBe(true);
    }
  });

  it("fleet compositions reference valid design IDs", () => {
    const designIds = new Set(mockPlayerState.designs.map((d) => d.id));
    for (const fleet of mockPlayerState.fleets) {
      if (fleet.composition) {
        for (const comp of fleet.composition) {
          expect(designIds.has(comp.designId)).toBe(true);
        }
      }
    }
  });

  it("Tim owns at least 2 planets", () => {
    const owned = mockPlayerState.planets.filter((p) => p.owner === "tim");
    expect(owned.length).toBeGreaterThanOrEqual(2);
  });

  it("has at least one fleet with waypoints", () => {
    const withWaypoints = mockPlayerState.fleets.filter(
      (f) => f.waypoints && f.waypoints.length > 0,
    );
    expect(withWaypoints.length).toBeGreaterThanOrEqual(1);
  });

  it("has at least one enemy fleet visible", () => {
    const enemy = mockPlayerState.fleets.filter((f) => f.owner !== "tim");
    expect(enemy.length).toBeGreaterThanOrEqual(1);
  });

  it("has turn events", () => {
    expect(mockPlayerState.events.length).toBeGreaterThanOrEqual(1);
  });

  it("events reference the correct turn", () => {
    for (const event of mockPlayerState.events) {
      expect(event.turn).toBe(3);
    }
  });

  it("has fleet_arrived and planet_scanned events", () => {
    const types = new Set(mockPlayerState.events.map((e) => e.type));
    expect(types.has("fleet_arrived")).toBe(true);
    expect(types.has("planet_scanned")).toBe(true);
  });

  it("waypoint coordinates are within galaxy bounds", () => {
    const maxCoord = 2 ** GALAXY_SIZES.small - 1;
    for (const fleet of mockPlayerState.fleets) {
      if (fleet.waypoints) {
        for (const wp of fleet.waypoints) {
          expect(wp.x).toBeGreaterThanOrEqual(0);
          expect(wp.x).toBeLessThanOrEqual(maxCoord);
          expect(wp.y).toBeGreaterThanOrEqual(0);
          expect(wp.y).toBeLessThanOrEqual(maxCoord);
        }
      }
    }
  });

  it("design speeds and scanner ranges are positive parsec values", () => {
    for (const design of mockPlayerState.designs) {
      expect(design.speed).toBeGreaterThan(0);
      expect(design.scanner.normal).toBeGreaterThan(0);
      expect(design.scanner.penetrating).toBeGreaterThanOrEqual(0);
    }
  });

  it("PARSEC constant is 2^29", () => {
    expect(PARSEC).toBe(536_870_912);
  });
});
