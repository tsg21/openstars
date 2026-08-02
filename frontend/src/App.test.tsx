import { useEffect, useState, type ReactNode } from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "./App";
import type { PlayerState, Galaxy } from "./types";
import { useGameCommands } from "./hooks/useGameCommands";

vi.mock("./components", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./components")>();
  return {
    ...actual,
  TopBar: ({
    gameName,
    mode,
    onModeChange,
    research,
    productionEnabled,
  }: {
    gameName: string;
    mode: "command" | "production" | "designer" | "research";
    onModeChange: (mode: "command" | "production" | "designer" | "research") => void;
    research: PlayerState["research"];
    productionEnabled?: boolean;
  }) => (
    <div>
      <div>{gameName}</div>
      <button
        aria-pressed={mode === "command"}
        onClick={() => onModeChange("command")}
      >
        Command
      </button>
      <button
        aria-pressed={mode === "production"}
        disabled={!productionEnabled}
        onClick={() => { if (productionEnabled) onModeChange("production"); }}
      >
        Production
      </button>
      <button
        aria-pressed={mode === "designer"}
        onClick={() => onModeChange("designer")}
      >
        Designer
      </button>
      {research && (
        <button
          aria-pressed={mode === "research"}
          onClick={() => onModeChange("research")}
        >
          Research
        </button>
      )}
    </div>
  ),
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
  }) => {
    const { addCommand } = useGameCommands();
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
                addCommand({
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
  DesignsWorkspace: ({ gameId, player }: { gameId: string; player: string }) => (
    <div>Designs workspace for {gameId}:{player}</div>
  ),
  ResearchWorkspace: () => <div>Research workspace</div>,
  RaceSelectionScreen: () => <div>Race selection screen</div>,
  ProductionWorkspace: ({ initialPlanetId }: { initialPlanetId: string | null }) => (
    <div>Production workspace{initialPlanetId ? ` for ${initialPlanetId}` : ""}</div>
  ),
  };
});

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

// App owns the session hook; without this the real module initialises the
// Firebase SDK and fails on the absent API key. Tests mutate `authState` to
// drive the gate.
const { authState, signInMock, signOutMock, refreshSessionMock } = vi.hoisted(
  () => ({
    authState: {
      status: "signed-in" as
        | "loading"
        | "signed-out"
        | "signed-in"
        | "error",
      user: { email: "tim", displayName: "Tim" } as {
        email: string;
        displayName: string | null;
      } | null,
      games: [] as string[],
      error: null as Error | null,
    },
    signInMock: vi.fn(),
    signOutMock: vi.fn(),
    refreshSessionMock: vi.fn(),
  }),
);

vi.mock("./hooks/useAuth", () => ({
  useAuth: () => ({
    ...authState,
    signIn: signInMock,
    signOut: signOutMock,
    refreshSession: refreshSessionMock,
  }),
}));

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
        components: [],
        mass: 25,
        fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        fuelCapacity: 50,
        scanner: { normal: 1, penetrating: 0 },
        cargoCapacity: 0,
        cost: {
          resources: 15,
          minerals: { ironium: 5, boranium: 3, germanium: 2 },
        },
      },
    ],
    events: [],
    research: null,
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

function makeResearchState(): NonNullable<PlayerState["research"]> {
  return {
    levels: {
      energy: 3,
      weapons: 2,
      propulsion: 1,
      construction: 0,
      electronics: 0,
      biotechnology: 0,
    },
    progress: {
      energy: 20,
      weapons: 0,
      propulsion: 0,
      construction: 0,
      electronics: 0,
      biotechnology: 0,
    },
    currentField: "energy",
    nextField: "weapons",
    allocationPercent: 15,
    remainingCost: {
      energy: 80,
      weapons: 100,
      propulsion: 100,
      construction: 100,
      electronics: 100,
      biotechnology: 100,
    },
    reservableResourcesThisTurn: 200,
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
      allowPlayerOverride: false,
    },
    turnStatus: { turn, playersAwaitingSubmission: [] },
    isDirty: false,
    submitted: false,
    commands: { commands: [] },
    addCommand: vi.fn(),
    setPlanetProductionQueue: vi.fn(),
    replaceCommands: vi.fn(),
          nextTmpFleetId: vi.fn(() => "tmp_1"),
    submit: vi.fn(),
    resolve: vi.fn(),
    refresh: vi.fn(),
  };
}

