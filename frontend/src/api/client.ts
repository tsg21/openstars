/**
 * OpenStars! API client.
 *
 * Typed functions for each backend endpoint. Handles snake_case ↔ camelCase
 * conversion transparently so the rest of the frontend works with camelCase.
 *
 * Base URL comes from VITE_API_URL environment variable (default: "" for
 * same-origin, which works with the Vite dev proxy or when served together).
 */

import type {
  Galaxy,
  GalaxySize,
  PlayerState,
  PlayerCommand,
} from "../types";
import { keysToCamel, keysToSnake } from "../lib/caseConvert";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  player?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (player) {
    headers["X-Player"] = player;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let code = "UNKNOWN";
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.error) {
        code = body.error.code ?? code;
        message = body.error.message ?? message;
      }
    } catch {
      // Couldn't parse error body — use defaults
    }
    throw new ApiError(res.status, code, message);
  }

  const json = await res.json();
  return keysToCamel(json) as T;
}

// ---------------------------------------------------------------------------
// API types (response shapes after camelCase conversion)
// ---------------------------------------------------------------------------

export interface GameSummary {
  gameId: string;
  name: string;
  galaxySize: GalaxySize;
  turn: number;
  players: string[];
  allTurnsSubmitted: boolean;
  createdAt: string;
}

export interface PlayerSubmissionInfo {
  username: string;
  name: string;
  submitted: boolean;
}

export interface GameDetail {
  gameId: string;
  name: string;
  galaxySize: GalaxySize;
  turn: number;
  players: PlayerSubmissionInfo[];
  createdAt: string;
}

export interface TurnStatus {
  turn: number;
}

export interface CreateGameResponse {
  gameId: string;
  name: string;
  galaxySize: GalaxySize;
  turn: number;
  players: { username: string; name: string }[];
  createdAt: string;
}

export interface SubmitCommandsResponse {
  status: string;
  turn: number;
  commandCount: number;
}

export interface ResolveResponse {
  turn: number;
  status: string;
}

export interface CommandsResponse {
  turn: number;
  commands: PlayerCommand[];
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** List all games, optionally filtered to a player. */
export async function listGames(player?: string): Promise<GameSummary[]> {
  const result = await request<{ games: GameSummary[] }>(
    "/api/v1/games",
    {},
    player,
  );
  return result.games;
}

/** Get game detail with per-player submission status. */
export async function getGame(
  gameId: string,
  player: string,
): Promise<GameDetail> {
  return request<GameDetail>(`/api/v1/games/${gameId}`, {}, player);
}

/** Get the current turn number using the lightweight status endpoint. */
export async function getTurnStatus(
  gameId: string,
  player: string,
): Promise<TurnStatus> {
  return request<TurnStatus>(`/api/v1/games/${gameId}/turn-status`, {}, player);
}

/** Create a new game. */
export async function createGame(
  name: string,
  galaxySize: GalaxySize,
  players: string[],
): Promise<CreateGameResponse> {
  return request<CreateGameResponse>("/api/v1/games", {
    method: "POST",
    body: JSON.stringify(
      keysToSnake({ name, galaxySize, players }),
    ),
  });
}

/** Get the static galaxy definition. */
export async function getGalaxy(
  gameId: string,
  player: string,
): Promise<Galaxy> {
  return request<Galaxy>(`/api/v1/games/${gameId}/galaxy`, {}, player);
}

/** Get the player's state for a turn (default: current). */
export async function getPlayerState(
  gameId: string,
  player: string,
  turn?: number,
): Promise<PlayerState> {
  const query = turn !== undefined ? `?turn=${turn}` : "";
  return request<PlayerState>(
    `/api/v1/games/${gameId}/state${query}`,
    {},
    player,
  );
}

/** Submit commands for the current turn. */
export async function submitCommands(
  gameId: string,
  player: string,
  turn: number,
  commands: PlayerCommand[],
): Promise<SubmitCommandsResponse> {
  const integerCommands = commands.map((command) => {
    if (command.type !== "set_waypoints") return command;

    return {
      ...command,
      waypoints: command.waypoints.map((wp) => ({
        x: Math.trunc(wp.x),
        y: Math.trunc(wp.y),
      })),
    };
  });

  return request<SubmitCommandsResponse>(
    `/api/v1/games/${gameId}/commands`,
    {
      method: "POST",
      body: JSON.stringify(
        keysToSnake({ turn, commands: integerCommands }),
      ),
    },
    player,
  );
}

/** Get the player's submitted commands for the current turn. */
export async function getCommands(
  gameId: string,
  player: string,
): Promise<CommandsResponse> {
  return request<CommandsResponse>(
    `/api/v1/games/${gameId}/commands`,
    {},
    player,
  );
}

/** Trigger turn resolution (all players must have submitted). */
export async function resolveTurn(
  gameId: string,
  player: string,
): Promise<ResolveResponse> {
  return request<ResolveResponse>(
    `/api/v1/games/${gameId}/resolve`,
    { method: "POST" },
    player,
  );
}
