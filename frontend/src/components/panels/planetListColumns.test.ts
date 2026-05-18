import { describe, it, expect } from "vitest";
import {
  queueHeadColumn,
  starbaseColumn,
  ownerColumn,
  resourcesColumn,
} from "./planetListColumns";
import type { PlayerPlanet } from "../../types";
import type { DesignSummary } from "../../types/designer";

function makePlanet(overrides: Partial<PlayerPlanet> = {}): PlayerPlanet {
  return {
    id: "p1",
    name: "Earth",
    x: 0,
    y: 0,
    scanLevel: "detailed",
    scanAge: 0,
    owner: "tim",
    ...overrides,
  };
}

function makeQueueItem(
  itemType: "mine" | "factory" | "ship" | "planetary_scanner" | "starbase",
  designId?: string,
) {
  return {
    id: "qi1",
    itemType,
    quantity: 1,
    designId: designId ?? null,
    progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
  };
}

const designs: DesignSummary[] = [
  {
    id: "d1",
    name: "Scout",
    hull: "scout",
    fuelCapacity: 100,
    cost: { resources: 40, minerals: { ironium: 0, boranium: 0, germanium: 0 } },
  },
];

describe("queueHeadColumn", () => {
  it("returns null sortValue for an empty queue", () => {
    const col = queueHeadColumn(designs);
    expect(col.sortValue!(makePlanet({ productionQueue: [] }))).toBeNull();
  });

  it("returns null sortValue for null productionQueue", () => {
    const col = queueHeadColumn(designs);
    expect(col.sortValue!(makePlanet({ productionQueue: null }))).toBeNull();
  });

  it("returns the friendly label for a non-ship queue head", () => {
    const col = queueHeadColumn(designs);
    const p = makePlanet({ productionQueue: [makeQueueItem("mine")] });
    expect(col.sortValue!(p)).toBe("Mine");
    expect(col.render(p)).toBe("Mine");
  });

  it("returns the design name for a ship queue head", () => {
    const col = queueHeadColumn(designs);
    const p = makePlanet({ productionQueue: [makeQueueItem("ship", "d1")] });
    expect(col.render(p)).toBe("Scout");
  });
});

describe("starbaseColumn", () => {
  it("renders None for a planet with no starbase", () => {
    expect(starbaseColumn.render(makePlanet({ starbase: null }))).toBe("None");
  });

  it("renders Dock for a starbase that cannot build ships", () => {
    const p = makePlanet({ starbase: { type: "orbital_fort", canBuildShips: false } });
    expect(starbaseColumn.render(p)).toBe("Dock");
  });

  it("renders Dock (+ships) for a starbase that can build ships", () => {
    const p = makePlanet({ starbase: { type: "space_station", canBuildShips: true } });
    expect(starbaseColumn.render(p)).toBe("Dock (+ships)");
  });

  it("sortValue ranks None < Dock < Dock(+ships)", () => {
    const none = makePlanet({ starbase: null });
    const dock = makePlanet({ starbase: { type: "orbital_fort", canBuildShips: false } });
    const shipDock = makePlanet({ starbase: { type: "space_station", canBuildShips: true } });
    expect(starbaseColumn.sortValue!(none)).toBe(0);
    expect(starbaseColumn.sortValue!(dock)).toBe(1);
    expect(starbaseColumn.sortValue!(shipDock)).toBe(2);
  });
});

describe("ownerColumn", () => {
  it("sortValue for current player sorts before any other username", () => {
    const col = ownerColumn("tim");
    const own = makePlanet({ owner: "tim" });
    const other = makePlanet({ owner: "alice" });
    const ownVal = col.sortValue!(own) as string;
    const otherVal = col.sortValue!(other) as string;
    expect(ownVal < otherVal).toBe(true);
  });
});

describe("resourcesColumn", () => {
  it("renders — for a planet with no resources field", () => {
    expect(resourcesColumn.render(makePlanet({ resources: null }))).toBe("—");
    expect(resourcesColumn.render(makePlanet({ resources: undefined }))).toBe("—");
  });

  it("renders the numeric value otherwise", () => {
    expect(resourcesColumn.render(makePlanet({ resources: 412 }))).toBe("412");
  });
});
