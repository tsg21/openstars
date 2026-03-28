/**
 * Game lobby — game list + game creation + player selection.
 *
 * This is the entry screen before the galaxy map. Simple and functional
 * for Phase 1 dev use. Will be polished in later phases.
 */

import { useState, useEffect, useCallback } from "react";
import {
  listGames,
  createGame,
  ApiError,
} from "../api/client";
import type { GameSummary } from "../api/client";
import type { GalaxySize } from "../types";

interface GameLobbyProps {
  onJoinGame: (gameId: string, player: string) => void;
}

export function GameLobby({ onJoinGame }: GameLobbyProps) {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create game form
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSize, setNewSize] = useState<GalaxySize>("small");
  const [newPlayers, setNewPlayers] = useState("player1, player2");
  const [creating, setCreating] = useState(false);

  // Player selection for joining
  const [selectedGame, setSelectedGame] = useState<GameSummary | null>(null);

  const loadGames = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await listGames();
      setGames(result);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to load games",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGames();
  }, [loadGames]);

  const handleCreate = async () => {
    const players = newPlayers
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);
    if (!newName.trim() || players.length < 2) return;

    try {
      setCreating(true);
      setError(null);
      await createGame(newName.trim(), newSize, players);
      setShowCreate(false);
      setNewName("");
      setNewPlayers("player1, player2");
      await loadGames();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to create game",
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-background text-foreground">
      <div className="w-full max-w-lg space-y-6 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-wide">OpenStars!</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Select a game or create a new one
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Player selection modal */}
        {selectedGame && (
          <div className="rounded-lg border border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] p-4 space-y-3">
            <h3 className="font-semibold">
              Join "{selectedGame.name}" as:
            </h3>
            <div className="space-y-2">
              {selectedGame.players.map((p) => (
                <button
                  key={p}
                  onClick={() => onJoinGame(selectedGame.gameId, p)}
                  className="w-full rounded-md border border-[var(--color-panel-border)] px-3 py-2 text-left text-sm hover:border-[var(--color-player-self)] hover:bg-[var(--color-player-self)]/10 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
            <button
              onClick={() => setSelectedGame(null)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              ← Back
            </button>
          </div>
        )}

        {/* Game list */}
        {!selectedGame && (
          <>
            {loading ? (
              <p className="text-center text-sm text-muted-foreground">
                Loading games…
              </p>
            ) : games.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground">
                No games yet. Create one to get started.
              </p>
            ) : (
              <div className="space-y-2">
                {games.map((game) => (
                  <button
                    key={game.gameId}
                    onClick={() => setSelectedGame(game)}
                    className="w-full rounded-lg border border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] p-3 text-left transition-colors hover:border-[var(--color-player-self)]/50"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{game.name}</span>
                      <span className="text-xs text-muted-foreground">
                        Turn {game.turn}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{game.galaxySize} galaxy</span>
                      <span>·</span>
                      <span>{game.players.length} players</span>
                      {game.allTurnsSubmitted && (
                        <>
                          <span>·</span>
                          <span className="text-green-400">
                            All submitted
                          </span>
                        </>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Create game */}
            {showCreate ? (
              <div className="rounded-lg border border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] p-4 space-y-3">
                <h3 className="font-semibold">New Game</h3>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Game Name
                  </label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="My Game"
                    className="w-full rounded-md border border-[var(--color-panel-border)] bg-background px-3 py-1.5 text-sm focus:border-[var(--color-player-self)] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Galaxy Size
                  </label>
                  <select
                    value={newSize}
                    onChange={(e) => setNewSize(e.target.value as GalaxySize)}
                    className="w-full rounded-md border border-[var(--color-panel-border)] bg-background px-3 py-1.5 text-sm focus:border-[var(--color-player-self)] focus:outline-none"
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                    <option value="huge">Huge</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Players (comma-separated usernames)
                  </label>
                  <input
                    type="text"
                    value={newPlayers}
                    onChange={(e) => setNewPlayers(e.target.value)}
                    placeholder="alice, bob"
                    className="w-full rounded-md border border-[var(--color-panel-border)] bg-background px-3 py-1.5 text-sm focus:border-[var(--color-player-self)] focus:outline-none"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleCreate}
                    disabled={creating}
                    className="rounded-md bg-[var(--color-player-self)] px-4 py-1.5 text-sm font-semibold text-white hover:bg-[var(--color-player-self)]/85 disabled:opacity-50"
                  >
                    {creating ? "Creating…" : "Create"}
                  </button>
                  <button
                    onClick={() => setShowCreate(false)}
                    className="rounded-md border border-[var(--color-panel-border)] px-4 py-1.5 text-sm text-muted-foreground hover:text-foreground"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowCreate(true)}
                className="w-full rounded-md border border-dashed border-[var(--color-panel-border)] px-3 py-2 text-sm text-muted-foreground hover:border-[var(--color-player-self)]/50 hover:text-foreground transition-colors"
              >
                + New Game
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
