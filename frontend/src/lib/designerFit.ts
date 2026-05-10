import type {
  ComponentType,
  DesignerComponentEntry,
  HullDefinition,
  HullSlotDefinition,
  ShipDesignComponentAssignment,
} from "../types";

export type FitState = Map<number, { componentId: string; componentCount: number }>;

export function applyComponentToFitState({
  hull,
  components,
  fitState,
  slotNumber,
  componentId,
}: {
  hull: HullDefinition;
  components: DesignerComponentEntry[];
  fitState: FitState;
  slotNumber: number;
  componentId: string;
}): { fitState: FitState; rejected: boolean; replaced: boolean } {
  const slot = hull.slots.find((candidate) => candidate.slotNumber === slotNumber);
  const component = components.find((candidate) => candidate.id === componentId);
  if (!slot || !component || !slotAcceptsComponent(slot.slotCategories, component.componentType)) {
    return { fitState, rejected: true, replaced: false };
  }

  const current = fitState.get(slotNumber);
  const next = new Map(fitState);
  if (!current) {
    next.set(slotNumber, { componentId, componentCount: 1 });
    return { fitState: next, rejected: false, replaced: false };
  }

  if (current.componentId === componentId) {
    next.set(slotNumber, {
      componentId,
      componentCount: Math.min(slot.capacity, current.componentCount + 1),
    });
    return { fitState: next, rejected: false, replaced: false };
  }

  next.set(slotNumber, { componentId, componentCount: 1 });
  return { fitState: next, rejected: false, replaced: true };
}

export function computeDesignValidationErrors(hull: HullDefinition, fitState: FitState): string[] {
  const errors: string[] = [];
  for (const slot of hull.slots) {
    const fit = fitState.get(slot.slotNumber);
    if (fit && fit.componentCount > slot.capacity) {
      errors.push(`Slot ${slot.slotNumber} (${formatSlotCategories(slot)}) exceeds capacity`);
    }
    if (!slot.required) continue;
    if (!fit) {
      if (slot.slotCategories.includes("engine")) {
        errors.push(
          `Slot ${slot.slotNumber} (${formatSlotCategories(slot)}) needs ${slot.capacity} engines`,
        );
      } else {
        errors.push(`Slot ${slot.slotNumber} (${formatSlotCategories(slot)}) is required`);
      }
      continue;
    }
    if (fit.componentCount < slot.capacity) {
      if (slot.slotCategories.includes("engine")) {
        errors.push(
          `Slot ${slot.slotNumber} (${formatSlotCategories(slot)}) needs ${slot.capacity} engines`,
        );
      } else {
        errors.push(
          `Slot ${slot.slotNumber} (${formatSlotCategories(slot)}) needs ${slot.capacity} components`,
        );
      }
    }
  }
  return errors;
}

export function fitStateToAssignments(fitState: FitState): ShipDesignComponentAssignment[] {
  return Array.from(fitState, ([slotNumber, fit]) => ({
    slotNumber,
    componentId: fit.componentId,
    componentCount: fit.componentCount,
  })).sort((left, right) => left.slotNumber - right.slotNumber);
}

export function assignmentsToFitState(
  assignments: ShipDesignComponentAssignment[] | undefined,
): FitState {
  return new Map(
    (assignments ?? []).map((assignment) => [
      assignment.slotNumber,
      {
        componentId: assignment.componentId,
        componentCount: assignment.componentCount,
      },
    ]),
  );
}

export function decrementSlot(fitState: FitState, slotNumber: number): FitState {
  const next = new Map(fitState);
  const fit = next.get(slotNumber);
  if (!fit) return fitState;
  if (fit.componentCount <= 1) {
    next.delete(slotNumber);
  } else {
    next.set(slotNumber, { ...fit, componentCount: fit.componentCount - 1 });
  }
  return next;
}

function slotAcceptsComponent(slotCategories: string[], componentType: ComponentType): boolean {
  if (slotCategories.includes(componentType)) return true;
  if (componentType === "torpedo" && slotCategories.includes("weapon")) return true;
  return (
    slotCategories.includes("general_purpose") &&
    ["scanner", "weapon", "torpedo", "shield", "armour", "electrical", "mechanical"].includes(
      componentType,
    )
  );
}

function formatSlotCategories(slot: HullSlotDefinition) {
  return slot.slotCategories
    .map((category) =>
      category
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" "),
    )
    .join("/");
}
