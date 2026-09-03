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
} from "../../api/client";
import type { GameSummary } from "../../api/client";
import type { GalaxySize } from "../../types";
import { Button } from "../ui/Button";
import { ErrorBox } from "../ui/ErrorBox";
import { FormField, SelectInput, TextInput } from "../ui/FormField";
import { MutedText } from "../ui/MutedText";
import { PanelCard } from "../ui/PanelCard";

const LOBBY_COVER_ART_URL =
  "https://storage.googleapis.com/openstars-assets/stars.jpg";

interface GameLobbyProps {
  onJoinGame: (gameId: string, playerOverride: string | null) => void;
  /** The signed-in identity — the player for every game that does not allow overrides. */
  signedInAs: string;
  displayName?: string | null;
  onSignOut: () => void;
  /** Re-runs the session call so a newly created game lands in the `games` claim. */
  onSessionChanged: () => void;
}

export function GameLobby({
  onJoinGame,
  signedInAs,
  displayName,
  onSignOut,
  onSessionChanged,
}: GameLobbyProps) {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  // Create game form
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSize, setNewSize] = useState<GalaxySize>("small");
  const [newPlayers, setNewPlayers] = useState(signedInAs);
  const [newAllowOverride, setNewAllowOverride] = useState(false);
  const [creating, setCreating] = useState(false);

  // Player selection for joining
  const [selectedGame, setSelectedGame] = useState<GameSummary | null>(null);
  const [mismatchedGame, setMismatchedGame] = useState<GameSummary | null>(null);

  const handleSelectGame = useCallback(
    (game: GameSummary) => {
      if (game.allowPlayerOverride) {
        setSelectedGame(game);
        return;
      }
      if (!game.players.includes(signedInAs)) {
        setMismatchedGame(game);
        return;
      }
      // Strict game and we are a participant: no override, no picker.
      onJoinGame(game.gameId, null);
    },
    [onJoinGame, signedInAs],
  );

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
    queueMicrotask(() => {
      loadGames();
    });
  }, [loadGames]);

  const handleCreate = async () => {
    const players = newPlayers
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);
    if (!newName.trim() || players.length < 1) return;

    try {
      setCreating(true);
      setCreateError(null);
      await createGame(newName.trim(), newSize, players, newAllowOverride);
      setShowCreate(false);
      setNewName("");
      setNewPlayers(signedInAs);
      setNewAllowOverride(false);
      // The new game must reach the `games` claim before its listener can attach.
      onSessionChanged();
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
    <div className="relative flex h-screen items-center justify-center overflow-hidden bg-background text-foreground">
      <div className="absolute left-1/2 top-1/2 h-[700px] w-[850px] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl border border-white/10 shadow-2xl">
        <img
          src={LOBBY_COVER_ART_URL}
          alt="Stars! cover art"
          className="absolute inset-0 h-full w-full object-cover object-center opacity-40"
        />
        <div className="absolute inset-0 bg-background/60" />
      </div>

      <div className="relative z-10 w-full max-w-lg space-y-6 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-wide">OpenStars!</h1>
          <MutedText as="p" className="mt-1">
            Select a game or create a new one
          </MutedText>
          <div className="mt-2 flex items-center justify-center gap-2">
            <MutedText className="text-xs">
              Signed in as {displayName ? `${displayName} (${signedInAs})` : signedInAs}
            </MutedText>
            <Button onClick={onSignOut} variant="ghost" size="xs" className="px-1">
              Sign out
            </Button>
          </div>
        </div>

        {loadError && (
          <ErrorBox className="px-4 py-3 text-sm">
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
          </ErrorBox>
        )}

        {/* Override picker — only for games that permit playing as someone else */}
        {selectedGame && (
          <PanelCard className="space-y-3 p-4">
            <h3 className="font-semibold">Join "{selectedGame.name}" as:</h3>
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

        {/* A game that does not contain the signed-in user, and does not allow
            overrides, cannot be joined at all — say so rather than silently
            joining as somebody else. */}
        {mismatchedGame && (
          <PanelCard className="space-y-3 p-4">
            <h3 className="font-semibold">Cannot join "{mismatchedGame.name}"</h3>
            <MutedText as="p" className="text-sm">
              {signedInAs} is not a player in this game.
            </MutedText>
            <Button
              onClick={() => setMismatchedGame(null)}
              variant="ghost"
              size="xs"
              className="px-0"
            >
              ← Back
            </Button>
          </PanelCard>
        )}

        {/* Game list */}
        {!selectedGame && !mismatchedGame && (
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
                    onClick={() => handleSelectGame(game)}
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
                {createError && <ErrorBox>{createError}</ErrorBox>}
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
                <FormField label="Players (comma-separated emails)">
                  <TextInput
                    type="text"
                    value={newPlayers}
                    onChange={(e) => setNewPlayers(e.target.value)}
                    placeholder="alice@example.com"
                  />
                </FormField>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={newAllowOverride}
                    onChange={(e) => setNewAllowOverride(e.target.checked)}
                  />
                  Allow play-as-any-player (testing)
                </label>
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
