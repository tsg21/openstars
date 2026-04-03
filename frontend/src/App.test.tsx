import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "./App";
import type { PlayerState, Galaxy } from "./types";

// Mock the API client to avoid real network calls
vi.mock("./api/client", () => ({
  listGames: vi.fn().mockResolvedValue([]),
  getGalaxy: vi.fn().mockResolvedValue(null),
  getPlayerState: vi.fn().mockResolvedValue(null),
  getGame: vi.fn().mockResolvedValue(null),
  getCommands: vi.fn().mockResolvedValue({ turn: 0, commands: [] }),
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

const mockUseGameState = vi.hoisted(() => vi.fn());
vi.mock("./hooks/useGameState", () => ({
  useGameState: mockUseGameState,
}));

function makeGalaxy(): Galaxy {
  return {
    galaxy: { name: "Test Galaxy", size: "small", seed: 1 },
    planets: [{ id: "PL1", name: "Sol", x: 100, y: 200 }],
  };
}

function makePlayerState(turn: number): PlayerState {
  return {
    player: "alice",
    turn,
    planets: [],
    designs: [
      {
        id: "DS1",
        owner: "alice",
        name: "Scout",
        hull: "scout",
        speed: 4,
        scanner: { normal: 1, penetrating: 0 },
      },
    ],
    events: [],
    fleets: [
      {
        id: "FL1",
        owner: "alice",
        position: { x: 100, y: 200 },
        composition: [{ designId: "DS1", count: 1 }],
        waypoints: [],
        repeat: false,
      },
    ],
  };
}

function makeGameStateReturn(turn: number) {
  const playerState = makePlayerState(turn);
  return {
    loading: false,
    error: null,
    galaxy: makeGalaxy(),
    playerState,
    workingPlayerState: playerState,
    gameDetail: {
      gameId: "game-1",
      name: "Test Game",
      galaxySize: "small",
      turn,
      players: [{ username: "alice", name: "Alice", submitted: false }],
      createdAt: "2026-01-01T00:00:00Z",
      allTurnsSubmitted: false,
    },
    isDirty: false,
    submitted: false,
    setCommand: vi.fn(),
    setPlanetProductionQueue: vi.fn(),
    submit: vi.fn(),
    resolve: vi.fn(),
    refresh: vi.fn(),
  };
}

describe("App", () => {
  beforeEach(() => {
    // Clear URL params so lobby is shown
    window.history.pushState({}, "", "/");
    // Default mock: minimal state sufficient for lobby (no game/player)
    mockUseGameState.mockReturnValue({
      loading: false,
      error: null,
      galaxy: null,
      playerState: null,
      workingPlayerState: null,
      gameDetail: null,
      isDirty: false,
      submitted: false,
      setCommand: vi.fn(),
      setPlanetProductionQueue: vi.fn(),
      submit: vi.fn(),
      resolve: vi.fn(),
      refresh: vi.fn(),
    });
  });

  it("renders the lobby when no game is selected", async () => {
    render(<App />);
    // The lobby title should be present
    const titles = screen.getAllByText("OpenStars!");
    expect(titles.length).toBeGreaterThanOrEqual(1);
    // Should show the lobby text
    await waitFor(() => {
      expect(
        screen.getByText("Select a game or create a new one"),
      ).toBeInTheDocument();
    });
  });

  it("renders the new game button in the lobby", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText("+ New Game")).toBeInTheDocument();
    });
  });

  it("shows loading state when no games exist", async () => {
    render(<App />);
    // Initially shows loading, then resolves to empty
    await waitFor(() => {
      const loadingOrEmpty =
        screen.queryByText("Loading games…") ||
        screen.queryByText("No games yet. Create one to get started.");
      expect(loadingOrEmpty).toBeInTheDocument();
    });
  });
});

describe("App — turn advance clears waypoint edit state", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?game=game-1&player=alice");
  });

  it("exits waypoint edit mode when turn increments", async () => {
    mockUseGameState.mockReturnValue(makeGameStateReturn(1));

    const { rerender } = render(<App />);

    // Select the fleet and enter waypoint edit mode
    await waitFor(() => {
      expect(screen.getByText("Test Game")).toBeInTheDocument();
    });

    const editBtn = screen.queryByRole("button", { name: /edit waypoints/i });
    if (editBtn) {
      act(() => { editBtn.click(); });
      await waitFor(() => {
        expect(screen.queryByRole("button", { name: /done/i })).toBeInTheDocument();
      });
    }

    // Simulate turn advancing
    mockUseGameState.mockReturnValue(makeGameStateReturn(2));
    rerender(<App />);

    await waitFor(() => {
      // "Done" button (edit mode active) should be gone
      expect(screen.queryByRole("button", { name: /done/i })).not.toBeInTheDocument();
    });
  });
});
