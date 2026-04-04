import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useGameState } from "./useGameState";
import type { Galaxy, PlayerState } from "../types";
import type { GameDetail } from "../api/client";

const mocks = vi.hoisted(() => ({
  getGalaxy: vi.fn(),
  getPlayerState: vi.fn(),
  submitCommands: vi.fn(),
  getGame: vi.fn(),
  getTurnStatus: vi.fn(),
  resolveTurn: vi.fn(),
  getCommands: vi.fn(),
}));

vi.mock("../api/client", () => ({
  getGalaxy: mocks.getGalaxy,
  getPlayerState: mocks.getPlayerState,
  submitCommands: mocks.submitCommands,
  getGame: mocks.getGame,
  getTurnStatus: mocks.getTurnStatus,
  resolveTurn: mocks.resolveTurn,
  getCommands: mocks.getCommands,
  ApiError: class ApiError extends Error {
    status: number;
    code: string;

    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
    }
  },
}));

function makeGalaxy(): Galaxy {
  return {
    galaxy: {
      name: "Test Galaxy",
      size: "small",
      seed: 123,
    },
    planets: [
      { id: "PL1", name: "Sol", x: 100, y: 200 },
    ],
  };
}

function makePlayerState(turn: number): PlayerState {
  return {
    player: "alice",
    turn,
    planets: [
      {
        id: "PL1",
        name: "Sol",
        x: 100,
        y: 200,
        owner: "alice",
        population: 25_000,
        scanLevel: "detailed",
        productionQueue: [
          {
            id: "PQ1",
            itemType: "factory",
            quantity: 3,
            progress: {
              resourcesSpent: 6,
              mineralsSpent: {
                ironium: 0,
                boranium: 0,
                germanium: 2,
              },
            },
          },
          {
            id: "PQ2",
            itemType: "mine",
            quantity: 1,
            progress: {
              resourcesSpent: 0,
              mineralsSpent: {
                ironium: 0,
                boranium: 0,
                germanium: 0,
              },
            },
          },
        ],
      },
    ],
    fleets: [
      {
        id: "FL1",
        owner: "alice",
        name: "Fleet #1",
        position: { x: 100, y: 200 },
        composition: [{ designId: "DS1", count: 1 }],
        waypoints: [],
      },
    ],
    designs: [
      {
        id: "DS1",
        owner: "alice",
        name: "Scout",
        hull: "Scout",
        speed: 4,
        scanner: { normal: 1, penetrating: 0 },
      },
    ],
    events: [],
  };
}

function makeGameDetail(turn: number, submittedByAlice: boolean, submittedByBob: boolean): GameDetail {
  return {
    gameId: "game-1",
    name: "Test Game",
    galaxySize: "small",
    turn,
    players: [
      { username: "alice", name: "Alice", submitted: submittedByAlice },
      { username: "bob", name: "Bob", submitted: submittedByBob },
    ],
    createdAt: "2026-03-30T12:00:00Z",
  };
}

async function flushHookUpdates() {
  await act(async () => {
    await Promise.resolve();
  });
  await act(async () => {
    await Promise.resolve();
  });
}

