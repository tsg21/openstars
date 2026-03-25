import { useState, useCallback, useMemo } from "react";
import { useMockGameState } from "./hooks";
import {
  TopBar,
  DetailPanel,
  EventLog,
  GalaxyMap,
  DesktopGate,
} from "./components";
import type { Selection } from "./types";

function App() {
  const gameState = useMockGameState();
  const [detailCollapsed, setDetailCollapsed] = useState(false);
  const [eventLogCollapsed, setEventLogCollapsed] = useState(true);
  const [selection, setSelection] = useState<Selection>(null);

  const handleSelect = useCallback((sel: Selection) => {
    setSelection(sel);
    // Auto-open detail panel when selecting something
    if (sel !== null) {
      setDetailCollapsed(false);
    }
  }, []);

  // Resolve selection to data objects
  const selectedPlanet = useMemo(() => {
    if (selection?.kind !== "planet") return null;
    return (
      gameState.playerState.planets.find((p) => p.id === selection.id) ??
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
  }, [selection, gameState.playerState.planets, gameState.galaxy.planets]);

  const selectedFleet = useMemo(() => {
    if (selection?.kind !== "fleet") return null;
    return (
      gameState.playerState.fleets.find((f) => f.id === selection.id) ?? null
    );
  }, [selection, gameState.playerState.fleets]);

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
        <div className="flex flex-1 overflow-hidden">
          <GalaxyMap
            galaxy={gameState.galaxy}
            playerState={gameState.playerState}
            selection={selection}
            onSelect={handleSelect}
          />
          <DetailPanel
            collapsed={detailCollapsed}
            onToggle={() => setDetailCollapsed((c) => !c)}
            selectedPlanet={selectedPlanet}
            selectedFleet={selectedFleet}
            currentPlayer={gameState.playerState.player}
            designs={gameState.playerState.designs}
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
