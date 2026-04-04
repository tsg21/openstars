import type { PlayerCommand, PlayerProductionQueueItem } from "../types";

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
