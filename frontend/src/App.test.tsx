import { useEffect, useState, type ReactNode } from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "./App";
import type { PlayerState, Galaxy } from "./types";

vi.mock("./components", () => ({
  TopBar: ({ gameName }: { gameName: string }) => <div>{gameName}</div>,
  DesktopGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  Button: ({
    children,
    onClick,
  }: {
    children: ReactNode;
    onClick?: () => void;
  }) => <button onClick={onClick}>{children}</button>,
  GalaxyMap: ({
    playerState,
    onSelect,
  }: {
    playerState: PlayerState | null;
    onSelect: (selection: { kind: "fleet"; id: string } | null) => void;
  }) => (
    <div>
      {playerState?.fleets.map((fleet) => (
        <button
          key={fleet.id}
          onClick={() => onSelect({ kind: "fleet", id: fleet.id })}
        >
          Select {fleet.name ?? fleet.id}
        </button>
      ))}
    </div>
  ),
  DetailPanel: ({
    selectedFleet,
    selectedTurn,
    onWaypointEditorStateChange,
    onNewCommand,
  }: {
    selectedFleet: PlayerState["fleets"][number] | null;
    selectedTurn: number;
    onWaypointEditorStateChange: (state: {
      waypointEditMode: boolean;
      editingFleetId: string | null;
      editedWaypoints: unknown[] | null;
      onEnterWaypointMode?: () => void;
      onExitWaypointMode?: () => void;
    }) => void;
    onNewCommand: (command: { type: "rename_fleet"; fleetId: string; name: string }) => void;
  }) => {
    const [waypointEditMode, setWaypointEditMode] = useState(false);

    useEffect(() => {
      setWaypointEditMode(false);
    }, [selectedFleet?.id, selectedTurn]);

    useEffect(() => {
      if (!selectedFleet) {
        onWaypointEditorStateChange({
          waypointEditMode: false,
          editingFleetId: null,
          editedWaypoints: null,
        });
        return;
      }

      const enterWaypointMode = () => setWaypointEditMode(true);
      const exitWaypointMode = () => setWaypointEditMode(false);

      onWaypointEditorStateChange({
        waypointEditMode,
        editingFleetId: waypointEditMode ? selectedFleet.id : null,
        editedWaypoints: waypointEditMode ? [] : null,
        onEnterWaypointMode: enterWaypointMode,
        onExitWaypointMode: exitWaypointMode,
      });
    }, [onWaypointEditorStateChange, selectedFleet, waypointEditMode]);

    return (
      <div>
        {selectedFleet ? (
          <>
            <div>Selected fleet: {selectedFleet.name ?? selectedFleet.id}</div>
            {!waypointEditMode ? (
              <button onClick={() => setWaypointEditMode(true)}>Edit waypoints</button>
            ) : (
              <button onClick={() => setWaypointEditMode(false)}>Done</button>
            )}
            <button
              onClick={() =>
                onNewCommand({
                  type: "rename_fleet",
                  fleetId: selectedFleet.id,
                  name: "Vanguard",
                })
              }
            >
              Stage rename command
            </button>
          </>
        ) : (
          <div>No selection</div>
        )}
      </div>
    );
  },
  EventLog: () => <div>Event log</div>,
}));

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
        name: "Fleet #1",
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

    act(() => {
      screen.getByRole("button", { name: /select fleet #1/i }).click();
    });

    act(() => {
      screen.getByRole("button", { name: /edit waypoints/i }).click();
    });
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /done/i })).toBeInTheDocument();
    });

    // Simulate turn advancing
    mockUseGameState.mockReturnValue(makeGameStateReturn(2));
    rerender(<App />);

    await waitFor(() => {
      // "Done" button (edit mode active) should be gone
      expect(screen.queryByRole("button", { name: /done/i })).not.toBeInTheDocument();
    });
  });
});

describe("App — fleet rename flow", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?game=game-1&player=alice");
  });

  it("passes fleet commands from the detail panel into top-level staged commands", async () => {
    const gameState = makeGameStateReturn(1);
    mockUseGameState.mockReturnValue(gameState);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Test Game")).toBeInTheDocument();
    });

    act(() => {
      screen.getByRole("button", { name: /select fleet #1/i }).click();
    });
    act(() => {
      screen.getByRole("button", { name: /stage rename command/i }).click();
    });

    expect(gameState.setCommand).toHaveBeenCalledWith({
      type: "rename_fleet",
      fleetId: "FL1",
      name: "Vanguard",
    });
  });
});
