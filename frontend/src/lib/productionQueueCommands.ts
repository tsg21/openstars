import type { PlayerCommand, PlayerProductionQueueItem } from "../types";

/**
 * Build all planet-scoped commands for a single replacement, including production
 * queue diffs and (optionally) a `set_planet_production_mode` command.
 *
 * Use this in any handler that calls `replaceCommands({ kind: "planet", ... }, ...)`,
 * so that staging unrelated edits (e.g. tweaking the queue) does not silently drop
 * an already-staged production-mode toggle (or vice versa).
 */
export function buildPlanetScopeCommands(
  planetId: string,
  baseQueue: PlayerProductionQueueItem[],
  desiredQueue: PlayerProductionQueueItem[],
  baseContributeOnlyLeftoverToResearch: boolean | null | undefined,
  desiredContributeOnlyLeftoverToResearch: boolean | null | undefined,
): PlayerCommand[] {
  const commands: PlayerCommand[] = buildProductionQueueCommands(
    planetId,
    baseQueue,
    desiredQueue,
  );
  if (
    desiredContributeOnlyLeftoverToResearch != null &&
    desiredContributeOnlyLeftoverToResearch !== baseContributeOnlyLeftoverToResearch
  ) {
    commands.push({
      type: "set_planet_production_mode",
      planetId,
      contributeOnlyLeftoverToResearch: desiredContributeOnlyLeftoverToResearch,
    });
  }
  return commands;
}

export function buildProductionQueueCommands(
  planetId: string,
  baseQueue: PlayerProductionQueueItem[],
  desiredQueue: PlayerProductionQueueItem[],
): PlayerCommand[] {
  if (desiredQueue.length === 0) {
    return baseQueue.length === 0 ? [] : [{ type: "clear_production_queue", planetId }];
  }

  const baseById = new Map(baseQueue.map((item) => [item.id, item]));
  const desiredExistingItems = desiredQueue.filter((item) => baseById.has(item.id));
  const desiredExistingIds = new Set(desiredExistingItems.map((item) => item.id));
  const commands: PlayerCommand[] = [];
  const workingOrder = baseQueue.map((item) => item.id);

  for (const item of desiredExistingItems) {
    const targetAnchorId =
      findPreviousExistingItemId(desiredQueue, item.id, desiredExistingIds) ?? null;
    const currentIndex = workingOrder.indexOf(item.id);
    const targetIndex =
      targetAnchorId == null ? 0 : workingOrder.indexOf(targetAnchorId) + 1;

    if (currentIndex !== targetIndex) {
      commands.push({
        type: "move_production_item",
        planetId,
        itemId: item.id,
        insertAfterItemId: targetAnchorId,
      });
      workingOrder.splice(currentIndex, 1);
      workingOrder.splice(targetIndex, 0, item.id);
    }
  }

  for (const baseItem of baseQueue) {
    const desiredItem = desiredQueue.find((item) => item.id === baseItem.id);
    if (!desiredItem) {
      commands.push({
        type: "remove_production_item",
        planetId,
        itemId: baseItem.id,
        quantity: baseItem.quantity,
      });
      continue;
    }

    if (desiredItem.quantity < baseItem.quantity) {
      commands.push({
        type: "remove_production_item",
        planetId,
        itemId: baseItem.id,
        quantity: baseItem.quantity - desiredItem.quantity,
      });
      continue;
    }

    if (desiredItem.quantity > baseItem.quantity) {
      commands.push({
        type: "add_production_item",
        planetId,
        itemType: desiredItem.itemType,
        ...(desiredItem.itemType === "starbase" && { targetType: desiredItem.targetType ?? null }),
        ...(desiredItem.itemType === "ship" && { designId: desiredItem.designId ?? null }),
        quantity: desiredItem.quantity - baseItem.quantity,
        insertAfterItemId: desiredItem.id,
      });
    }
  }

  const newItemBlocks = collectNewItemBlocks(desiredQueue, desiredExistingIds);
  for (const block of newItemBlocks) {
    for (const item of [...block.items].reverse()) {
      commands.push({
        type: "add_production_item",
        planetId,
        itemType: item.itemType,
        ...(item.itemType === "starbase" && { targetType: item.targetType ?? null }),
        ...(item.itemType === "ship" && { designId: item.designId ?? null }),
        quantity: item.quantity,
        insertAfterItemId: block.insertAfterItemId,
      });
    }
  }

  return commands;
}

function findPreviousExistingItemId(
  desiredQueue: PlayerProductionQueueItem[],
  itemId: string,
  existingIds: Set<string>,
): string | null {
  const itemIndex = desiredQueue.findIndex((item) => item.id === itemId);
  for (let index = itemIndex - 1; index >= 0; index -= 1) {
    const candidate = desiredQueue[index];
    if (existingIds.has(candidate.id)) {
      return candidate.id;
    }
  }
  return null;
}

function collectNewItemBlocks(
  desiredQueue: PlayerProductionQueueItem[],
  existingIds: Set<string>,
): Array<{ insertAfterItemId: string | null; items: PlayerProductionQueueItem[] }> {
  const blocks: Array<{ insertAfterItemId: string | null; items: PlayerProductionQueueItem[] }> = [];
  let insertAfterItemId: string | null = null;
  let currentBlock: PlayerProductionQueueItem[] = [];

  for (const item of desiredQueue) {
    if (existingIds.has(item.id)) {
      if (currentBlock.length > 0) {
        blocks.push({ insertAfterItemId, items: currentBlock });
        currentBlock = [];
      }
      insertAfterItemId = item.id;
      continue;
    }

    currentBlock.push(item);
  }

  if (currentBlock.length > 0) {
    blocks.push({ insertAfterItemId, items: currentBlock });
  }

  return blocks;
}
