import { PanelRightClose, PanelRightOpen } from "lucide-react";
import type {
  Design,
  GalaxyPlanet,
  PlayerCommand,
  PlayerFleet,
  PlayerPlanet,
  PlayerProductionQueueItem,
  Waypoint,
  WaypointTask,
} from "../types";
import { FleetDetail } from "./FleetDetail";
import { PlanetDetail } from "./PlanetDetail";
import { DetailPanelContent, DetailPanelHeading } from "./DetailPanelLayout";

interface DetailPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  selectedPlanet: PlayerPlanet | null;
  selectedFleet: PlayerFleet | null;
  currentPlayer: string;
  designs: Design[];
  waypointEditMode: boolean;
  editedWaypoints: Waypoint[] | null;
  editRepeat: boolean;
  knownPlanets: Array<GalaxyPlanet | PlayerPlanet>;
  onEnterWaypointMode: () => void;
  onExitWaypointMode: () => void;
  onNewCommand: (command: PlayerCommand) => void;
  onRemoveWaypoint: (index: number) => void;
  onClearAllWaypoints: () => void;
  onToggleRepeat: () => void;
  onUpdateWaypointTask: (index: number, task: WaypointTask | null) => void;
  waypointValidationErrors: Record<string, string>;
  ownFleets: PlayerFleet[];
  onSetPlanetProductionQueue: (planetId: string, queue: PlayerProductionQueueItem[]) => void;
  fleetsAtSelectedPlanet: PlayerFleet[];
  onSelectFleet: (fleetId: string) => void;
}

export function DetailPanel({
  collapsed,
  onToggle,
  selectedPlanet,
  selectedFleet,
  currentPlayer,
  designs,
  waypointEditMode,
  editedWaypoints,
  editRepeat,
  knownPlanets,
  onEnterWaypointMode,
  onExitWaypointMode,
  onNewCommand,
  onRemoveWaypoint,
  onClearAllWaypoints,
  onToggleRepeat,
  onUpdateWaypointTask,
  waypointValidationErrors,
  ownFleets,
  onSetPlanetProductionQueue,
  fleetsAtSelectedPlanet,
  onSelectFleet,
}: DetailPanelProps) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="absolute -left-7 top-2 z-10 rounded-l border border-r-0 border-[var(--color-panel-border)] panel-surface p-1 text-muted-foreground transition-colors duration-200 hover:text-foreground"
        aria-label={collapsed ? "Open detail panel" : "Close detail panel"}
      >
        {collapsed ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
      </button>

      <aside
        className={`h-full border-l border-[var(--color-panel-border)] panel-surface transition-[width] duration-300 overflow-hidden ${
          collapsed ? "w-0 border-l-0" : "w-[350px]"
        }`}
      >
        {!collapsed && (
          <>
            {selectedFleet ? (
              <FleetDetail
                key={selectedFleet.id}
                fleet={selectedFleet}
                currentPlayer={currentPlayer}
                designs={designs}
                knownPlanets={knownPlanets}
                waypointEditMode={waypointEditMode}
                editedWaypoints={editedWaypoints}
                editRepeat={editRepeat}
                onEnterWaypointMode={onEnterWaypointMode}
                onExitWaypointMode={onExitWaypointMode}
                onNewCommand={onNewCommand}
                onRemoveWaypoint={onRemoveWaypoint}
                onClearAllWaypoints={onClearAllWaypoints}
                onToggleRepeat={onToggleRepeat}
                onUpdateWaypointTask={onUpdateWaypointTask}
                waypointValidationErrors={waypointValidationErrors}
                ownFleets={ownFleets}
              />
            ) : selectedPlanet ? (
              <PlanetDetail
                planet={selectedPlanet}
                currentPlayer={currentPlayer}
                fleetsInOrbit={fleetsAtSelectedPlanet}
                onSelectFleet={onSelectFleet}
                onSetProductionQueue={onSetPlanetProductionQueue}
              />
            ) : (
              <DetailPanelContent>
                <DetailPanelHeading className="text-sm text-muted-foreground">
                  Nothing selected
                </DetailPanelHeading>
                <p className="mt-2 text-xs text-muted-foreground">
                  Click a planet or fleet on the map to see details.
                </p>
              </DetailPanelContent>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
