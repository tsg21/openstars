import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameLobby } from "./GameLobby";
import type { GameSummary } from "../../api/client";

const mocks = vi.hoisted(() => ({
  listGames: vi.fn(),
  createGame: vi.fn(),
}));

vi.mock("../../api/client", () => ({
  listGames: mocks.listGames,
  createGame: mocks.createGame,
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

const SIGNED_IN = "alice@example.com";

function makeGame(overrides: Partial<GameSummary> = {}): GameSummary {
  return {
    gameId: "g1",
    name: "Test Game",
    galaxySize: "small",
    turn: 1,
    players: [SIGNED_IN, "bob@example.com"],
    allTurnsSubmitted: false,
    createdAt: "2026-01-01T00:00:00Z",
    allowPlayerOverride: false,
    ...overrides,
  };
}

function renderLobby(props: Partial<Parameters<typeof GameLobby>[0]> = {}) {
  const onJoinGame = vi.fn();
  const onSignOut = vi.fn();
  const onSessionChanged = vi.fn();
  render(
    <GameLobby
      onJoinGame={onJoinGame}
      signedInAs={SIGNED_IN}
      onSignOut={onSignOut}
      onSessionChanged={onSessionChanged}
      {...props}
    />,
  );
  return { onJoinGame, onSignOut, onSessionChanged };
}

describe("GameLobby", () => {
  beforeEach(() => {
    mocks.listGames.mockReset();
    mocks.createGame.mockReset();
    mocks.listGames.mockResolvedValue([]);
    mocks.createGame.mockResolvedValue({ gameId: "new" });
  });

  it("shows loading state while games are being fetched", () => {
    mocks.listGames.mockReturnValue(new Promise(() => {}));

    renderLobby();

    expect(
      screen.getByRole("img", { name: "Stars! cover art" }),
    ).toHaveAttribute(
      "src",
      "https://storage.googleapis.com/openstars-assets/stars.jpg",
    );
    expect(screen.getByText("Loading games…")).toBeInTheDocument();
  });

  it("shows load error with retry button and retries successfully", async () => {
    mocks.listGames
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce([]);

    renderLobby();

    await waitFor(() => {
      expect(screen.getByText("Failed to load games")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(mocks.listGames).toHaveBeenCalledTimes(2);
    });
    await waitFor(() => {
      expect(
        screen.getByText("No games yet. Create one to get started."),
      ).toBeInTheDocument();
    });
  });

  describe("identity", () => {
    it("displays the signed-in email", async () => {
      renderLobby();
      await waitFor(() =>
        expect(screen.getByText(/Signed in as/)).toHaveTextContent(SIGNED_IN),
      );
    });

    it("prefers the display name when there is one", async () => {
      renderLobby({ displayName: "Alice" });
      await waitFor(() =>
        expect(screen.getByText(/Signed in as/)).toHaveTextContent(
          `Alice (${SIGNED_IN})`,
        ),
      );
    });

    it("offers a sign-out action", async () => {
      const { onSignOut } = renderLobby();
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument(),
      );

      fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
      expect(onSignOut).toHaveBeenCalledOnce();
    });
  });

  describe("joining", () => {
    it("joins a strict game directly as the signed-in email, with no picker", async () => {
      mocks.listGames.mockResolvedValue([makeGame()]);
      const { onJoinGame } = renderLobby();

      await waitFor(() =>
        expect(screen.getByText("Test Game")).toBeInTheDocument(),
      );
      fireEvent.click(screen.getByText("Test Game"));

      expect(onJoinGame).toHaveBeenCalledWith("g1", null);
      expect(screen.queryByText(/Join "Test Game" as:/)).not.toBeInTheDocument();
    });

    it("shows the picker for an override game", async () => {
      mocks.listGames.mockResolvedValue([
        makeGame({ allowPlayerOverride: true, players: ["tim", "matt"] }),
      ]);
      const { onJoinGame } = renderLobby();

      await waitFor(() =>
        expect(screen.getByText("Test Game")).toBeInTheDocument(),
      );
      fireEvent.click(screen.getByText("Test Game"));

      expect(screen.getByText('Join "Test Game" as:')).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "matt" }));
      expect(onJoinGame).toHaveBeenCalledWith("g1", "matt");
    });

    it("reports the mismatch when a strict game does not contain the signed-in email", async () => {
      mocks.listGames.mockResolvedValue([
        makeGame({ players: ["bob@example.com"] }),
      ]);
      const { onJoinGame } = renderLobby();

      await waitFor(() =>
        expect(screen.getByText("Test Game")).toBeInTheDocument(),
      );
      fireEvent.click(screen.getByText("Test Game"));

      expect(screen.getByText('Cannot join "Test Game"')).toBeInTheDocument();
      expect(
        screen.getByText(`${SIGNED_IN} is not a player in this game.`),
      ).toBeInTheDocument();
      expect(onJoinGame).not.toHaveBeenCalled();
    });
  });

  describe("creating", () => {
    async function openCreateForm() {
      await waitFor(() =>
        expect(
          screen.getByRole("button", { name: "+ New Game" }),
        ).toBeInTheDocument(),
      );
      fireEvent.click(screen.getByRole("button", { name: "+ New Game" }));
    }

    it("prefills the creator's email and labels the field for emails", async () => {
      renderLobby();
      await openCreateForm();

      // FormField renders an unassociated <label>, so query the input directly.
      expect(screen.getByText("Players (comma-separated emails)")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("alice@example.com")).toHaveValue(
        SIGNED_IN,
      );
    });

    it("sends allow_player_override false by default", async () => {
      renderLobby();
      await openCreateForm();

      fireEvent.change(screen.getByPlaceholderText("My Game"), {
        target: { value: "My Game" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Create" }));

      await waitFor(() =>
        expect(mocks.createGame).toHaveBeenCalledWith(
          "My Game",
          "small",
          [SIGNED_IN],
          false,
        ),
      );
    });

    it("sends allow_player_override true when the checkbox is ticked", async () => {
      renderLobby();
      await openCreateForm();

      fireEvent.change(screen.getByPlaceholderText("My Game"), {
        target: { value: "My Game" },
      });
      fireEvent.click(
        screen.getByLabelText("Allow play-as-any-player (testing)"),
      );
      fireEvent.click(screen.getByRole("button", { name: "Create" }));

      await waitFor(() =>
        expect(mocks.createGame).toHaveBeenCalledWith(
          "My Game",
          "small",
          [SIGNED_IN],
          true,
        ),
      );
    });

    it("refreshes the session after a successful create", async () => {
      const { onSessionChanged } = renderLobby();
      await openCreateForm();

      fireEvent.change(screen.getByPlaceholderText("My Game"), {
        target: { value: "My Game" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Create" }));

      // Without this the new game is absent from the `games` claim and its
      // Firestore listener cannot attach.
      await waitFor(() => expect(onSessionChanged).toHaveBeenCalledOnce());
    });

    it("does not refresh the session when create fails", async () => {
      mocks.createGame.mockRejectedValue(new Error("boom"));
      const { onSessionChanged } = renderLobby();
      await openCreateForm();

      fireEvent.change(screen.getByPlaceholderText("My Game"), {
        target: { value: "My Game" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Create" }));

      await waitFor(() =>
        expect(screen.getByText("Failed to create game")).toBeInTheDocument(),
      );
      expect(onSessionChanged).not.toHaveBeenCalled();
    });
  });
});
