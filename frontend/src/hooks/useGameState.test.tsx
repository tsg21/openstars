import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { Galaxy, PlayerState } from "../types";
import type { GameDetail } from "../api/client";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mocks = vi.hoisted(() => ({
  getGalaxy: vi.fn(),
  getPlayerState: vi.fn(),
  submitCommands: vi.fn(),
  getGame: vi.fn(),
  getTurnStatus: vi.fn(),
  getCommands: vi.fn(),
  getDesigns: vi.fn(),
}));

vi.mock("../api/client", () => ({
  getGalaxy: mocks.getGalaxy,
  getPlayerState: mocks.getPlayerState,
  submitCommands: mocks.submitCommands,
  getGame: mocks.getGame,
  getTurnStatus: mocks.getTurnStatus,
  getCommands: mocks.getCommands,
  getDesigns: mocks.getDesigns,
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

vi.mock("./useGameNotifications", () => ({
  useGameNotifications: () => ({ error: null }),
}));

import { useGameState } from "./useGameState";

// ---------------------------------------------------------------------------
// Test data builders
// ---------------------------------------------------------------------------

function makeGalaxy(): Galaxy {
  return {
    galaxy: { name: "Test Galaxy", size: "small", seed: 123 },
    planets: [{ id: "PL1", name: "Sol", x: 100, y: 200 }],
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
        scanAge: 0,
        productionQueue: [
          {
            id: "PQ1",
            itemType: "factory",
            quantity: 3,
            progress: {
              resourcesSpent: 6,
              mineralsSpent: { ironium: 0, boranium: 0, germanium: 2 },
            },
          },
          {
            id: "PQ2",
            itemType: "mine",
            quantity: 1,
            progress: {
              resourcesSpent: 0,
              mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 },
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
        components: [],
        mass: 25,
        fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        fuelCapacity: 50,
        scanner: { normal: 1, penetrating: 0 },
        cargoCapacity: 0,
        cost: { resources: 15, minerals: { ironium: 5, boranium: 3, germanium: 2 } },
      },
    ],
    events: [],
  };
}

const TEST_AUTH = { games: [], refreshSession: vi.fn() };

function makeGameDetail(
  turn: number,
  submittedByAlice: boolean,
  submittedByBob: boolean,
): GameDetail {
  return {
    gameId: "game-1",
    name: "Test Game",
    galaxySize: "small",
    allowPlayerOverride: false,
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useGameState", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.values(mocks).forEach((m) => m.mockReset());

    mocks.getGalaxy.mockResolvedValue(makeGalaxy());
    mocks.submitCommands.mockResolvedValue({
      status: "submitted",
      turn: 3,
      commandCount: 0,
      turnResolved: false,
      newTurn: null,
    });
    mocks.getCommands.mockResolvedValue({ turn: 3, commands: [] });
    mocks.getTurnStatus.mockResolvedValue({ turn: 3, playersAwaitingSubmission: [] });
    mocks.getDesigns.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not poll with setTimeout after submit (uses Firestore listener instead)", async () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame.mockResolvedValue(makeGameDetail(3, false, false));

    const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");

    const { result } = renderHook(() => useGameState("game-1", "alice", TEST_AUTH));
    await flushHookUpdates();

    await act(async () => {
      await result.current.submit();
    });

    // Any setTimeout calls should not be for 10s polling
    const pollingCalls = setTimeoutSpy.mock.calls.filter(
      ([, delay]) => typeof delay === "number" && delay >= 10_000,
    );
    expect(pollingCalls).toHaveLength(0);
    setTimeoutSpy.mockRestore();
  });

  it("reloads state when turn resolves immediately on submit", async () => {
    mocks.getPlayerState
      .mockResolvedValueOnce(makePlayerState(3))
      .mockResolvedValueOnce(makePlayerState(4));
    mocks.getGame
      .mockResolvedValueOnce(makeGameDetail(3, false, false))
      .mockResolvedValueOnce(makeGameDetail(4, false, false));
    mocks.getTurnStatus
      .mockResolvedValueOnce({ turn: 3, playersAwaitingSubmission: ["alice", "bob"] })
      .mockResolvedValueOnce({ turn: 4, playersAwaitingSubmission: ["alice", "bob"] });
    mocks.submitCommands.mockResolvedValue({
      status: "submitted",
      turn: 3,
      commandCount: 0,
      turnResolved: true,
      newTurn: 4,
    });

    const { result } = renderHook(() => useGameState("game-1", "alice", TEST_AUTH));
    await flushHookUpdates();

    await act(async () => {
      await result.current.submit();
    });
    await flushHookUpdates();

    expect(result.current.playerState?.turn).toBe(4);
  });

  it("stages server-valid production queue commands and updates the working planet queue", async () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame.mockResolvedValue(makeGameDetail(3, false, false));

    const { result } = renderHook(() => useGameState("game-1", "alice", TEST_AUTH));
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
      { type: "move_production_item", planetId: "PL1", itemId: "PQ2", insertAfterItemId: null },
      { type: "remove_production_item", planetId: "PL1", itemId: "PQ1", quantity: 1 },
      { type: "add_production_item", planetId: "PL1", itemType: "factory", quantity: 1, insertAfterItemId: "PQ1" },
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

    const { result } = renderHook(() => useGameState("game-1", "alice", TEST_AUTH));
    await flushHookUpdates();

    act(() => {
      result.current.addCommand({ type: "rename_fleet", fleetId: "FL1", name: "Vanguard" });
      result.current.addCommand({ type: "rename_fleet", fleetId: "FL1", name: "Pathfinder" });
    });

    expect(result.current.commands.commands).toEqual([
      { type: "rename_fleet", fleetId: "FL1", name: "Pathfinder" },
    ]);
    expect(result.current.workingPlayerState?.fleets[0]?.name).toBe("Pathfinder");
  });

  it("replaces research-scoped commands atomically", async () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame.mockResolvedValue(makeGameDetail(3, false, false));

    const { result } = renderHook(() => useGameState("game-1", "alice", TEST_AUTH));
    await flushHookUpdates();

    act(() => {
      result.current.replaceCommands({ kind: "research" }, [{ type: "set_research", currentField: "weapons" }]);
      result.current.replaceCommands({ kind: "research" }, [{ type: "set_research", currentField: "construction" }]);
    });

    expect(
      result.current.commands.commands.filter((cmd) => cmd.type === "set_research"),
    ).toEqual([{ type: "set_research", currentField: "construction" }]);

    act(() => {
      result.current.replaceCommands({ kind: "research" }, []);
    });

    expect(
      result.current.commands.commands.filter((cmd) => cmd.type === "set_research"),
    ).toHaveLength(0);
  });

  it("exposes notificationsError (null when listener is healthy)", () => {
    mocks.getPlayerState.mockResolvedValue(makePlayerState(3));
    mocks.getGame.mockResolvedValue(makeGameDetail(3, false, false));

    const { result } = renderHook(() => useGameState("game-1", "alice", TEST_AUTH));
    // useGameNotifications is mocked to return { error: null }
    expect(result.current.notificationsError).toBeNull();
  });
});
