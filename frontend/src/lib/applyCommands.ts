import type {
  PlayerState,
  PlayerCommand,
  PlayerProductionQueueItem,
  ProductionItemType,
} from "../types";

/**
 * Applies pending commands to a base player state, creating a "working view"
 * of the game state that includes local changes not yet submitted to the server.
 *
 * This is a pure function — it does not mutate the input state.
 *
 * @param playerState Base player state from the turn file
 * @param commands Array of pending commands to apply
 * @returns New player state with commands applied
 */
export function applyCommandsToPlayerState(
  playerState: PlayerState,
  commands: PlayerCommand[]
): PlayerState {
  // Clone the player state (shallow clone, but we'll replace modified arrays)
  const merged: PlayerState = {
    ...playerState,
    // Deep clone the fleets array since we'll be modifying fleet objects
    fleets: playerState.fleets.map((fleet) => ({ ...fleet })),
    planets: playerState.planets.map((planet) => ({
      ...planet,
      productionQueue: planet.productionQueue?.map((item) => ({
        ...item,
        progress: {
          ...item.progress,
          mineralsSpent: { ...item.progress.mineralsSpent },
        },
      })) ?? planet.productionQueue,
    })),
  };

  let draftQueueItemCount = 0;

  // Apply each command to the merged state
  for (const cmd of commands) {
    if (cmd.type === "set_waypoints") {
      const fleetIndex = merged.fleets.findIndex((f) => f.id === cmd.fleetId);
      if (fleetIndex !== -1) {
        merged.fleets[fleetIndex] = {
          ...merged.fleets[fleetIndex],
          waypoints: cmd.waypoints,
          ...(cmd.repeat != null && { repeat: cmd.repeat }),
        };
      }
      continue;
    }

    if (cmd.type === "rename_fleet") {
      const fleetIndex = merged.fleets.findIndex((fleet) => fleet.id === cmd.fleetId);
      if (fleetIndex !== -1) {
        merged.fleets[fleetIndex] = {
          ...merged.fleets[fleetIndex],
          name: cmd.name,
        };
      }
      continue;
    }

    const planetIndex = merged.planets.findIndex((planet) => planet.id === cmd.planetId);
    if (planetIndex === -1) {
      continue;
    }

    const planet = merged.planets[planetIndex];
    const queue = [...(planet.productionQueue ?? [])];

    if (cmd.type === "add_production_item") {
      const draftItem = createDraftQueueItem(
        `draft-${draftQueueItemCount++}`,
        cmd.itemType,
        cmd.targetType ?? null,
        cmd.designId ?? null,
        cmd.quantity,
      );
      const updatedQueue = insertQueueItem(queue, draftItem, cmd.insertAfterItemId ?? null);
      merged.planets[planetIndex] = { ...planet, productionQueue: updatedQueue };
      continue;
    }

    if (cmd.type === "move_production_item") {
      const itemIndex = queue.findIndex((item) => item.id === cmd.itemId);
      if (itemIndex === -1) {
        continue;
      }
      const [item] = queue.splice(itemIndex, 1);
      const updatedQueue = insertQueueItem(queue, item, cmd.insertAfterItemId ?? null);
      merged.planets[planetIndex] = { ...planet, productionQueue: updatedQueue };
      continue;
    }

    if (cmd.type === "remove_production_item") {
      const itemIndex = queue.findIndex((item) => item.id === cmd.itemId);
      if (itemIndex === -1) {
        continue;
      }
      const item = queue[itemIndex];
      if (cmd.quantity >= item.quantity) {
        queue.splice(itemIndex, 1);
      } else {
        queue[itemIndex] = {
          ...item,
          quantity: item.quantity - cmd.quantity,
        };
      }
      merged.planets[planetIndex] = { ...planet, productionQueue: queue };
      continue;
    }

    if (cmd.type === "clear_production_queue") {
      merged.planets[planetIndex] = { ...planet, productionQueue: [] };
    }
  }

  return merged;
}

function createDraftQueueItem(
  id: string,
  itemType: ProductionItemType,
  targetType: PlayerProductionQueueItem["targetType"],
  designId: PlayerProductionQueueItem["designId"],
  quantity: number,
): PlayerProductionQueueItem {
  return {
    id,
    itemType,
    targetType,
    designId,
    quantity,
    progress: {
      resourcesSpent: 0,
      mineralsSpent: {
        ironium: 0,
        boranium: 0,
        germanium: 0,
      },
    },
  };
}

function insertQueueItem(
  queue: PlayerProductionQueueItem[],
  item: PlayerProductionQueueItem,
  insertAfterItemId: string | null,
): PlayerProductionQueueItem[] {
  if (insertAfterItemId == null) {
    return [item, ...queue];
  }

  const insertAfterIndex = queue.findIndex((queueItem) => queueItem.id === insertAfterItemId);
  if (insertAfterIndex === -1) {
    return [...queue, item];
  }

  const updatedQueue = [...queue];
  updatedQueue.splice(insertAfterIndex + 1, 0, item);
  return updatedQueue;
}
