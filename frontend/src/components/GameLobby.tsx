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
import { Button } from "./Button";
import { FormField, SelectInput, TextInput } from "./FormField";
import { MutedText } from "./MutedText";
import { PanelCard } from "./PanelCard";

interface GameLobbyProps {
  onJoinGame: (gameId: string, player: string) => void;
}

export function GameLobby({ onJoinGame }: GameLobbyProps) {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

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
      setLoadError(null);
      const result = await listGames();
      setGames(result);
    } catch (err) {
      setLoadError(
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
      setCreateError(null);
      await createGame(newName.trim(), newSize, players);
      setShowCreate(false);
      setNewName("");
      setNewPlayers("player1, player2");
      await loadGames();
    } catch (err) {
      setCreateError(
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

        {loadError && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <p>{loadError}</p>
            <Button
              onClick={loadGames}
              disabled={loading}
              variant="secondary"
              size="xs"
              className="mt-2 border-red-400/50 text-red-200 hover:bg-red-500/15 hover:text-red-100"
            >
              {loading ? "Retrying…" : "Retry"}
            </Button>
          </div>
        )}

        {/* Player selection modal */}
        {selectedGame && (
          <PanelCard className="space-y-3 p-4">
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
            <Button
              onClick={() => setSelectedGame(null)}
              variant="ghost"
              size="xs"
              className="px-0"
            >
              ← Back
            </Button>
          </PanelCard>
        )}

        {/* Game list */}
        {!selectedGame && (
          <>
            {loading ? (
              <MutedText as="p" className="text-center text-sm">
                Loading games…
              </MutedText>
            ) : games.length === 0 ? (
              <MutedText as="p" className="text-center text-sm">
                No games yet. Create one to get started.
              </MutedText>
            ) : (
              <div className="space-y-2">
                {games.map((game) => (
                  <PanelCard
                    as="button"
                    key={game.gameId}
                    onClick={() => setSelectedGame(game)}
                    className="w-full p-3 text-left"
                    interactive
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{game.name}</span>
                      <MutedText className="text-xs">Turn {game.turn}</MutedText>
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
                  </PanelCard>
                ))}
              </div>
            )}

            {/* Create game */}
            {showCreate ? (
              <PanelCard className="space-y-3 p-4">
                <h3 className="font-semibold">New Game</h3>
                {createError && (
                  <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                    {createError}
                  </div>
                )}
                <FormField label="Game Name">
                  <TextInput
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="My Game"
                  />
                </FormField>
                <FormField label="Galaxy Size">
                  <SelectInput
                    value={newSize}
                    onChange={(e) => setNewSize(e.target.value as GalaxySize)}
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                    <option value="huge">Huge</option>
                  </SelectInput>
                </FormField>
                <FormField label="Players (comma-separated usernames)">
                  <TextInput
                    type="text"
                    value={newPlayers}
                    onChange={(e) => setNewPlayers(e.target.value)}
                    placeholder="alice, bob"
                  />
                </FormField>
                <div className="flex gap-2">
                  <Button
                    onClick={handleCreate}
                    disabled={creating}
                    variant="primary"
                  >
                    {creating ? "Creating…" : "Create"}
                  </Button>
                  <Button
                    onClick={() => setShowCreate(false)}
                    variant="secondary"
                  >
                    Cancel
                  </Button>
                </div>
              </PanelCard>
            ) : (
              <Button
                onClick={() => setShowCreate(true)}
                variant="dashed"
                fullWidth
                className="py-2"
              >
                + New Game
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
