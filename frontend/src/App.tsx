import { useState } from "react";
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
          <GalaxyMap />
          <DetailPanel
            collapsed={detailCollapsed}
            onToggle={() => setDetailCollapsed((c) => !c)}
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