describe("useGameState", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mocks.getGalaxy.mockReset();
    mocks.getPlayerState.mockReset();
    mocks.submitCommands.mockReset();
    mocks.getGame.mockReset();
    mocks.getTurnStatus.mockReset();
    mocks.resolveTurn.mockReset();
    mocks.getCommands.mockReset();

    mocks.getGalaxy.mockResolvedValue(makeGalaxy());
    mocks.submitCommands.mockResolvedValue({
      status: "submitted",
      turn: 3,
      commandCount: 0,
    });
    mocks.resolveTurn.mockResolvedValue({
      turn: 4,
      status: "resolved",
    });
    mocks.getCommands.mockResolvedValue({ turn: 3, commands: [] });
    mocks.getTurnStatus.mockResolvedValue({ turn: 3 });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("polls the lightweight turn status endpoint while waiting after submit", async () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame
      .mockResolvedValueOnce(makeGameDetail(3, false, false))
      .mockResolvedValueOnce(makeGameDetail(3, true, false));
    mocks.getTurnStatus.mockResolvedValueOnce({ turn: 3 });

    const { result } = renderHook(() => useGameState("game-1", "alice"));

    await flushHookUpdates();

    expect(result.current.playerState?.turn).toBe(3);

    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.submitted).toBe(true);
    expect(result.current.gameDetail?.players[1]?.submitted).toBe(false);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    await flushHookUpdates();

    expect(mocks.getTurnStatus).toHaveBeenCalledWith("game-1", "alice");
    expect(result.current.gameDetail?.players[1]?.submitted).toBe(false);
  });

  it("reloads state when polling detects the next turn", async () => {
    mocks.getPlayerState
      .mockResolvedValueOnce(makePlayerState(3))
      .mockResolvedValueOnce(makePlayerState(4));
    mocks.getGame
      .mockResolvedValueOnce(makeGameDetail(3, false, false))
      .mockResolvedValueOnce(makeGameDetail(3, true, false))
      .mockResolvedValueOnce(makeGameDetail(4, false, false));
    mocks.getTurnStatus.mockResolvedValueOnce({ turn: 4 });

    const { result } = renderHook(() => useGameState("game-1", "alice"));

    await flushHookUpdates();

    expect(result.current.playerState?.turn).toBe(3);

    await act(async () => {
      await result.current.submit();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    await flushHookUpdates();

    expect(result.current.playerState?.turn).toBe(4);
    expect(result.current.submitted).toBe(false);
    expect(mocks.getGalaxy).toHaveBeenCalledTimes(2);
    expect(mocks.getPlayerState).toHaveBeenCalledTimes(2);
  });

  it("stages server-valid production queue commands and updates the working planet queue", async () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame.mockResolvedValue(makeGameDetail(3, false, false));

    const { result } = renderHook(() => useGameState("game-1", "alice"));
    await flushHookUpdates();

    act(() => {
      result.current.setPlanetProductionQueue("PL1", [
        {
          id: "PQ2",
          itemType: "mine",
          quantity: 1,
          progress: {
            resourcesSpent: 0,
            mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 },
          },
        },
        {
          id: "PQ1",
          itemType: "factory",
          quantity: 2,
          progress: {
            resourcesSpent: 6,
            mineralsSpent: { ironium: 0, boranium: 0, germanium: 2 },
          },
        },
        {
          id: "draft-1",
          itemType: "factory",
          quantity: 1,
          progress: {
            resourcesSpent: 0,
            mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 },
          },
        },
      ]);
    });

    expect(result.current.commands.commands).toEqual([
      {
        type: "move_production_item",
        planetId: "PL1",
        itemId: "PQ2",
        insertAfterItemId: null,
      },
      {
        type: "remove_production_item",
        planetId: "PL1",
        itemId: "PQ1",
        quantity: 1,
      },
      {
        type: "add_production_item",
        planetId: "PL1",
        itemType: "factory",
        quantity: 1,
        insertAfterItemId: "PQ1",
      },
    ]);

    expect(result.current.workingPlayerState?.planets[0]?.productionQueue).toEqual([
      expect.objectContaining({ id: "PQ2", itemType: "mine" }),
      expect.objectContaining({ id: "PQ1", itemType: "factory", quantity: 2 }),
      expect.objectContaining({ itemType: "factory", quantity: 1 }),
    ]);
  });

  it("keeps only the latest staged rename_fleet command for a fleet", async () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame.mockResolvedValue(makeGameDetail(3, false, false));

    const { result } = renderHook(() => useGameState("game-1", "alice"));
    await flushHookUpdates();

    act(() => {
      result.current.addCommand({
        type: "rename_fleet",
        fleetId: "FL1",
        name: "Vanguard",
      });
      result.current.addCommand({
        type: "rename_fleet",
        fleetId: "FL1",
        name: "Pathfinder",
      });
    });

    expect(result.current.commands.commands).toEqual([
      {
        type: "rename_fleet",
        fleetId: "FL1",
        name: "Pathfinder",
      },
    ]);
    expect(result.current.workingPlayerState?.fleets[0]?.name).toBe("Pathfinder");
  });
});
