import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameLobby } from "./GameLobby";

const mocks = vi.hoisted(() => ({
  listGames: vi.fn(),
  createGame: vi.fn(),
}));

vi.mock("../api/client", () => ({
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

describe("GameLobby", () => {
  beforeEach(() => {
    mocks.listGames.mockReset();
    mocks.createGame.mockReset();
  });

  it("shows loading state while games are being fetched", () => {
    mocks.listGames.mockReturnValue(new Promise(() => {}));

    render(<GameLobby onJoinGame={vi.fn()} />);

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

    render(<GameLobby onJoinGame={vi.fn()} />);

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
});
