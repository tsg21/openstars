import type { DesignerComponentEntry, HullDefinition } from "../../types";

export function makeHull(overrides: Partial<HullDefinition> = {}): HullDefinition {
  return {
    id: "small_freighter",
    name: "Small Freighter",
    cost: { resources: 20, ironium: 12, boranium: 0, germanium: 17 },
    mass: 25,
    domain: "ship",
    fuelCapacity: 130,
    cargoCapacity: 70,
    dockCapacity: 0,
    armourPoints: 25,
    initiative: 0,
    layoutGrid: { w: 8, h: 2 },
    cargoLayout: { x: 2, y: 0, w: 2, h: 2 },
    slots: [
      {
        slotNumber: 1,
        slotCategories: ["engine"],
        capacity: 1,
        required: true,
        position: { x: 0, y: 0 },
      },
      {
        slotNumber: 2,
        slotCategories: ["scanner", "electrical", "mechanical"],
        capacity: 1,
        required: false,
        position: { x: 6, y: 0 },
      },
      {
        slotNumber: 3,
        slotCategories: ["shield", "armour"],
        capacity: 1,
        required: false,
        position: { x: 4, y: 0 },
      },
    ],
    ...overrides,
  };
}

export function makeCruiser(overrides: Partial<HullDefinition> = {}): HullDefinition {
  return makeHull({
    id: "cruiser",
    name: "Cruiser",
    cost: { resources: 85, ironium: 40, boranium: 5, germanium: 8 },
    mass: 90,
    fuelCapacity: 600,
    cargoCapacity: 0,
    armourPoints: 700,
    layoutGrid: { w: 8, h: 8 },
    cargoLayout: undefined,
    slots: [
      {
        slotNumber: 1,
        slotCategories: ["engine"],
        capacity: 2,
        required: true,
        position: { x: 0, y: 2 },
        size: { w: 2, h: 4 },
      },
      {
        slotNumber: 4,
        slotCategories: ["weapon"],
        capacity: 2,
        required: false,
        position: { x: 4, y: 0 },
      },
    ],
    ...overrides,
  });
}

export const quickJump5: DesignerComponentEntry = {
  id: "quick_jump_5",
  name: "Quick Jump 5",
  componentType: "engine",
  cost: { resources: 3, ironium: 1, boranium: 0, germanium: 1 },
  mass: 4,
  engine: { fuelUsage: [25, 100, 100, 100, 100, 100, 100, 100, 100, 100], isRamscoop: false },
};

export const colloidalPhaser: DesignerComponentEntry = {
  id: "colloidal_phaser",
  name: "Colloidal Phaser",
  componentType: "weapon",
  cost: { resources: 12, ironium: 0, boranium: 8, germanium: 0 },
  mass: 2,
  weapon: { range: 3, damage: 26, initiative: 9 },
};

export const laser: DesignerComponentEntry = {
  id: "laser",
  name: "Laser",
  componentType: "weapon",
  cost: { resources: 5, ironium: 0, boranium: 2, germanium: 0 },
  mass: 1,
  weapon: { range: 1, damage: 10, initiative: 6 },
};

export const rhinoScanner: DesignerComponentEntry = {
  id: "rhino_scanner",
  name: "Rhino Scanner",
  componentType: "scanner",
  cost: { resources: 5, ironium: 3, boranium: 0, germanium: 2 },
  mass: 3,
  scanner: { normal: 120, penetrating: 0 },
};

export const shield: DesignerComponentEntry = {
  id: "bat_shield",
  name: "Bat Shield",
  componentType: "shield",
  cost: { resources: 4, ironium: 0, boranium: 0, germanium: 2 },
  mass: 1,
  shield: { shieldPoints: 25 },
};
