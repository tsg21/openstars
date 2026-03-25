import { PanelRightClose, PanelRightOpen } from "lucide-react";
import type { PlayerPlanet, PlayerFleet, Design, Position } from "../types";
import { PARSEC } from "../types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Distance between two galaxy positions in parsecs. */
function distanceParsecs(a: Position, b: Position): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy) / PARSEC;
}

/** Estimated turns to travel a distance at a given speed (parsecs/turn). */
function estimatedTurns(distPc: number, speed: number): number {
  if (speed <= 0) return Infinity;
  return Math.ceil(distPc / speed);
}

// ---------------------------------------------------------------------------
// Planet Detail
// ---------------------------------------------------------------------------

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
      <h2 className="text-base font-semibold text-foreground">
        {planet.name}
      </h2>

      <div className="mt-3 space-y-2 text-sm">
        {isOwn && (
          <div className="text-blue-400">
            <span className="text-muted-foreground">Owner:</span> You
          </div>
        )}
        {isEnemy && (
          <div className="text-red-400">
            <span className="text-muted-foreground">Owner:</span>{" "}
            {planet.owner}
          </div>
        )}
        {isUncolonised && <div className="text-zinc-500">Uncolonised</div>}

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

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">
        ID: {planet.id}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Fleet Detail
// ---------------------------------------------------------------------------

function FleetDetail({
  fleet,
  currentPlayer,
  designs,
}: {
  fleet: PlayerFleet;
  currentPlayer: string;
  designs: Design[];
}) {
  const isOwn = fleet.owner === currentPlayer;

  // Resolve design names and find effective speed
  const composition = (fleet.composition ?? []).map((c) => {
    const design = designs.find((d) => d.id === c.designId);
    return {
      name: design?.name ?? c.designId,
      count: c.count,
      speed: design?.speed ?? 0,
    };
  });

  const effectiveSpeed =
    composition.length > 0
      ? Math.min(...composition.map((c) => c.speed))
      : 0;

  // Calculate waypoint distances and estimated turns
  const waypoints = fleet.waypoints ?? [];
  const waypointInfo: { pos: Position; distPc: number; turns: number }[] = [];
  let prevPos = fleet.position;
  for (const wp of waypoints) {
    const distPc = distanceParsecs(prevPos, wp);
    waypointInfo.push({
      pos: wp,
      distPc,
      turns: estimatedTurns(distPc, effectiveSpeed),
    });
    prevPos = wp;
  }

  return (
    <div className="flex h-full flex-col p-4">
      <h2 className="text-base font-semibold text-foreground">
        Fleet{" "}
        <span className="font-mono text-sm text-muted-foreground">
          {fleet.id}
        </span>
      </h2>

      <div className="mt-3 space-y-3 text-sm">
        {/* Owner */}
        <div className={isOwn ? "text-blue-400" : "text-red-400"}>
          <span className="text-muted-foreground">Owner:</span>{" "}
          {isOwn ? "You" : fleet.owner}
        </div>

        {/* Composition (own fleets only) */}
        {isOwn && composition.length > 0 && (
          <div>
            <span className="text-muted-foreground">Ships:</span>
            <ul className="mt-1 space-y-0.5 pl-3">
              {composition.map((c, i) => (
                <li key={i} className="text-foreground">
                  {c.name} × {c.count}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Speed */}
        {isOwn && effectiveSpeed > 0 && (
          <div>
            <span className="text-muted-foreground">Speed:</span>{" "}
            <span className="text-foreground">{effectiveSpeed} pc/turn</span>
          </div>
        )}

        {/* Waypoints (own fleets only) */}
        {isOwn && waypointInfo.length > 0 && (
          <div>
            <span className="text-muted-foreground">Waypoints:</span>
            <ol className="mt-1 space-y-1 pl-3">
              {waypointInfo.map((wp, i) => (
                <li
                  key={i}
                  className="flex items-baseline justify-between text-foreground"
                >
                  <span className="font-mono text-xs">
                    ① ({Math.round(wp.pos.x / PARSEC)},{" "}
                    {Math.round(wp.pos.y / PARSEC)})
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ~{wp.turns} turn{wp.turns !== 1 ? "s" : ""}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {isOwn && waypointInfo.length === 0 && (
          <div className="text-muted-foreground italic">Stationary</div>
        )}
      </div>

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">
        ID: {fleet.id}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Detail Panel
// ---------------------------------------------------------------------------

interface DetailPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  selectedPlanet: PlayerPlanet | null;
  selectedFleet: PlayerFleet | null;
  currentPlayer: string;
  designs: Design[];
}

export function DetailPanel({
  collapsed,
  onToggle,
  selectedPlanet,
  selectedFleet,
  currentPlayer,
  designs,
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
            {selectedFleet ? (
              <FleetDetail
                fleet={selectedFleet}
                currentPlayer={currentPlayer}
                designs={designs}
              />
            ) : selectedPlanet ? (
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
