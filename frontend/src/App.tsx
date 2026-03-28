import { useState, useCallback, useMemo, useEffect } from "react";
import { useMockGameState } from "./hooks";
import {
  TopBar,
  DetailPanel,
  EventLog,
  GalaxyMap,
  DesktopGate,
} from "./components";
import type { Selection, Position } from "./types";

function App() {
  const gameState = useMockGameState();
  const [detailCollapsed, setDetailCollapsed] = useState(false);
  const [eventLogCollapsed, setEventLogCollapsed] = useState(true);
  const [selection, setSelection] = useState<Selection>(null);
  const [waypointEditMode, setWaypointEditMode] = useState(false);
  const [editedWaypoints, setEditedWaypoints] = useState<Position[] | null>(null);

  // Warn user before leaving page with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (gameState.isDirty) {
        e.preventDefault();
        // Modern browsers ignore custom messages and show their own
        return (e.returnValue = "");
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [gameState.isDirty]);

  const handleSelect = useCallback((sel: Selection) => {
    setSelection(sel);
    // Auto-open detail panel when selecting something
    if (sel !== null) {
      setDetailCollapsed(false);
    }
    // Exit waypoint edit mode when selection changes
    setWaypointEditMode(false);
    setEditedWaypoints(null);
  }, []);

  // Resolve selection to data objects
  const selectedPlanet = useMemo(() => {
    if (selection?.kind !== "planet") return null;
    return (
      gameState.workingPlayerState.planets.find((p) => p.id === selection.id) ??
      (() => {
        const gp = gameState.galaxy.planets.find(
          (p) => p.id === selection.id,
        );
        if (!gp) return null;
        return {
          id: gp.id,
          name: gp.name,
          x: gp.x,
          y: gp.y,
          owner: null,
        } as const;
      })()
    );
  }, [selection, gameState.workingPlayerState.planets, gameState.galaxy.planets]);

  const selectedFleet = useMemo(() => {
    if (selection?.kind !== "fleet") return null;
    return (
      gameState.workingPlayerState.fleets.find((f) => f.id === selection.id) ??
      null
    );
  }, [selection, gameState.workingPlayerState.fleets]);

  // Waypoint editing handlers
  const handleEnterWaypointMode = useCallback(() => {
    if (selectedFleet && selectedFleet.owner === gameState.playerState.player) {
      setWaypointEditMode(true);
      setEditedWaypoints(selectedFleet.waypoints ?? []);
    }
  }, [selectedFleet, gameState.playerState.player]);

  const handleExitWaypointMode = useCallback(() => {
    setWaypointEditMode(false);
    setEditedWaypoints(null);
  }, []);

  const handleAddWaypoint = useCallback((pos: Position) => {
    setEditedWaypoints((prev) => (prev ? [...prev, pos] : [pos]));
  }, []);

  const handleRemoveWaypoint = useCallback((index: number) => {
    setEditedWaypoints((prev) =>
      prev ? prev.filter((_, i) => i !== index) : null
    );
  }, []);

  const handleClearAllWaypoints = useCallback(() => {
    setEditedWaypoints([]);
  }, []);

  const handleSaveWaypoints = useCallback(() => {
    if (selectedFleet && editedWaypoints !== null) {
      // Only save if waypoints have actually changed
      const originalWaypoints = selectedFleet.waypoints ?? [];
      const hasChanged =
        editedWaypoints.length !== originalWaypoints.length ||
        editedWaypoints.some(
          (wp, i) =>
            wp.x !== originalWaypoints[i]?.x ||
            wp.y !== originalWaypoints[i]?.y
        );

      if (hasChanged) {
        gameState.setCommand({
          type: "set_waypoints",
          fleetId: selectedFleet.id,
          waypoints: editedWaypoints,
        });
      }
    }
    setWaypointEditMode(false);
    setEditedWaypoints(null);
  }, [selectedFleet, editedWaypoints, gameState]);

  return (
    <DesktopGate>
      <div className="flex h-screen flex-col bg-background text-foreground">
        {/* Top Bar */}
        <TopBar
          gameName="OpenStars!"
          turn={gameState.playerState.turn}
          isDirty={gameState.isDirty}
          onSubmit={gameState.submit}
        />

        {/* Main area: map + detail panel */}
        <div
          className="flex flex-1 overflow-hidden"
          onKeyDown={(e) => {
            // "w" key to enter waypoint edit mode
            if (
              e.key === "w" &&
              !waypointEditMode &&
              selectedFleet &&
              selectedFleet.owner === gameState.playerState.player
            ) {
              e.preventDefault();
              handleEnterWaypointMode();
            }
            // Escape to exit waypoint edit mode
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
          />
          <DetailPanel
            collapsed={detailCollapsed}
            onToggle={() => setDetailCollapsed((c) => !c)}
            selectedPlanet={selectedPlanet}
            selectedFleet={selectedFleet}
            currentPlayer={gameState.playerState.player}
            designs={gameState.playerState.designs}
            waypointEditMode={waypointEditMode}
            editedWaypoints={editedWaypoints}
            onEnterWaypointMode={handleEnterWaypointMode}
            onExitWaypointMode={handleSaveWaypoints}
            onRemoveWaypoint={handleRemoveWaypoint}
            onClearAllWaypoints={handleClearAllWaypoints}
          />
        </div>

        {/* Event Log */}
        <EventLog
          collapsed={eventLogCollapsed}
          onToggle={() => setEventLogCollapsed((c) => !c)}
        />
      </div>
    </DesktopGate>
  );
}

export default App;
