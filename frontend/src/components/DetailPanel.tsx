import { useEffect, useRef, useMemo, useState, type ReactNode } from "react";
import { PanelRightClose, PanelRightOpen, Trash2 } from "lucide-react";
import type { PlayerPlanet, PlayerFleet, Design, Position, Minerals } from "../types";
import { PARSEC } from "../types";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../lib/planetImages";
import { cn } from "../lib/utils";
import { Button } from "./Button";
import { MutedText } from "./MutedText";

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

/** Convert a bearing in degrees (0=north, clockwise) to a compass direction. */
function bearingToCompass(bearing: number): string {
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(bearing / 45) % 8;
  return directions[index];
}

function DetailPanelContent({ children }: { children: ReactNode }) {
  return <div className="flex h-full flex-col gap-3 p-4">{children}</div>;
}

function DetailPanelHeading({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <h2 className={cn("text-base font-semibold text-foreground", className)}>{children}</h2>;
}

function DetailPanelCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "elevated-surface rounded-md border border-[var(--color-panel-border)] p-3",
        className,
      )}
    >
      {children}
    </div>
  );
}

const MINERAL_CONFIG = [
  { key: "ironium",   label: "Ironium",   bright: "#60a5fa", dark: "#1e40af" },
  { key: "boranium",  label: "Boranium",  bright: "#facc15", dark: "#713f12" },
  { key: "germanium", label: "Germanium", bright: "#e5e7eb", dark: "#6b7280" },
] as const;

function MineralBars({
  minerals,
  miningRate,
  concentrations,
}: {
  minerals: Minerals;
  miningRate: Minerals | undefined;
  concentrations: Minerals | undefined;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const maxStock = Math.max(
    100,
    minerals.ironium,
    minerals.boranium,
    minerals.germanium,
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio ?? 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, W, H);

    const labelW = 72;
    const valueW = 52;
    const barX = labelW;
    const barW = W - labelW - valueW - 4;
    const rowH = H / 3;
    const barH = 10;

    MINERAL_CONFIG.forEach(({ key, label, bright, dark }, i) => {
      const stock = minerals[key];
      const rate = miningRate?.[key] ?? 0;
      const y = i * rowH + rowH / 2;

      // Label
      ctx.font = "11px ui-monospace, monospace";
      ctx.fillStyle = "#9ca3af";
      ctx.textBaseline = "middle";
      ctx.textAlign = "left";
      ctx.fillText(label, 0, y);

      // Track background
      const trackY = y - barH / 2;
      ctx.fillStyle = "#1f2937";
      ctx.beginPath();
      ctx.roundRect(barX, trackY, barW, barH, 2);
      ctx.fill();

      // Stockpile bar (bright), anchored left
      const stockW = Math.round((stock / maxStock) * barW);
      if (stockW > 0) {
        ctx.fillStyle = bright;
        ctx.beginPath();
        ctx.roundRect(barX, trackY, stockW, barH, 2);
        ctx.fill();
      }

      // Mining rate bar (dark), immediately right of the stockpile bar
      const rateW = Math.round((rate / maxStock) * barW);
      if (rateW > 0) {
        ctx.fillStyle = dark;
        ctx.beginPath();
        ctx.roundRect(barX + stockW, trackY, rateW, barH, 2);
        ctx.fill();
      }

      // Value
      ctx.fillStyle = "#f9fafb";
      ctx.textAlign = "right";
      ctx.fillText(`${stock.toLocaleString()}kT`, W, y);
    });
  }, [minerals, miningRate, maxStock]);

  const conc = concentrations;

  return (
    <div className="space-y-1">
      <canvas
        ref={canvasRef}
        className="w-full"
        style={{ height: 66 }}
        aria-label="Mineral stockpile bars"
      />
      {conc && (
        <div className="text-xs text-muted-foreground">
          conc: {conc.ironium} / {conc.boranium} / {conc.germanium}
        </div>
      )}
    </div>
  );
}

