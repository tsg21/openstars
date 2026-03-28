import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "./App";

// Mock the API client to avoid real network calls
vi.mock("./api/client", () => ({
  listGames: vi.fn().mockResolvedValue([]),
  getGalaxy: vi.fn().mockResolvedValue(null),
  getPlayerState: vi.fn().mockResolvedValue(null),
  getGame: vi.fn().mockResolvedValue(null),
  getCommands: vi.fn().mockResolvedValue({ turn: 0, commands: [] }),
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public code: string,
      message: string,
    ) {
      super(message);
    }
  },
}));

describe("App", () => {
  beforeEach(() => {
    // Clear URL params so lobby is shown
    window.history.pushState({}, "", "/");
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
