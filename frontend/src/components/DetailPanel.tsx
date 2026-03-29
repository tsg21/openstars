import { useEffect, useMemo, useState } from "react";
import { PanelRightClose, PanelRightOpen, Trash2 } from "lucide-react";
import type { PlayerPlanet, PlayerFleet, Design, Position } from "../types";
import { PARSEC } from "../types";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../lib/planetImages";

const CIRCLED_NUMBERS = [
  "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
  "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳",
];

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

  const [manifest, setManifest] = useState<PlanetImageManifest | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchPlanetImageManifest()
      .then((result) => {
        if (!cancelled) setManifest(result);
      })
      .catch((error) => {
        console.warn("Unable to load planet image manifest", error);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const planetImageUrl = useMemo(() => {
    if (!manifest) return null;
    return getPlanetImageUrl(manifest, planet.id);
  }, [manifest, planet.id]);

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <h2 className="text-base font-semibold text-foreground">{planet.name}</h2>

      <div className="overflow-hidden rounded-md border border-[var(--color-panel-border)] bg-black/20">
        {planetImageUrl ? (
          <img
            src={planetImageUrl}
            alt={`${planet.name} render`}
            className="aspect-square w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="flex aspect-square w-full items-center justify-center text-xs text-muted-foreground">
            No planet image available
          </div>
        )}
      </div>

      <div className="elevated-surface rounded-md border border-[var(--color-panel-border)] p-3 space-y-2 text-sm">
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
        {isUncolonised && <div className="text-zinc-500">Uncolonised</div>}

        {isOwn && planet.population !== undefined && (
          <div>
            <span className="text-muted-foreground">Population:</span>{" "}
            <span className="text-foreground font-semibold">
              {planet.population.toLocaleString()}
            </span>
          </div>
        )}

        {isEnemy && planet.population !== undefined && (
          <div>
            <span className="text-muted-foreground">Population:</span>{" "}
            <span className="text-foreground">~{planet.population.toLocaleString()}</span>
          </div>
        )}
      </div>

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">ID: {planet.id}</div>
    </div>
  );
}

