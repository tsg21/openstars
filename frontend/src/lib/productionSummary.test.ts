import { describe, it, expect } from "vitest";
import { describeQueueItem, summariseQueue } from "./productionSummary";
import type { PlayerProductionQueueItem } from "../types";
import type { DesignSummary } from "../types/designer";

const makeItem = (
  itemType: PlayerProductionQueueItem["itemType"],
  quantity = 1,
  designId?: string,
): PlayerProductionQueueItem => ({
  id: `item-${itemType}`,
  itemType,
  quantity,
  designId: designId ?? null,
  progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
});

const designs: DesignSummary[] = [
  {
    id: "design-1",
    name: "Scout",
    hull: "scout",
    fuelCapacity: 100,
    cost: { resources: 40, minerals: { ironium: 0, boranium: 0, germanium: 0 } },
  },
];

describe("describeQueueItem", () => {
  it("returns the design name for a ship item", () => {
    expect(describeQueueItem(makeItem("ship", 1, "design-1"), designs)).toBe("Scout");
  });

  it("returns friendly label for non-ship items", () => {
    expect(describeQueueItem(makeItem("mine"), designs)).toBe("Mine");
    expect(describeQueueItem(makeItem("factory"), designs)).toBe("Factory");
    expect(describeQueueItem(makeItem("planetary_scanner"), designs)).toBe("Planetary Scanner");
  });

  it("falls back to 'Ship' for unknown design id", () => {
    expect(describeQueueItem(makeItem("ship", 1, "unknown"), designs)).toBe("Ship");
  });
});

describe("summariseQueue", () => {
  it("returns 'Queue: empty' for an empty queue", () => {
    expect(summariseQueue([], designs)).toBe("Queue: empty");
  });

  it("returns single-item summary", () => {
    expect(summariseQueue([makeItem("mine", 3)], designs)).toBe("Queue: 3× Mine");
  });

  it("returns two-item summary", () => {
    expect(summariseQueue([makeItem("factory", 5), makeItem("mine", 2)], designs)).toBe(
      "Queue: 5× Factory, 2× Mine",
    );
  });

  it("returns three-item summary with +N more", () => {
    const queue = [makeItem("factory", 5), makeItem("mine", 2), makeItem("planetary_scanner", 1)];
    expect(summariseQueue(queue, designs)).toBe("Queue: 5× Factory, 2× Mine, +1 more");
  });

  it("counts all items beyond two in +N more", () => {
    const queue = [
      makeItem("factory", 1),
      makeItem("mine", 1),
      makeItem("planetary_scanner", 1),
      makeItem("ship", 1, "design-1"),
    ];
    expect(summariseQueue(queue, designs)).toBe("Queue: 1× Factory, 1× Mine, +2 more");
  });
});