function signedIn() {
  Object.assign(authState, {
    status: "signed-in" as const,
    user: { email: "alice", displayName: "Alice" },
    games: [],
    error: null,
  });
}

describe("App — sign-in gate", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
    signedIn();
    mockUseGameState.mockReturnValue(makeGameStateReturn(1));
  });

  it("renders the sign-in screen and no lobby when signed out", async () => {
    Object.assign(authState, { status: "signed-out", user: null });
    render(<App />);

    expect(
      screen.getByRole("button", { name: "Sign in with Google" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Create Game")).not.toBeInTheDocument();
    expect(screen.queryByText("Test Game")).not.toBeInTheDocument();
  });

  it("renders neither sign-in nor lobby while loading", () => {
    Object.assign(authState, { status: "loading", user: null });
    render(<App />);

    expect(
      screen.queryByRole("button", { name: "Sign in with Google" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Create Game")).not.toBeInTheDocument();
  });

  it("renders the lobby when signed in with no game selected", async () => {
    signedIn();
    render(<App />);

    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Sign in with Google" }),
      ).not.toBeInTheDocument(),
    );
    expect(screen.getByText("OpenStars!")).toBeInTheDocument();
  });

  it("offers a retry in the error state that re-invokes sign-in", async () => {
    Object.assign(authState, {
      status: "error",
      user: null,
      error: new Error("popup blocked"),
    });
    render(<App />);

    expect(screen.getByText("popup blocked")).toBeInTheDocument();
    const retry = screen.getByRole("button", { name: "Try again" });
    act(() => retry.click());

    expect(signInMock).toHaveBeenCalled();
  });
});

describe("App — ?player= override", () => {
  beforeEach(() => {
    signedIn();
  });

  it("ignores ?player= for a non-override game", async () => {
    window.history.pushState({}, "", "/?game=game-1&player=someone-else");
    mockUseGameState.mockReturnValue(makeGameStateReturn(1));

    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Test Game")).toBeInTheDocument(),
    );

    // The strict game strips the parameter rather than advertising an identity
    // the app no longer takes from it.
    await waitFor(() =>
      expect(new URLSearchParams(window.location.search).get("player")).toBeNull(),
    );
    expect(mockUseGameState).toHaveBeenLastCalledWith(
      "game-1",
      "alice",
      expect.anything(),
    );
  });

  it("honours ?player= for an override game", async () => {
    window.history.pushState({}, "", "/?game=game-1&player=someone-else");
    const gs = makeGameStateReturn(1);
    gs.gameDetail.allowPlayerOverride = true;
    mockUseGameState.mockReturnValue(gs);

    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Test Game")).toBeInTheDocument(),
    );

    expect(new URLSearchParams(window.location.search).get("player")).toBe(
      "someone-else",
    );
    expect(mockUseGameState).toHaveBeenLastCalledWith(
      "game-1",
      "someone-else",
      expect.anything(),
    );
  });
});

describe("App", () => {
  beforeEach(() => {
    // Clear URL params so lobby is shown
    window.history.pushState({}, "", "/");
    signedIn();
    // Default mock: minimal state sufficient for lobby (no game/player)
    mockUseGameState.mockReturnValue({
      loading: false,
      error: null,
      galaxy: null,
      playerState: null,
      workingPlayerState: null,
      gameDetail: null,
      turnStatus: null,
      isDirty: false,
      submitted: false,
      commands: { commands: [] },
      addCommand: vi.fn(),
      setPlanetProductionQueue: vi.fn(),
      replaceCommands: vi.fn(),
          nextTmpFleetId: vi.fn(() => "tmp_1"),
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

describe("App — mode switch", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?game=game-1&player=alice");
    signedIn();
  });

  it("switches to Designs mode and shows designs workspace", async () => {
    mockUseGameState.mockReturnValue(makeGameStateReturn(1));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Test Game")).toBeInTheDocument();
    });

    act(() => {
      screen.getByRole("button", { name: "Designer" }).click();
    });

    await waitFor(() => {
      expect(screen.getByText("Designs workspace for game-1:alice")).toBeInTheDocument();
    });
  });

  it("switches to Research mode and shows research workspace", async () => {
    const gameState = makeGameStateReturn(1);
    gameState.playerState.research = makeResearchState();
    gameState.workingPlayerState.research = gameState.playerState.research;
    mockUseGameState.mockReturnValue(gameState);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Test Game")).toBeInTheDocument();
    });

    act(() => {
      screen.getByRole("button", { name: "Research" }).click();
    });

    await waitFor(() => {
      expect(screen.getByText("Research workspace")).toBeInTheDocument();
    });
  });
});

