/**
 * Integration coverage for the whole signed-in journey (task step 8):
 * sign-in → lobby → join → sign-out.
 *
 * Only the Firebase SDK and the API client are mocked; useAuth, App, the gate
 * and the lobby are all real, so this exercises the wiring the unit tests stub.
 */

import { render, screen, waitFor, act, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

const {
  signInWithPopupMock,
  signOutMock,
  onAuthStateChangedMock,
  getIdTokenMock,
  onSnapshotMock,
  apiMocks,
} = vi.hoisted(() => ({
  signInWithPopupMock: vi.fn(),
  signOutMock: vi.fn(),
  onAuthStateChangedMock: vi.fn(),
  getIdTokenMock: vi.fn(),
  onSnapshotMock: vi.fn(),
  apiMocks: {
    listGames: vi.fn(),
    createGame: vi.fn(),
    getGame: vi.fn(),
    getGalaxy: vi.fn(),
    getPlayerState: vi.fn(),
    getCommands: vi.fn(),
    getTurnStatus: vi.fn(),
    postAuthSession: vi.fn(),
    setAuthTokenGetter: vi.fn(),
    getDesigns: vi.fn(),
    getDesignerReferenceData: vi.fn(),
    getDesignDetail: vi.fn(),
    createDesign: vi.fn(),
    getRace: vi.fn(),
    getPredefinedRaces: vi.fn(),
    previewRace: vi.fn(),
    submitCommands: vi.fn(),
  },
}));

vi.mock("firebase/auth", () => ({
  signInWithPopup: signInWithPopupMock,
  signOut: signOutMock,
  onAuthStateChanged: onAuthStateChangedMock,
  GoogleAuthProvider: class {},
}));

vi.mock("./lib/firebase", () => ({
  firebaseAuth: { currentUser: null },
  googleProvider: {},
  firebaseDb: {},
}));

vi.mock("firebase/firestore", () => ({
  doc: vi.fn(() => ({})),
  onSnapshot: onSnapshotMock,
}));

vi.mock("./api/client", () => ({
  ...apiMocks,
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

vi.mock("./components/ui/DesktopGate", () => ({
  DesktopGate: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

import App from "./App";
import { firebaseAuth } from "./lib/firebase";

const EMAIL = "alice@example.com";
let emitAuthState: (user: unknown) => void = () => {};
const user = { uid: "uid-1", getIdToken: getIdTokenMock };

function makeSummary(overrides = {}) {
  return {
    gameId: "g1",
    name: "Andromeda",
    galaxySize: "small",
    turn: 1,
    players: [EMAIL],
    allTurnsSubmitted: false,
    createdAt: "2026-01-01T00:00:00Z",
    allowPlayerOverride: false,
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  window.history.pushState({}, "", "/");
  (firebaseAuth as { currentUser: unknown }).currentUser = null;

  onAuthStateChangedMock.mockImplementation((_auth, cb) => {
    emitAuthState = cb;
    return () => {};
  });
  getIdTokenMock.mockResolvedValue("token");
  onSnapshotMock.mockReturnValue(() => {});

  apiMocks.postAuthSession.mockResolvedValue({
    username: EMAIL,
    displayName: "Alice",
    games: ["g1"],
  });
  apiMocks.listGames.mockResolvedValue([makeSummary()]);
  apiMocks.getGame.mockResolvedValue({
    gameId: "g1",
    name: "Andromeda",
    galaxySize: "small",
    turn: 1,
    players: [{ username: EMAIL, name: "Alice", submitted: false }],
    createdAt: "2026-01-01T00:00:00Z",
    allowPlayerOverride: false,
  });
  apiMocks.getGalaxy.mockResolvedValue({
    galaxy: { name: "Andromeda", size: "small", seed: 1 },
    planets: [],
  });
  apiMocks.getPlayerState.mockResolvedValue({
    player: EMAIL,
    turn: 1,
    planets: [],
    designs: [],
    events: [],
    research: null,
    fleets: [],
  });
  apiMocks.getCommands.mockResolvedValue({ turn: 1, commands: [] });
  apiMocks.getTurnStatus.mockResolvedValue({
    turn: 1,
    playersAwaitingSubmission: [],
  });
  apiMocks.getDesigns.mockResolvedValue([]);
  apiMocks.getPredefinedRaces.mockResolvedValue([]);
  apiMocks.getRace.mockResolvedValue({ race: null, costBreakdown: null });
});

describe("sign-in → lobby → join → sign-out", () => {
  it("gates the lobby until sign-in succeeds, then joins and signs out", async () => {
    render(<App />);

    // 1. Signed out: the gate shows the sign-in screen and no game data.
    act(() => emitAuthState(null));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Sign in with Google" }),
      ).toBeInTheDocument(),
    );
    expect(apiMocks.listGames).not.toHaveBeenCalled();

    // 2. Sign in. onAuthStateChanged reports the user, useAuth establishes the
    //    session, and only then does the lobby become reachable.
    signInWithPopupMock.mockImplementation(async () => {
      (firebaseAuth as { currentUser: unknown }).currentUser = user;
      emitAuthState(user);
      return { user };
    });

    await act(async () => {
      screen.getByRole("button", { name: "Sign in with Google" }).click();
    });

    await waitFor(() =>
      expect(screen.getByText("Andromeda")).toBeInTheDocument(),
    );
    expect(apiMocks.postAuthSession).toHaveBeenCalled();
    // The claim must be written before the token is refreshed, or the Firestore
    // listener attaches with a token that cannot see the game.
    expect(getIdTokenMock).toHaveBeenCalledWith(true);
    expect(screen.getByText(/Signed in as/)).toHaveTextContent(EMAIL);

    // 3. Join the strict game: no picker, joined as the signed-in identity.
    await act(async () => {
      fireEvent.click(screen.getByText("Andromeda"));
    });

    await waitFor(() => expect(apiMocks.getGame).toHaveBeenCalled());
    expect(new URLSearchParams(window.location.search).get("game")).toBe("g1");
    expect(new URLSearchParams(window.location.search).get("player")).toBeNull();

    // The Firestore listener attaches under the refreshed claims.
    await waitFor(() => expect(onSnapshotMock).toHaveBeenCalled());

    // 4. Sign out: back to the gate, with nothing left from the old session.
    signOutMock.mockImplementation(async () => {
      (firebaseAuth as { currentUser: unknown }).currentUser = null;
      emitAuthState(null);
    });

    await act(async () => {
      screen.getByRole("button", { name: "Sign out" }).click();
    });

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Sign in with Google" }),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("Andromeda")).not.toBeInTheDocument();
    expect(new URLSearchParams(window.location.search).get("game")).toBeNull();
  });

  it("honours the override picker for a game that allows it", async () => {
    apiMocks.listGames.mockResolvedValue([
      makeSummary({ allowPlayerOverride: true, players: ["tim", "matt"] }),
    ]);
    apiMocks.getGame.mockResolvedValue({
      gameId: "g1",
      name: "Andromeda",
      galaxySize: "small",
      turn: 1,
      players: [
        { username: "tim", name: "tim", submitted: false },
        { username: "matt", name: "matt", submitted: false },
      ],
      createdAt: "2026-01-01T00:00:00Z",
      allowPlayerOverride: true,
    });

    render(<App />);
    (firebaseAuth as { currentUser: unknown }).currentUser = user;
    act(() => emitAuthState(user));

    await waitFor(() =>
      expect(screen.getByText("Andromeda")).toBeInTheDocument(),
    );

    await act(async () => {
      fireEvent.click(screen.getByText("Andromeda"));
    });

    expect(screen.getByText('Join "Andromeda" as:')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "matt" }));
    });

    // An override game keeps the deep-link parameter, because it means something.
    await waitFor(() =>
      expect(new URLSearchParams(window.location.search).get("player")).toBe(
        "matt",
      ),
    );
  });
});
