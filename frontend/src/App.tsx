import { useState, useCallback } from "react";
import { useMockGameState } from "./hooks";
import {
  TopBar,
  DetailPanel,
  EventLog,
  GalaxyMap,
  DesktopGate,
} from "./components";

function App() {
  const gameState = useMockGameState();
  const [detailCollapsed, setDetailCollapsed] = useState(false);
  const [eventLogCollapsed, setEventLogCollapsed] = useState(true);
  const [selectedPlanetId, setSelectedPlanetId] = useState<string | null>(null);

  const handleSelectPlanet = useCallback((id: string | null) => {
    setSelectedPlanetId(id);
    // Auto-open detail panel when selecting something
    if (id !== null) {
      setDetailCollapsed(false);
    }
  }, []);

  // Find the selected planet data from the player state
  const selectedPlanet = selectedPlanetId
    ? gameState.playerState.planets.find((p) => p.id === selectedPlanetId) ?? null
    : null;

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
            selectedPlanetId={selectedPlanetId}
            onSelectPlanet={handleSelectPlanet}
          />
          <DetailPanel
            collapsed={detailCollapsed}
            onToggle={() => setDetailCollapsed((c) => !c)}
            selectedPlanet={selectedPlanet}
            currentPlayer={gameState.playerState.player}
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
