import { PanelRightClose, PanelRightOpen } from "lucide-react";
import type {
  Design,
  DesignSummary,
  GalaxyPlanet,
  PlayerFleet,
  PlayerPlanet,
} from "../../types";
import { FleetDetail } from "./FleetDetail";
import type { WaypointEditorState } from "./FleetDetail";
import { PlanetDetail } from "./PlanetDetail";
import { DetailPanelContent, DetailPanelHeading } from "../ui/DetailPanelLayout";
import { MutedText } from "../ui/MutedText";

interface DetailPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  selectedPlanet: PlayerPlanet | null;
  selectedFleet: PlayerFleet | null;
  currentPlayer: string;
  designs: Design[];
  selectedTurn: number;
  knownPlanets: Array<GalaxyPlanet | PlayerPlanet>;
  onWaypointEditorStateChange: (state: WaypointEditorState) => void;
  ownFleets: PlayerFleet[];
  fleetsAtSelectedPlanet: PlayerFleet[];
  onSelectFleet: (fleetId: string) => void;
  shipDesigns: DesignSummary[];
  onOpenProduction?: (planetId: string) => void;
}

export function DetailPanel({
  collapsed,
  onToggle,
  selectedPlanet,
  selectedFleet,
  currentPlayer,
  designs,
  selectedTurn,
  knownPlanets,
  onWaypointEditorStateChange,
  ownFleets,
  fleetsAtSelectedPlanet,
  onSelectFleet,
  shipDesigns,
  onOpenProduction,
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
                key={`${selectedFleet.id}:${selectedTurn}`}
                fleet={selectedFleet}
                currentPlayer={currentPlayer}
                designs={designs}
                knownPlanets={knownPlanets}
                onWaypointEditorStateChange={onWaypointEditorStateChange}
                ownFleets={ownFleets}
              />
            ) : selectedPlanet ? (
              <PlanetDetail
                key={`${selectedPlanet.id}:${selectedTurn}`}
                planet={selectedPlanet}
                currentPlayer={currentPlayer}
                fleetsInOrbit={fleetsAtSelectedPlanet}
                onSelectFleet={onSelectFleet}
                shipDesigns={shipDesigns}
                onOpenProduction={onOpenProduction}
              />
            ) : (
              <DetailPanelContent>
                <DetailPanelHeading className="text-sm text-muted-foreground">
                  Nothing selected
                </DetailPanelHeading>
                <MutedText as="p" className="mt-2 text-xs">
                  Click a planet or fleet on the map to see details.
                </MutedText>
              </DetailPanelContent>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
