import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  listGames,
  getPlayerState,
  getTurnStatus,
  submitCommands,
  ApiError,
} from "./client";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API client", () => {
  describe("snake_case / camelCase conversion", () => {
    it("converts snake_case response keys to camelCase", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          games: [
            {
              game_id: "test-abc123",
              name: "Test Game",
              galaxy_size: "small",
              turn: 0,
              players: ["alice", "bob"],
              all_turns_submitted: false,
              created_at: "2026-03-28T00:00:00Z",
            },
          ],
        }),
      });

      const result = await listGames();
      expect(result).toHaveLength(1);
      expect(result[0].gameId).toBe("test-abc123");
      expect(result[0].galaxySize).toBe("small");
      expect(result[0].allTurnsSubmitted).toBe(false);
    });

    it("converts player state with nested objects", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          player: "alice",
          turn: 1,
          planets: [
            {
              id: "PL000001",
              name: "Sol",
              x: 100,
              y: 200,
              owner: "alice",
              population: 25000,
            },
          ],
          fleets: [
            {
              id: "FL000001",
              owner: "alice",
              position: { x: 100, y: 200 },
              composition: [{ design_id: "DE000001", count: 1 }],
              waypoints: [{ x: 300, y: 400 }],
            },
          ],
          designs: [
            {
              id: "DE000001",
              owner: "alice",
              name: "Scout",
              hull: "scout",
              speed: 6,
              scanner: { normal: 150, penetrating: 0 },
            },
          ],
          events: [],
        }),
      });

      const state = await getPlayerState("game-1", "alice");
      expect(state.player).toBe("alice");
      expect(state.fleets[0].composition?.[0].designId).toBe("DE000001");
      expect(state.designs[0].scanner.normal).toBe(150);
      expect(state.designs[0].scanner.penetrating).toBe(0);
    });

    it("converts lightweight turn status responses", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          turn: 4,
        }),
      });

      const status = await getTurnStatus("game-1", "alice");
      expect(status.turn).toBe(4);
    });
  });

  describe("error handling", () => {
    it("throws ApiError with error details from response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          error: {
            code: "GAME_NOT_FOUND",
            message: "Game 'xyz' not found",
          },
        }),
      });

      await expect(listGames()).rejects.toThrow(ApiError);
      // First call already verified the throw above
    });

    it("throws ApiError with HTTP status when body is not JSON", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("not json");
        },
      });

      await expect(listGames()).rejects.toThrow(ApiError);
    });
  });

  describe("request formatting", () => {
    it("sends X-Player header when player is provided", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          games: [],
        }),
      });

      await listGames("alice");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/games"),
        expect.objectContaining({
          headers: expect.objectContaining({
            "X-Player": "alice",
          }),
        }),
      );
    });

    it("converts command bodies to snake_case and truncates waypoint coordinates", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "submitted",
          turn: 0,
          command_count: 1,
        }),
      });

      await submitCommands("game-1", "alice", 0, [
        {
          type: "set_waypoints",
          fleetId: "FL000001",
          waypoints: [{ x: 100.9, y: 200.1 }],
        },
      ]);

      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.commands[0].fleet_id).toBe("FL000001");
      expect(body.commands[0].waypoints[0]).toEqual({ x: 100, y: 200 });
    });
  });
});