describe("App — turn advance clears waypoint edit state", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?game=game-1&player=alice");
    signedIn();
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
    signedIn();
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

    expect(gameState.addCommand).toHaveBeenCalledWith({
      type: "rename_fleet",
      fleetId: "FL1",
      name: "Vanguard",
    });
  });
});

function makeGameStateWithPlanets(turn: number) {
  const gs = makeGameStateReturn(turn);
  const planet = {
    id: "PL001",
    name: "Earth",
    x: 100,
    y: 200,
    owner: "alice",
    scanLevel: "detailed" as const,
    scanAge: 0,
    productionQueue: [],
    starbase: null,
    scanner: null,
    contributeOnlyLeftoverToResearch: false,
  };
  gs.playerState.planets = [planet];
  gs.workingPlayerState.planets = [planet];
  return gs;
}

describe("App — production mode keyboard shortcuts", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?game=game-1&player=alice");
    signedIn();
  });

  it("pressing P toggles between Command and Production", async () => {
    mockUseGameState.mockReturnValue(makeGameStateWithPlanets(1));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "p", bubbles: true })); });
    await waitFor(() => expect(screen.getByText(/Production workspace/)).toBeInTheDocument());

    act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "p", bubbles: true })); });
    await waitFor(() => expect(screen.queryByText(/Production workspace/)).not.toBeInTheDocument());
  });

  it("pressing P while an input is focused does not toggle", async () => {
    mockUseGameState.mockReturnValue(makeGameStateWithPlanets(1));
    const { container } = render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    const input = document.createElement("input");
    container.appendChild(input);
    input.focus();

    act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "p", bubbles: true })); });
    expect(screen.queryByText(/Production workspace/)).not.toBeInTheDocument();
  });

  it("P does not fire when modifier keys are held", async () => {
    mockUseGameState.mockReturnValue(makeGameStateWithPlanets(1));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "p", ctrlKey: true, bubbles: true })); });
    expect(screen.queryByText(/Production workspace/)).not.toBeInTheDocument();
  });

  it("Esc from Production returns to Command", async () => {
    mockUseGameState.mockReturnValue(makeGameStateWithPlanets(1));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "p", bubbles: true })); });
    await waitFor(() => expect(screen.getByText(/Production workspace/)).toBeInTheDocument());

    act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true })); });
    await waitFor(() => expect(screen.queryByText(/Production workspace/)).not.toBeInTheDocument());
  });
});

describe("App — production mode wiring", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?game=game-1&player=alice");
    signedIn();
  });

  it("clicking Production tab mounts the workspace", async () => {
    mockUseGameState.mockReturnValue(makeGameStateWithPlanets(1));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    act(() => { screen.getByRole("button", { name: "Production" }).click(); });
    await waitFor(() => expect(screen.getByText(/Production workspace/)).toBeInTheDocument());
  });

  it("Production tab is disabled when there are no owned planets", async () => {
    mockUseGameState.mockReturnValue(makeGameStateReturn(1));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    expect(screen.getByRole("button", { name: "Production" })).toBeDisabled();
  });

  it("mode falls back to command when owned planets becomes empty while in production", async () => {
    const gs = makeGameStateWithPlanets(1);
    mockUseGameState.mockReturnValue(gs);
    const { rerender } = render(<App />);
    await waitFor(() => expect(screen.getByText("Test Game")).toBeInTheDocument());

    act(() => { screen.getByRole("button", { name: "Production" }).click(); });
    await waitFor(() => expect(screen.getByText(/Production workspace/)).toBeInTheDocument());

    const gsEmpty = makeGameStateReturn(1);
    mockUseGameState.mockReturnValue(gsEmpty);
    rerender(<App />);

    await waitFor(() => expect(screen.queryByText(/Production workspace/)).not.toBeInTheDocument());
  });
});
