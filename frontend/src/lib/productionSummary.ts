import type { PlayerProductionQueueItem, ProductionItemType, StarbaseType } from "../types";
import type { DesignSummary } from "../types/designer";

let _draftId = 0;

export function createDraftProductionQueueItem(
  itemType: ProductionItemType,
  targetType: StarbaseType | null = null,
  designId: string | null = null,
): PlayerProductionQueueItem {
  _draftId += 1;
  return {
    id: `draft-${itemType}-${_draftId}`,
    itemType,
    targetType,
    designId,
    quantity: 1,
    progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
  };
}

export const PRODUCTION_ITEM_LABELS: Record<ProductionItemType, string> = {
  mine: "Mine",
  factory: "Factory",
  starbase: "Starbase",
  ship: "Ship",
  planetary_scanner: "Planetary Scanner",
};

export function describeQueueItem(
  item: PlayerProductionQueueItem,
  shipDesigns: DesignSummary[],
): string {
  if (item.itemType === "ship") {
    return shipDesigns.find((d) => d.id === item.designId)?.name ?? "Ship";
  }
  return PRODUCTION_ITEM_LABELS[item.itemType];
}

export function summariseQueue(
  queue: PlayerProductionQueueItem[],
  shipDesigns: DesignSummary[],
): string {
  if (queue.length === 0) return "Queue: empty";

  const label = (item: PlayerProductionQueueItem) => describeQueueItem(item, shipDesigns);

  if (queue.length === 1) {
    return `Queue: ${queue[0].quantity}× ${label(queue[0])}`;
  }
  if (queue.length === 2) {
    return `Queue: ${queue[0].quantity}× ${label(queue[0])}, ${queue[1].quantity}× ${label(queue[1])}`;
  }
  return `Queue: ${queue[0].quantity}× ${label(queue[0])}, ${queue[1].quantity}× ${label(queue[1])}, +${queue.length - 2} more`;
}
