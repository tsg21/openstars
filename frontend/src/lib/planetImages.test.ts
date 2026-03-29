import { describe, expect, it } from "vitest";
import { getPlanetImageUrl, type PlanetImageManifest } from "./planetImages";

const manifest: PlanetImageManifest = {
  version: "v1",
  baseUrl: "https://example.com/images",
  imagesByClass: {
    ice: ["ice-001.png", "ice-002.png", "ice-003.png"],
    lava: ["lava-001.png", "lava-002.png", "lava-003.png"],
    ocean: ["ocean-001.png", "ocean-002.png", "ocean-003.png"],
  },
};

describe("getPlanetImageUrl", () => {
  it("is deterministic for the same planet id", () => {
    const planetId = "PLk8m3x2";
    const first = getPlanetImageUrl(manifest, planetId);
    const second = getPlanetImageUrl(manifest, planetId);

    expect(first).toBe(second);
    expect(first).toMatch(/^https:\/\/example\.com\/images\/[a-z-]+-\d{3}\.png$/);
  });

  it("spreads ids across available images", () => {
    const picks = new Set(
      Array.from({ length: 30 }, (_, i) => getPlanetImageUrl(manifest, `PL-${i}`)),
    );

    expect(picks.size).toBeGreaterThan(3);
  });

  it("does not produce double slashes when baseUrl ends with /", () => {
    const withTrailingSlash: PlanetImageManifest = {
      ...manifest,
      baseUrl: "https://example.com/images/",
    };

    const picked = getPlanetImageUrl(withTrailingSlash, "PL-12");
    expect(picked).toMatch(/^https:\/\/example\.com\/images\/[a-z-]+-\d{3}\.png$/);
  });

  it("returns null when no classes exist", () => {
    expect(
      getPlanetImageUrl(
        {
          version: "v1",
          baseUrl: "https://example.com/images",
          imagesByClass: {},
        },
        "PL-1",
      ),
    ).toBeNull();
  });
});