function FleetDetail({
  fleet,
  currentPlayer,
  designs,
  waypointEditMode,
  editedWaypoints,
  onEnterWaypointMode,
  onExitWaypointMode,
  onRemoveWaypoint,
  onClearAllWaypoints,
}: {
  fleet: PlayerFleet;
  currentPlayer: string;
  designs: Design[];
  waypointEditMode: boolean;
  editedWaypoints: Position[] | null;
  onEnterWaypointMode: () => void;
  onExitWaypointMode: () => void;
  onRemoveWaypoint: (index: number) => void;
  onClearAllWaypoints: () => void;
}) {
  const isOwn = fleet.owner === currentPlayer;

  const composition = (fleet.composition ?? []).map((c) => {
    const design = designs.find((d) => d.id === c.designId);
    return {
      name: design?.name ?? c.designId,
      count: c.count,
      speed: design?.speed ?? 0,
    };
  });

  const effectiveSpeed = composition.length > 0 ? Math.min(...composition.map((c) => c.speed)) : 0;

  const waypoints = waypointEditMode && editedWaypoints !== null ? editedWaypoints : fleet.waypoints ?? [];
  const waypointInfo: {
    pos: Position;
    distPc: number;
    legTurns: number;
    cumulativeTurns: number;
  }[] = [];
  let prevPos = fleet.position;
  let totalTurns = 0;

  for (const wp of waypoints) {
    const distPc = distanceParsecs(prevPos, wp);
    const legTurns = estimatedTurns(distPc, effectiveSpeed);
    totalTurns += legTurns;
    waypointInfo.push({
      pos: wp,
      distPc,
      legTurns,
      cumulativeTurns: totalTurns,
    });
    prevPos = wp;
  }

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <h2 className="text-base font-semibold text-foreground">
        Fleet <span className="font-mono text-sm text-muted-foreground">{fleet.id}</span>
      </h2>

      <div className="space-y-3 text-sm">
        <div className="elevated-surface rounded-md border border-[var(--color-panel-border)] p-3">
          <div className={isOwn ? "text-blue-400" : "text-red-400"}>
            <span className="text-muted-foreground">Owner:</span> {isOwn ? "You" : fleet.owner}
          </div>
        </div>

        {isOwn && composition.length > 0 && (
          <div className="elevated-surface rounded-md border border-[var(--color-panel-border)] p-3">
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

        {isOwn && effectiveSpeed > 0 && (
          <div className="elevated-surface rounded-md border border-[var(--color-panel-border)] p-3">
            <span className="text-muted-foreground">Speed:</span>{" "}
            <span className="text-foreground font-semibold">{effectiveSpeed} pc/turn</span>
          </div>
        )}

        {isOwn && waypointInfo.length > 0 && (
          <div className="elevated-surface rounded-md border border-[var(--color-panel-border)] p-3">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Waypoints:</span>
              {waypointEditMode && (
                <button
                  onClick={onClearAllWaypoints}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                >
                  Clear All
                </button>
              )}
            </div>
            <ol className="mt-1 space-y-1 pl-3">
              {waypointInfo.map((wp, i) => (
                <li key={i} className="flex items-center justify-between text-foreground gap-2">
                  <span className="font-mono text-xs flex-1">
                    {CIRCLED_NUMBERS[i] ?? `(${i + 1})`} ({Math.round(wp.pos.x / PARSEC)},{" "}
                    {Math.round(wp.pos.y / PARSEC)})
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ~{wp.cumulativeTurns} turn{wp.cumulativeTurns !== 1 ? "s" : ""}
                  </span>
                  {waypointEditMode && (
                    <button
                      onClick={() => onRemoveWaypoint(i)}
                      className="text-red-400 hover:text-red-300 transition-colors p-0.5"
                      aria-label="Delete waypoint"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}

        {isOwn && waypointInfo.length === 0 && !waypointEditMode && (
          <div className="text-muted-foreground italic">Stationary</div>
        )}

        {isOwn && (
          <div className="elevated-surface rounded-md border border-[var(--color-panel-border)] p-3">
            {!waypointEditMode ? (
              <button
                onClick={onEnterWaypointMode}
                className="w-full rounded bg-blue-600 hover:bg-blue-700 px-3 py-1.5 text-sm font-medium transition-colors duration-200 hover:-translate-y-px"
              >
                Edit Waypoints
              </button>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground bg-blue-950/30 border border-blue-900/50 rounded px-2 py-1.5">
                  Click the map to add waypoints
                </div>
                <button
                  onClick={onExitWaypointMode}
                  className="w-full rounded bg-green-600 hover:bg-green-700 px-3 py-1.5 text-sm font-medium transition-colors duration-200"
                >
                  Done
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">ID: {fleet.id}</div>
    </div>
  );
}

interface DetailPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  selectedPlanet: PlayerPlanet | null;
  selectedFleet: PlayerFleet | null;
  currentPlayer: string;
  designs: Design[];
  waypointEditMode: boolean;
  editedWaypoints: Position[] | null;
  onEnterWaypointMode: () => void;
  onExitWaypointMode: () => void;
  onRemoveWaypoint: (index: number) => void;
  onClearAllWaypoints: () => void;
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
  onEnterWaypointMode,
  onExitWaypointMode,
  onRemoveWaypoint,
  onClearAllWaypoints,
}: DetailPanelProps) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="absolute -left-7 top-2 z-10 rounded-l border border-r-0 border-[var(--color-panel-border)] panel-surface p-1 text-muted-foreground hover:text-foreground transition-colors duration-200"
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
                fleet={selectedFleet}
                currentPlayer={currentPlayer}
                designs={designs}
                waypointEditMode={waypointEditMode}
                editedWaypoints={editedWaypoints}
                onEnterWaypointMode={onEnterWaypointMode}
                onExitWaypointMode={onExitWaypointMode}
                onRemoveWaypoint={onRemoveWaypoint}
                onClearAllWaypoints={onClearAllWaypoints}
              />
            ) : selectedPlanet ? (
              <PlanetDetail planet={selectedPlanet} currentPlayer={currentPlayer} />
            ) : (
              <div className="flex h-full flex-col p-4">
                <h2 className="text-sm font-semibold text-muted-foreground">Nothing selected</h2>
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
