import type {
  ComponentCost,
  DesignerComponentEntry,
  HullDefinition,
  ShipDesignComponentAssignment,
} from "../types";
import type { FitState } from "./designerFit";

export type DerivedDesignerStats = {
  cost: ComponentCost;
  mass: number;
  fuelCapacity: number;
  cargoCapacity: number;
  armour: number;
  scanner: { normal: number; penetrating: number } | null;
};

export function computeDerivedStats(
  hull: HullDefinition,
  components: DesignerComponentEntry[],
  fitState: FitState | ShipDesignComponentAssignment[],
): DerivedDesignerStats {
  const componentById = new Map(components.map((component) => [component.id, component]));
  const assignments = Array.isArray(fitState)
    ? fitState
    : Array.from(fitState, ([slotNumber, fit]) => ({ slotNumber, ...fit }));
  const cost = { ...hull.cost };
  let mass = hull.mass;
  let armour = hull.armourPoints;
  let scannerNormal = 0;
  let scannerPenetrating = 0;

  for (const assignment of assignments) {
    const component = componentById.get(assignment.componentId);
    if (!component) continue;
    cost.resources += component.cost.resources * assignment.componentCount;
    cost.ironium += component.cost.ironium * assignment.componentCount;
    cost.boranium += component.cost.boranium * assignment.componentCount;
    cost.germanium += component.cost.germanium * assignment.componentCount;
    mass += component.mass * assignment.componentCount;
    if (component.armour) {
      armour += component.armour.armourPoints * assignment.componentCount;
    }
    if (component.scanner) {
      scannerNormal = Math.max(scannerNormal, component.scanner.normal);
      scannerPenetrating = Math.max(scannerPenetrating, component.scanner.penetrating);
    }
  }

  return {
    cost,
    mass,
    fuelCapacity: hull.fuelCapacity,
    cargoCapacity: hull.cargoCapacity,
    armour,
    scanner:
      scannerNormal > 0 || scannerPenetrating > 0
        ? { normal: scannerNormal, penetrating: scannerPenetrating }
        : null,
  };
}
