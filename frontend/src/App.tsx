import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useGameState } from "./hooks/useGameState";
import {
  TopBar,
  DetailPanel,
  EventLog,
  GalaxyMap,
  DesktopGate,
  Button,
} from "./components";
import { GameLobby } from "./components/GameLobby";
import type { Selection, Position, Waypoint, WaypointTask } from "./types";
import { validateTransportOrders, validateTransferTask } from "./lib/waypointValidation";

function computeWaypointValidationErrors(
  waypoints: Waypoint[] | null,
): Record<string, string> {
  if (!waypoints) {
    return {};
  }

  const errors: Record<string, string> = {};
  waypoints.forEach((wp, i) => {
    if (!wp.task) return;
    let taskErrors: Record<string, string> = {};
    if (wp.task.type === "transport") {
      taskErrors = validateTransportOrders(wp.task.orders);
    } else if (wp.task.type === "transfer") {
      taskErrors = validateTransferTask(wp.task.fleetId ?? null, wp.task.orders);
    }
    for (const [key, msg] of Object.entries(taskErrors)) {
      errors[`waypoint-${i}-${key}`] = msg;
    }
  });

  return errors;
}

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
  const [waypointEditMode, setWaypointEditMode] = useState(false);
  const [editedWaypoints, setEditedWaypoints] = useState<Waypoint[] | null>(null);
  const [editRepeat, setEditRepeat] = useState(false);
  const [waypointValidationErrors, setWaypointValidationErrors] = useState<Record<string, string>>({});
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

  // Exit waypoint edit mode when the turn advances (draft would be stale)
  useEffect(() => {
    if (waypointEditMode) {
      setWaypointEditMode(false);
      setEditedWaypoints(null);
      setEditRepeat(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gameState.playerState?.turn]);

  const handleSelect = useCallback((sel: Selection) => {
    setSelection(sel);
    if (sel !== null) {
      setDetailCollapsed(false);
    }
    setWaypointEditMode(false);
    setEditedWaypoints(null);
    setEditRepeat(false);
    setWaypointValidationErrors({});
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

  // Waypoint editing handlers
  const handleEnterWaypointMode = useCallback(() => {
    if (selectedFleet && selectedFleet.owner === player) {
      setWaypointEditMode(true);
      setEditedWaypoints(selectedFleet.waypoints ?? []);
      setEditRepeat(selectedFleet.repeat ?? false);
    }
  }, [selectedFleet, player]);

  const handleExitWaypointMode = useCallback(() => {
    setWaypointEditMode(false);
    setEditedWaypoints(null);
    setEditRepeat(false);
    setWaypointValidationErrors({});
  }, []);

  const handleAddWaypoint = useCallback((pos: Position) => {
    setEditedWaypoints((prev) =>
      prev ? [...prev, { x: pos.x, y: pos.y, task: null }] : [{ x: pos.x, y: pos.y, task: null }]
    );
  }, []);

  const handleRemoveWaypoint = useCallback((index: number) => {
    setEditedWaypoints((prev) =>
      prev ? prev.filter((_, i) => i !== index) : null
    );
  }, []);

  const handleClearAllWaypoints = useCallback(() => {
    setEditedWaypoints([]);
  }, []);

  const handleToggleRepeat = useCallback(() => {
    setEditRepeat((r) => !r);
  }, []);

  const handleUpdateWaypointTask = useCallback(
    (index: number, task: WaypointTask | null) => {
      setEditedWaypoints((prev) =>
        prev ? prev.map((wp, i) => (i === index ? { ...wp, task } : wp)) : null,
      );
    },
    [],
  );

  useEffect(() => {
    if (!waypointEditMode) {
      return;
    }

    setWaypointValidationErrors(computeWaypointValidationErrors(editedWaypoints));
  }, [editedWaypoints, waypointEditMode]);

  const handleSaveWaypoints = useCallback(() => {
    if (selectedFleet && editedWaypoints !== null) {
      const errors = computeWaypointValidationErrors(editedWaypoints);
      if (Object.keys(errors).length > 0) {
        setWaypointValidationErrors(errors);
        return; // block submit
      }

      setWaypointValidationErrors({});

      const originalWaypoints = selectedFleet.waypoints ?? [];
      const hasChanged =
        editRepeat !== (selectedFleet.repeat ?? false) ||
        editedWaypoints.length !== originalWaypoints.length ||
        editedWaypoints.some(
          (wp, i) =>
            wp.x !== originalWaypoints[i]?.x ||
            wp.y !== originalWaypoints[i]?.y ||
            JSON.stringify(wp.task) !== JSON.stringify(originalWaypoints[i]?.task),
        );

      if (hasChanged) {
        gameState.setCommand({
          type: "set_waypoints",
          fleetId: selectedFleet.id,
          waypoints: editedWaypoints,
          repeat: editRepeat,
        });
      }
    }
    setWaypointEditMode(false);
    setEditedWaypoints(null);
    setEditRepeat(false);
    setWaypointValidationErrors({});
  }, [selectedFleet, editedWaypoints, editRepeat, gameState]);

  const handleViewportReady = useCallback((panTo: (x: number, y: number) => void) => {
    mapPanToRef.current = panTo;
  }, []);

  const handleEventClick = useCallback((x: number, y: number) => {
    mapPanToRef.current?.(x, y);
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
  const submissionText = gameState.gameDetail
    ? (() => {
        const total = gameState.gameDetail.players.length;
        const submitted = gameState.gameDetail.players.filter(
          (p) => p.submitted,
        ).length;
        if (submitted === total) return "All submitted";
        return `Waiting: ${submitted} of ${total} submitted`;
      })()
    : "";

  const allSubmitted =
    gameState.gameDetail?.players.every((p) => p.submitted) ?? false;
  const waitingForNextTurn = gameState.submitted && !allSubmitted;

  return (
    <DesktopGate>
      <div className="flex h-screen flex-col bg-background text-foreground selection:bg-[var(--color-player-self)]/30">
        {/* Top Bar */}
        <TopBar
          gameName={gameState.gameDetail?.name ?? "OpenStars!"}
          turn={gameState.playerState.turn}
          isDirty={gameState.isDirty}
          submitted={gameState.submitted}
          waitingForNextTurn={waitingForNextTurn}
          onSubmit={gameState.submit}
          submissionStatus={
            waitingForNextTurn ? "Waiting for the next turn" : submissionText
          }
          allSubmitted={allSubmitted}
          onResolve={gameState.resolve}
          onLeave={handleLeaveGame}
          playerName={player}
          error={gameState.error}
        />

        {/* Main area: map + detail panel */}
        <div
          className="flex flex-1 overflow-hidden transition-colors duration-300"
          onKeyDown={(e) => {
            if (
              e.key === "w" &&
              !waypointEditMode &&
              selectedFleet &&
              selectedFleet.owner === player
            ) {
              e.preventDefault();
              handleEnterWaypointMode();
            }
            if (e.key === "Escape" && waypointEditMode) {
              e.preventDefault();
              handleExitWaypointMode();
            }
          }}
        >
          <GalaxyMap
            galaxy={gameState.galaxy}
            playerState={gameState.workingPlayerState}
            selection={selection}
            onSelect={handleSelect}
            editingFleetId={
              waypointEditMode && selectedFleet ? selectedFleet.id : null
            }
            editedWaypoints={waypointEditMode ? editedWaypoints : null}
            onMapClick={waypointEditMode ? handleAddWaypoint : undefined}
            onRemoveWaypoint={waypointEditMode ? handleRemoveWaypoint : undefined}
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
            knownPlanets={gameState.galaxy.planets}
            waypointEditMode={waypointEditMode}
            editedWaypoints={editedWaypoints}
            editRepeat={editRepeat}
            onEnterWaypointMode={handleEnterWaypointMode}
            onExitWaypointMode={handleSaveWaypoints}
            onNewCommand={gameState.setCommand}
            onRemoveWaypoint={handleRemoveWaypoint}
            onClearAllWaypoints={handleClearAllWaypoints}
            onToggleRepeat={handleToggleRepeat}
            onUpdateWaypointTask={handleUpdateWaypointTask}
            waypointValidationErrors={waypointValidationErrors}
            ownFleets={gameState.workingPlayerState.fleets.filter(
              (f) => f.owner === player,
            )}
            onSetPlanetProductionQueue={gameState.setPlanetProductionQueue}
            fleetsAtSelectedPlanet={fleetsAtSelectedPlanet}
            onSelectFleet={handleSelectFleet}
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
      </div>
    </DesktopGate>
  );
}

export default App;
