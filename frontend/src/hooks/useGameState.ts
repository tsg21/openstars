/**
 * Game state hook backed by the backend API.
 */

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import type {
  Design,
  Galaxy,
  PlayerState,
  PlayerCommands,
  PlayerCommand,
  PlayerProductionQueueItem,
} from "../types";
import { applyCommandsToPlayerState } from "../lib/applyCommands";
import { commandMatchesScope, type CommandScope } from "../lib/commandScope";
import { buildProductionQueueCommands } from "../lib/productionQueueCommands";
import {
  getGalaxy,
  getPlayerState,
  submitCommands,
  getGame,
  getTurnStatus,
  resolveTurn,
  getCommands,
  getDesigns,
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
  addCommand: (command: PlayerCommand) => void;
  /** Replace all staged production commands for a planet from the desired queue state. */
  setPlanetProductionQueue: (
    planetId: string,
    queue: PlayerProductionQueueItem[],
  ) => void;
  /** Replace all staged commands within a scope with an explicit command list. */
  replaceCommands: (scope: CommandScope, commands: PlayerCommand[]) => void;
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
  shipDesigns: Design[];
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
  const [shipDesigns, setShipDesigns] = useState<Design[]>([]);

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
      const [galaxyData, stateData, detailData, shipDesignData] = await Promise.all([
        getGalaxy(gameId, player),
        getPlayerState(gameId, player),
        getGame(gameId, player),
        getDesigns(gameId, player),
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
      setShipDesigns(shipDesignData);

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
    setShipDesigns([]);
    setIsDirty(false);
    setSubmitted(false);
    setError(null);

    loadGameData();
  }, [loadGameData]);

  // --- Command management ---

  const addCommand = useCallback((command: PlayerCommand) => {
    setCommands((prev) => {
      if (command.type === "set_waypoints") {
        const filtered = prev.commands.filter(
          (c) => c.type !== "set_waypoints" || c.fleetId !== command.fleetId,
        );
        return { commands: [...filtered, command] };
      }
      if (command.type === "rename_fleet") {
        const filtered = prev.commands.filter(
          (c) => c.type !== "rename_fleet" || c.fleetId !== command.fleetId,
        );
        return { commands: [...filtered, command] };
      }
      return { commands: [...prev.commands, command] };
    });
    setIsDirty(true);
    setSubmitted(false);
  }, []);

  const replaceCommands = useCallback((scope: CommandScope, scopedCommands: PlayerCommand[]) => {
    setCommands((prev) => {
      const filtered = prev.commands.filter(
        (command) => !commandMatchesScope(command, scope),
      );
      return { commands: [...filtered, ...scopedCommands] };
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
      replaceCommands({ kind: "planet", id: planetId }, productionCommands);
    },
    [playerState, replaceCommands],
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
    addCommand,
    setPlanetProductionQueue,
    replaceCommands,
    clearCommands,
    isDirty,
    submit,
    loading,
    error,
    gameDetail,
    shipDesigns,
    resolve,
    refresh: loadGameData,
    submitted,
  };
}
