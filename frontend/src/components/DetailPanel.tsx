import { PanelRightClose, PanelRightOpen } from "lucide-react";
import type { PlayerPlanet } from "../types";

interface DetailPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  selectedPlanet: PlayerPlanet | null;
  currentPlayer: string;
}

function PlanetDetail({
  planet,
  currentPlayer,
}: {
  planet: PlayerPlanet;
  currentPlayer: string;
}) {
  const isOwn = planet.owner === currentPlayer;
  const isEnemy = planet.owner !== null && !isOwn;
  const isUncolonised = planet.owner === null;

  return (
    <div className="flex h-full flex-col p-4">
      {/* Planet name */}
      <h2 className="text-base font-semibold text-foreground">{planet.name}</h2>

      <div className="mt-3 space-y-2 text-sm">
        {/* Ownership */}
        {isOwn && (
          <div className="text-blue-400">
            <span className="text-muted-foreground">Owner:</span> You
          </div>
        )}
        {isEnemy && (
          <div className="text-red-400">
            <span className="text-muted-foreground">Owner:</span> {planet.owner}
          </div>
        )}
        {isUncolonised && (
          <div className="text-zinc-500">Uncolonised</div>
        )}

        {/* Population — only for own planets, or enemy planets if data available */}
        {isOwn && planet.population !== undefined && (
          <div>
            <span className="text-muted-foreground">Population:</span>{" "}
            <span className="text-foreground">
              {planet.population.toLocaleString()}
            </span>
          </div>
        )}

        {isEnemy && planet.population !== undefined && (
          <div>
            <span className="text-muted-foreground">Population:</span>{" "}
            <span className="text-foreground">
              ~{planet.population.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {/* Placeholder for future info (minerals, factories, etc.) */}
      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">
        ID: {planet.id}
      </div>
    </div>
  );
}

export function DetailPanel({
  collapsed,
  onToggle,
  selectedPlanet,
  currentPlayer,
}: DetailPanelProps) {
  return (
    <div className="relative">
      {/* Toggle button — outside the aside so it's never clipped */}
      <button
        onClick={onToggle}
        className="absolute -left-7 top-2 z-10 rounded-l bg-[var(--color-panel-bg)] border border-r-0 border-[var(--color-panel-border)] p-1 text-muted-foreground hover:text-foreground"
        aria-label={collapsed ? "Open detail panel" : "Close detail panel"}
      >
        {collapsed ? (
          <PanelRightOpen className="h-4 w-4" />
        ) : (
          <PanelRightClose className="h-4 w-4" />
        )}
      </button>

      <aside
        className={`h-full border-l border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] transition-[width] duration-200 overflow-hidden ${
          collapsed ? "w-0 border-l-0" : "w-[350px]"
        }`}
      >
        {!collapsed && (
          <>
            {selectedPlanet ? (
              <PlanetDetail
                planet={selectedPlanet}
                currentPlayer={currentPlayer}
              />
            ) : (
              <div className="flex h-full flex-col p-4">
                <h2 className="text-sm font-semibold text-muted-foreground">
                  Nothing selected
                </h2>
                <p className="mt-2 text-xs text-muted-foreground">
                  Click a planet or fleet on the map to see details.
                </p>
              </div>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