function PlanetDetail({
  planet,
  currentPlayer,
}: {
  planet: PlayerPlanet;
  currentPlayer: string;
}) {
  const isOwn = planet.owner === currentPlayer;
  const isEnemy = planet.owner != null && !isOwn;
  const isUncolonised = planet.owner === null || planet.owner === undefined;

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
    <DetailPanelContent>
      <DetailPanelHeading>{planet.name}</DetailPanelHeading>

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

      <DetailPanelCard className="space-y-2 text-sm">
        {planet.scanLevel === "none" ? (
          <div className="text-zinc-500 italic">Unexplored — no scanner data</div>
        ) : (
          <>
            {isOwn && (
              <div className="text-blue-400">
                <MutedText>Owner:</MutedText> You
              </div>
            )}
            {isEnemy && (
              <div className="text-red-400">
                <MutedText>Owner:</MutedText> {planet.owner}
              </div>
            )}
            {isUncolonised && <div className="text-zinc-500">Uncolonised</div>}

            {planet.scanLevel === "detailed" && planet.population !== undefined && (
              <div>
                <MutedText>Population:</MutedText>{" "}
                <span className="text-foreground font-semibold">
                  {planet.population.toLocaleString()}
                </span>
              </div>
            )}

            {planet.scanLevel === "detailed" && planet.minerals && (
              <MineralBars
                minerals={planet.minerals}
                miningRate={planet.miningRate}
                concentrations={planet.concentrations}
              />
            )}

            {planet.scanLevel === "basic" && (
              <div className="text-xs text-muted-foreground italic mt-1">
                Basic scan — no detailed intel
              </div>
            )}
          </>
        )}
      </DetailPanelCard>

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">ID: {planet.id}</div>
    </DetailPanelContent>
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
    <DetailPanelContent>
      <DetailPanelHeading>
        Fleet <MutedText className="font-mono text-sm">{fleet.id}</MutedText>
      </DetailPanelHeading>

      <div className="space-y-3 text-sm">
        <DetailPanelCard>
          <div className={isOwn ? "text-blue-400" : "text-red-400"}>
            <MutedText>Owner:</MutedText> {isOwn ? "You" : fleet.owner}
          </div>
          {!isOwn && fleet.bearing != null && (
            <div>
              <MutedText>Heading:</MutedText>{" "}
              <span className="text-foreground">
                {bearingToCompass(fleet.bearing)} ({Math.round(fleet.bearing)}°)
              </span>
            </div>
          )}
          {!isOwn && fleet.bearing == null && (
            <div className="text-muted-foreground italic">Stationary</div>
          )}
        </DetailPanelCard>

        {isOwn && composition.length > 0 && (
          <DetailPanelCard>
            <MutedText>Ships:</MutedText>
            <ul className="mt-1 space-y-0.5 pl-3">
              {composition.map((c, i) => (
                <li key={i} className="text-foreground">
                  {c.name} × {c.count}
                </li>
              ))}
            </ul>
          </DetailPanelCard>
        )}

        {isOwn && effectiveSpeed > 0 && (
          <DetailPanelCard>
            <MutedText>Speed:</MutedText>{" "}
            <span className="text-foreground font-semibold">{effectiveSpeed} pc/turn</span>
          </DetailPanelCard>
        )}

        {isOwn && waypointInfo.length > 0 && (
          <DetailPanelCard>
            <div className="flex items-center justify-between">
              <MutedText>Waypoints:</MutedText>
              {waypointEditMode && (
                <Button
                  onClick={onClearAllWaypoints}
                  variant="dangerGhost"
                  size="xs"
                  className="px-0"
                >
                  Clear All
                </Button>
              )}
            </div>
            <ol className="mt-1 space-y-1 pl-3">
              {waypointInfo.map((wp, i) => (
                <li key={i} className="flex items-center justify-between text-foreground gap-2">
                  <span className="font-mono text-xs flex-1">
                    {CIRCLED_NUMBERS[i] ?? `(${i + 1})`} ({Math.round(wp.pos.x / PARSEC)},{" "}
                    {Math.round(wp.pos.y / PARSEC)})
                  </span>
                  <MutedText className="text-xs">
                    ~{wp.cumulativeTurns} turn{wp.cumulativeTurns !== 1 ? "s" : ""}
                  </MutedText>
                  {waypointEditMode && (
                    <Button
                      onClick={() => onRemoveWaypoint(i)}
                      variant="dangerGhost"
                      size="icon"
                      className="p-0.5"
                      aria-label="Delete waypoint"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </li>
              ))}
            </ol>
          </DetailPanelCard>
        )}

        {isOwn && waypointInfo.length === 0 && !waypointEditMode && (
          <div className="text-muted-foreground italic">Stationary</div>
        )}

        {isOwn && (
          <DetailPanelCard>
            {!waypointEditMode ? (
              <Button
                onClick={onEnterWaypointMode}
                variant="primary"
                fullWidth
                className="hover:-translate-y-px transition-all"
              >
                Edit Waypoints
              </Button>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground bg-blue-950/30 border border-blue-900/50 rounded px-2 py-1.5">
                  Click the map to add waypoints
                </div>
                <Button
                  onClick={onExitWaypointMode}
                  variant="success"
                  fullWidth
                >
                  Done
                </Button>
              </div>
            )}
          </DetailPanelCard>
        )}
      </div>

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">ID: {fleet.id}</div>
    </DetailPanelContent>
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
