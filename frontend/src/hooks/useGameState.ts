/**
 * Game state hook backed by the backend API.
 */

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import type {
  Galaxy,
  PlayerState,
  PlayerCommands,
  PlayerCommand,
  PlayerProductionQueueItem,
} from "../types";
import { applyCommandsToPlayerState } from "../lib/applyCommands";
import {
  getGalaxy,
  getPlayerState,
  submitCommands,
  getGame,
  getTurnStatus,
  resolveTurn,
  getCommands,
  ApiError,
} from "../api/client";
import type { GameDetail } from "../api/client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface GameStateHook {
  /** Static galaxy data (planet positions, names, metadata). */
  galaxy: Galaxy | null;
  /** Current player's filtered view of the game world (base state from turn file). */
  playerState: PlayerState | null;
  /** Player state with pending commands applied (working view for UI). */
  workingPlayerState: PlayerState | null;
  /** Commands queued for submission. */
  commands: PlayerCommands;
  /** Add or replace a command. For set_waypoints, replaces by fleetId. */
  setCommand: (command: PlayerCommand) => void;
  /** Replace all staged production commands for a planet from the desired queue state. */
  setPlanetProductionQueue: (
    planetId: string,
    queue: PlayerProductionQueueItem[],
  ) => void;
  /** Clear all queued commands. */
  clearCommands: () => void;
  /** Whether there are unsaved command changes. */
  isDirty: boolean;
  /** Submit commands to the server. */
  submit: () => Promise<void>;
  /** Whether data is loading. */
  loading: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Game detail (submission status per player). */
  gameDetail: GameDetail | null;
  /** Trigger turn resolution. */
  resolve: () => Promise<void>;
  /** Refresh game state from the server. */
  refresh: () => Promise<void>;
  /** Whether commands have been submitted for this turn. */
  submitted: boolean;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useGameState(
  gameId: string | null,
  player: string | null,
): GameStateHook {
  const [galaxy, setGalaxy] = useState<Galaxy | null>(null);
  const [playerState, setPlayerState] = useState<PlayerState | null>(null);
  const [commands, setCommands] = useState<PlayerCommands>({ commands: [] });
  const [isDirty, setIsDirty] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gameDetail, setGameDetail] = useState<GameDetail | null>(null);

  // Track the current gameId/player to avoid stale updates
  const activeRef = useRef({ gameId, player });
  activeRef.current = { gameId, player };

  // --- Load game data ---

  const loadGameData = useCallback(async () => {
    if (!gameId || !player) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch galaxy (static — only once per game), player state, and game detail
      const [galaxyData, stateData, detailData] = await Promise.all([
        getGalaxy(gameId, player),
        getPlayerState(gameId, player),
        getGame(gameId, player),
      ]);

      // Only update if still the same game/player
      if (
        activeRef.current.gameId !== gameId ||
        activeRef.current.player !== player
      ) {
        return;
      }

      setGalaxy(galaxyData);
      setPlayerState(stateData);
      setGameDetail(detailData);

      // Check if we already have submitted commands for this turn.
      // The game detail already tells us if this player has submitted
      // (via has_commands on the backend), so use that as the source of
      // truth rather than inferring from command list length — an empty
      // command list is a valid submission.
      const playerDetail = detailData.players.find(
        (p) => p.username === player,
      );
      const alreadySubmitted = playerDetail?.submitted ?? false;

      if (alreadySubmitted) {
        try {
          const existingCommands = await getCommands(gameId, player);

          // Guard against stale responses after game/player switch
          if (
            activeRef.current.gameId !== gameId ||
            activeRef.current.player !== player
          ) {
            return;
          }

          setSubmitted(true);
          setCommands({ commands: existingCommands.commands });
          setIsDirty(false);
        } catch {
          // Commands file exists (submitted=true) but fetch failed —
          // still mark as submitted, just with empty local commands
          if (
            activeRef.current.gameId !== gameId ||
            activeRef.current.player !== player
          ) {
            return;
          }
          setSubmitted(true);
          setCommands({ commands: [] });
          setIsDirty(false);
        }
      } else {
        setSubmitted(false);
        setCommands({ commands: [] });
        setIsDirty(false);
      }
    } catch (err) {
      if (
        activeRef.current.gameId !== gameId ||
        activeRef.current.player !== player
      ) {
        return;
      }
      const message =
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : err instanceof Error
            ? err.message
            : "Failed to load game data";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [gameId, player]);

  // Load data when game/player changes
  useEffect(() => {
    setGalaxy(null);
    setPlayerState(null);
    setGameDetail(null);
    setCommands({ commands: [] });
    setIsDirty(false);
    setSubmitted(false);
    setError(null);

    loadGameData();
  }, [loadGameData]);

  // --- Command management ---

  const setCommand = useCallback((command: PlayerCommand) => {
    setCommands((prev) => {
      if (command.type === "set_waypoints") {
        const filtered = prev.commands.filter(
          (c) => c.type !== "set_waypoints" || c.fleetId !== command.fleetId,
        );
        return { commands: [...filtered, command] };
      }
      return { commands: [...prev.commands, command] };
    });
    setIsDirty(true);
    setSubmitted(false);
  }, []);

  const setPlanetProductionQueue = useCallback(
    (planetId: string, queue: PlayerProductionQueueItem[]) => {
      if (!playerState) {
        return;
      }

      const planet = playerState.planets.find((candidate) => candidate.id === planetId);
      const baseQueue = planet?.productionQueue ?? [];
      const productionCommands = buildProductionQueueCommands(planetId, baseQueue, queue);

      setCommands((prev) => {
        const filtered = prev.commands.filter(
          (command) =>
            !("planetId" in command && command.planetId === planetId),
        );
        return { commands: [...filtered, ...productionCommands] };
      });
      setIsDirty(true);
      setSubmitted(false);
    },
    [playerState],
  );

  const clearCommands = useCallback(() => {
    setCommands({ commands: [] });
    setIsDirty(false);
    setSubmitted(false);
  }, []);

  // --- Submit ---

  const submit = useCallback(async () => {
    if (!gameId || !player || !playerState) return;

    try {
      setError(null);
      await submitCommands(gameId, player, playerState.turn, commands.commands);
      setIsDirty(false);
      setSubmitted(true);

      // Refresh game detail to update submission status
      const detail = await getGame(gameId, player);
      setGameDetail(detail);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : "Failed to submit commands";
      setError(message);
    }
  }, [gameId, player, playerState, commands]);

  // --- Resolve ---

  const resolve = useCallback(async () => {
    if (!gameId || !player) return;

    try {
      setError(null);
      await resolveTurn(gameId, player);

      // Reload everything for the new turn
      await loadGameData();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : "Failed to resolve turn";
      setError(message);
    }
  }, [gameId, player, loadGameData]);

  // --- Poll for next turn after submission ---

  useEffect(() => {
    if (!submitted || !gameId || !player || !playerState) {
      return;
    }

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const submittedTurn = playerState.turn;

    const poll = async () => {
      try {
        const status = await getTurnStatus(gameId, player);

        if (
          cancelled ||
          activeRef.current.gameId !== gameId ||
          activeRef.current.player !== player
        ) {
          return;
        }

        setError(null);

        if (status.turn > submittedTurn) {
          await loadGameData();
          return;
        }
      } catch (err) {
        if (
          cancelled ||
          activeRef.current.gameId !== gameId ||
          activeRef.current.player !== player
        ) {
          return;
        }

        const message =
          err instanceof ApiError
            ? `${err.code}: ${err.message}`
            : "Failed to check for a new turn";
        setError(message);
      }

      if (!cancelled) {
        timeoutId = setTimeout(poll, 10_000);
      }
    };

    timeoutId = setTimeout(poll, 10_000);

    return () => {
      cancelled = true;
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
      }
    };
  }, [submitted, gameId, player, playerState, loadGameData]);

  // --- Derived state ---

  const workingPlayerState = useMemo(() => {
    if (!playerState) return null;
    return applyCommandsToPlayerState(playerState, commands.commands);
  }, [playerState, commands.commands]);

  return {
    galaxy,
    playerState,
    workingPlayerState,
    commands,
    setCommand,
    setPlanetProductionQueue,
    clearCommands,
    isDirty,
    submit,
    loading,
    error,
    gameDetail,
    resolve,
    refresh: loadGameData,
    submitted,
  };
}

function buildProductionQueueCommands(
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
