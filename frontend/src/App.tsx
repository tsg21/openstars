import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useGameState } from "./hooks/useGameState";
import {
  TopBar,
  DesignsWorkspace,
  ProductionWorkspace,
  RaceSelectionScreen,
  ResearchWorkspace,
  DetailPanel,
  EventLog,
  GalaxyMap,
  DesktopGate,
  Button,
  GameLobby,
  ErrorBox,
} from "./components";
import type { WaypointEditorState } from "./components";
import { GameCommandsContext } from "./contexts/gameCommandsContext";
import type { Selection } from "./types";
import type { SetResearchCommand } from "./types";

type AppMode = "command" | "production" | "designer" | "research";

const EMPTY_WAYPOINT_EDITOR_STATE: WaypointEditorState = {
  waypointEditMode: false,
  editingFleetId: null,
  editedWaypoints: null,
};

function App() {
  // --- Game/player selection ---
  // Check URL params for deep-linking: ?game=<id>&player=<name>
  const [gameId, setGameId] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("game");
  });
  const [player, setPlayer] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("player");
  });

  const handleJoinGame = useCallback((gid: string, p: string) => {
    setGameId(gid);
    setPlayer(p);
    // Update URL for deep-linking without reload
    const url = new URL(window.location.href);
    url.searchParams.set("game", gid);
    url.searchParams.set("player", p);
    window.history.pushState({}, "", url.toString());
  }, []);

  const handleLeaveGame = useCallback(() => {
    setGameId(null);
    setPlayer(null);
    const url = new URL(window.location.href);
    url.searchParams.delete("game");
    url.searchParams.delete("player");
    window.history.pushState({}, "", url.toString());
  }, []);

  // Handle browser back/forward
  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      setGameId(params.get("game"));
      setPlayer(params.get("player"));
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // --- Game state ---
  const gameState = useGameState(gameId, player);

  // --- UI state ---
  const [detailCollapsed, setDetailCollapsed] = useState(false);
  const [eventLogCollapsed, setEventLogCollapsed] = useState(true);
  const [selection, setSelection] = useState<Selection>(null);
  const [mode, setMode] = useState<AppMode>("command");
  const [waypointEditorState, setWaypointEditorState] = useState<WaypointEditorState>(
    EMPTY_WAYPOINT_EDITOR_STATE,
  );
  const lastTurnRef = useRef<number | null>(null);
  const tmpFleetCounterRef = useRef(0);
  const mapPanToRef = useRef<((x: number, y: number) => void) | null>(null);

  // Warn user before leaving page with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (gameState.isDirty) {
        e.preventDefault();
        return (e.returnValue = "");
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [gameState.isDirty]);


  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      const active = document.activeElement;
      if (active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement) return;

      const key = event.key.toLowerCase();
      if (key === "r") {
        event.preventDefault();
        if (gameState.playerState?.research) {
          setMode((prev) => (prev === "research" ? "command" : "research"));
        }
      } else if (key === "p") {
        event.preventDefault();
        setMode((prev) => (prev === "production" ? "command" : "production"));
      } else if (event.key === "Escape") {
        setMode((prev) => (prev === "production" ? "command" : prev));
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [gameState.playerState?.research]);

  const handleSelect = useCallback((sel: Selection) => {
    setSelection(sel);
    if (sel !== null) {
      setDetailCollapsed(false);
    }
  }, []);

  // Resolve selection to data objects
  const selectedPlanet = useMemo(() => {
    if (selection?.kind !== "planet" || !gameState.workingPlayerState) return null;
    return (
      gameState.workingPlayerState.planets.find((p) => p.id === selection.id) ??
      (() => {
        const gp = gameState.galaxy?.planets.find((p) => p.id === selection.id);
        if (!gp) return null;
        return {
          id: gp.id,
          name: gp.name,
          x: gp.x,
          y: gp.y,
          owner: null,
          scanLevel: "none" as const,
          scanAge: 0,
        };
      })()
    );
  }, [selection, gameState.workingPlayerState, gameState.galaxy]);

  const selectedFleet = useMemo(() => {
    if (selection?.kind !== "fleet" || !gameState.workingPlayerState) return null;
    return (
      gameState.workingPlayerState.fleets.find((f) => f.id === selection.id) ??
      null
    );
  }, [selection, gameState.workingPlayerState]);

  const fleetsAtSelectedPlanet = useMemo(() => {
    if (!selectedPlanet || !gameState.workingPlayerState) return [];
    return gameState.workingPlayerState.fleets.filter(
      (f) => f.position.x === selectedPlanet.x && f.position.y === selectedPlanet.y,
    );
  }, [selectedPlanet, gameState.workingPlayerState]);

  const handleSelectFleet = useCallback((fleetId: string) => {
    handleSelect({ kind: "fleet", id: fleetId });
  }, [handleSelect]);

  const handleModeChange = useCallback((nextMode: AppMode) => {
    setMode(nextMode);
  }, []);

  const handleWaypointEditorStateChange = useCallback((state: WaypointEditorState) => {
    setWaypointEditorState(state);
  }, []);

  const handleViewportReady = useCallback((panTo: (x: number, y: number) => void) => {
    mapPanToRef.current = panTo;
  }, []);

  const handleEventClick = useCallback((x: number, y: number) => {
    mapPanToRef.current?.(x, y);
  }, []);

  useEffect(() => {
    const turn = gameState.playerState?.turn;
    if (turn == null) {
      return;
    }
    if (lastTurnRef.current == null || lastTurnRef.current !== turn) {
      lastTurnRef.current = turn;
      tmpFleetCounterRef.current = 0;
    }
  }, [gameState.playerState?.turn]);

  const nextTmpFleetId = useCallback(() => {
    tmpFleetCounterRef.current += 1;
    return `tmp_${tmpFleetCounterRef.current}`;
  }, []);

  // --- Show lobby if no game selected ---
  if (!gameId || !player) {
    return (
      <DesktopGate>
        <GameLobby onJoinGame={handleJoinGame} />
      </DesktopGate>
    );
  }

  // --- Loading state ---
  if (gameState.loading && !gameState.galaxy) {
    return (
      <DesktopGate>
        <div className="flex h-screen items-center justify-center bg-background text-foreground">
          <div className="text-center space-y-2">
            <p className="text-lg font-semibold">Loading game…</p>
            <p className="text-sm text-muted-foreground">
              Fetching galaxy and player state
            </p>
          </div>
        </div>
      </DesktopGate>
    );
  }

  // --- Error state ---
  if (gameState.error && !gameState.galaxy) {
    return (
      <DesktopGate>
        <div className="flex h-screen items-center justify-center bg-background text-foreground">
          <div className="text-center space-y-4">
            <p className="text-lg font-semibold text-red-400">
              Failed to load game
            </p>
            <p className="text-sm text-muted-foreground">
              {gameState.error}
            </p>
            <div className="flex gap-2 justify-center">
              <Button
                onClick={() => gameState.refresh()}
                variant="primary"
              >
                Retry
              </Button>
              <Button
                onClick={handleLeaveGame}
                variant="secondary"
              >
                Back to lobby
              </Button>
            </div>
          </div>
        </div>
      </DesktopGate>
    );
  }

  // If we still don't have galaxy or player state, show loading
  if (!gameState.galaxy || !gameState.playerState || !gameState.workingPlayerState) {
    return (
      <DesktopGate>
        <div className="flex h-screen items-center justify-center bg-background text-foreground">
          <p className="text-muted-foreground">Loading…</p>
        </div>
      </DesktopGate>
    );
  }

  // Compute submission status text
  const playersAwaitingSubmission =
    gameState.turnStatus?.playersAwaitingSubmission ??
    gameState.gameDetail?.players.filter((p) => !p.submitted).map((p) => p.username) ??
    [];
  const isTurnZeroRacePhase = gameState.playerState.turn === 0 && gameState.playerState.race == null;
  const submissionText = gameState.gameDetail
    ? (() => {
        const total = gameState.gameDetail.players.length;
        const submitted = total - playersAwaitingSubmission.length;
        return `Waiting: ${submitted} of ${total} submitted`;
      })()
    : "";

  const waitingForNextTurn = gameState.submitted && playersAwaitingSubmission.length > 0;
  const pendingResearchCommand = gameState.commands.commands.find((command): command is SetResearchCommand => command.type === "set_research") ?? null;
  const ownedPlanets = gameState.workingPlayerState.planets.filter((planet) => planet.owner === player);
  const ownedPlanetsLeftoverOnlyCount = ownedPlanets.filter((planet) => planet.contributeOnlyLeftoverToResearch === true).length;
  // Use the base (committed) research state as the diff baseline. workingPlayerState.research
  // already has the pending set_research command applied, which would cause the workspace to
  // diff later edits against an already-edited baseline and silently drop earlier changes.
  const activeResearch = gameState.playerState.research;
  const effectiveMode: AppMode =
    (mode === "research" && !activeResearch) ||
    (mode === "production" && ownedPlanets.length === 0)
      ? "command"
      : mode;

  return (
    <DesktopGate>
      <GameCommandsContext.Provider
        value={{
          basePlayerState: gameState.playerState,
          addCommand: gameState.addCommand,
          replaceCommands: gameState.replaceCommands,
          nextTmpFleetId,
        }}
      >
        <div className="flex h-screen flex-col bg-background text-foreground selection:bg-[var(--color-player-self)]/30">
        {gameState.notificationsError && (
          <ErrorBox className="rounded-none border-x-0 border-t-0">
            Realtime updates disconnected.{" "}
            <button
              className="underline"
              onClick={() => gameState.refresh()}
            >
              Reload
            </button>
          </ErrorBox>
        )}
        {/* Top Bar */}
        <TopBar
          gameName={gameState.gameDetail?.name ?? "OpenStars!"}
          turn={gameState.playerState.turn}
          waitingForNextTurn={waitingForNextTurn}
          mode={effectiveMode}
          onModeChange={handleModeChange}
          raceSelectionActive={isTurnZeroRacePhase}
          onSubmit={gameState.submit}
          submissionStatus={
            waitingForNextTurn ? "Waiting for the next turn" : submissionText
          }
          onLeave={handleLeaveGame}
          playerName={player}
          error={gameState.error}
          research={activeResearch ?? null}
          productionEnabled={ownedPlanets.length > 0}
        />

        {isTurnZeroRacePhase ? (
          <RaceSelectionScreen
            gameId={gameId}
            player={player}
          />
        ) : effectiveMode === "production" ? (
          <ProductionWorkspace
            ownedPlanets={ownedPlanets}
            currentPlayer={player}
            shipDesigns={gameState.shipDesigns}
            initialPlanetId={selection?.kind === "planet" ? selection.id : null}
            onShowOnMap={(planetId) => {
              const planet = gameState.workingPlayerState!.planets.find((p) => p.id === planetId);
              setSelection({ kind: "planet", id: planetId });
              setMode("command");
              if (planet) mapPanToRef.current?.(planet.x, planet.y);
            }}
          />
        ) : effectiveMode === "designer" ? (
          <DesignsWorkspace gameId={gameId} player={player} />
        ) : effectiveMode === "research" && activeResearch ? (
          <ResearchWorkspace
            research={activeResearch}
            ownedPlanetsLeftoverOnlyCount={ownedPlanetsLeftoverOnlyCount}
            ownedPlanetsCount={ownedPlanets.length}
            pendingCommand={pendingResearchCommand}
            onChange={(cmd) => gameState.replaceCommands({ kind: "research" }, cmd ? [cmd] : [])}
          />
        ) : (
          <>
            {/* Main area: map + detail panel */}
            <div
              className="flex flex-1 overflow-hidden transition-colors duration-300"
              onKeyDown={(e) => {
                if (
                  e.key === "w" &&
                  !waypointEditorState.waypointEditMode &&
                  selectedFleet &&
                  selectedFleet.owner === player
                ) {
                  e.preventDefault();
                  waypointEditorState.onEnterWaypointMode?.();
                }
                if (e.key === "Escape" && waypointEditorState.waypointEditMode) {
                  e.preventDefault();
                  waypointEditorState.onExitWaypointMode?.();
                }
              }}
            >
              <GalaxyMap
                galaxy={gameState.galaxy}
                playerState={gameState.workingPlayerState}
                selection={selection}
                onSelect={handleSelect}
                editingFleetId={waypointEditorState.editingFleetId}
                editedWaypoints={waypointEditorState.editedWaypoints}
                onMapClick={waypointEditorState.onAddWaypoint}
                onRemoveWaypoint={waypointEditorState.onRemoveWaypoint}
                onViewportReady={handleViewportReady}
                showScanners
              />
              <DetailPanel
                collapsed={detailCollapsed}
                onToggle={() => setDetailCollapsed((c) => !c)}
                selectedPlanet={selectedPlanet}
                selectedFleet={selectedFleet}
                currentPlayer={player}
                designs={gameState.playerState.designs}
                selectedTurn={gameState.playerState.turn}
                knownPlanets={gameState.galaxy.planets}
                onWaypointEditorStateChange={handleWaypointEditorStateChange}
                ownFleets={gameState.workingPlayerState.fleets.filter(
                  (f) => f.owner === player,
                )}
                fleetsAtSelectedPlanet={fleetsAtSelectedPlanet}
                onSelectFleet={handleSelectFleet}
                shipDesigns={gameState.shipDesigns}
                onOpenProduction={(planetId) => {
                  setSelection({ kind: "planet", id: planetId });
                  setMode("production");
                }}
              />
            </div>

            {/* Event Log */}
            <EventLog
              collapsed={eventLogCollapsed}
              onToggle={() => setEventLogCollapsed((c) => !c)}
              events={gameState.playerState.events}
              galaxy={gameState.galaxy}
              onEventClick={handleEventClick}
            />
          </>
        )}
        </div>
      </GameCommandsContext.Provider>
    </DesktopGate>
  );
}

export default App;
