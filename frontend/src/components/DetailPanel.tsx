import { useEffect, useRef, useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, PanelRightClose, PanelRightOpen, Plus, Trash2 } from "lucide-react";
import type {
  PlayerPlanet,
  PlayerFleet,
  Design,
  Position,
  Minerals,
  PlayerProductionQueueItem,
  ProductionItemType,
} from "../types";
import { PARSEC } from "../types";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../lib/planetImages";
import { cn } from "../lib/utils";
import { Button } from "./Button";
import { MutedText } from "./MutedText";

const CIRCLED_NUMBERS = [
  "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
  "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳",
];

const PRODUCTION_ITEM_LABELS: Record<ProductionItemType, string> = {
  mine: "Mine",
  factory: "Factory",
};

const PRODUCTION_COSTS: Record<ProductionItemType, { resources: number; germanium: number }> = {
  mine: { resources: 5, germanium: 0 },
  factory: { resources: 10, germanium: 4 },
};

let draftProductionQueueItemId = 0;

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
  miningRate: Minerals | null | undefined;
  concentrations: Minerals | null | undefined;
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
  onSetProductionQueue,
}: {
  planet: PlayerPlanet;
  currentPlayer: string;
  onSetProductionQueue: (planetId: string, queue: PlayerProductionQueueItem[]) => void;
}) {
  const isOwn = planet.owner === currentPlayer;
  const isEnemy = planet.owner != null && !isOwn;
  const isUncolonised = planet.owner === null || planet.owner === undefined;
  const productionQueue = planet.productionQueue ?? [];

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

  const handleAddProductionItem = (itemType: ProductionItemType) => {
    onSetProductionQueue(planet.id, [
      ...productionQueue,
      createDraftProductionQueueItem(itemType),
    ]);
  };

  const handleMoveProductionItem = (itemId: string, direction: -1 | 1) => {
    const itemIndex = productionQueue.findIndex((item) => item.id === itemId);
    const targetIndex = itemIndex + direction;
    if (itemIndex === -1 || targetIndex < 0 || targetIndex >= productionQueue.length) {
      return;
    }

    const nextQueue = [...productionQueue];
    const [item] = nextQueue.splice(itemIndex, 1);
    nextQueue.splice(targetIndex, 0, item);
    onSetProductionQueue(planet.id, nextQueue);
  };

  const handleRemoveProductionItem = (itemId: string) => {
    onSetProductionQueue(
      planet.id,
      productionQueue.filter((item) => item.id !== itemId),
    );
  };

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

            {planet.scanLevel === "detailed" && planet.population != null && (
              <div className="space-y-1">
                <div>
                  <MutedText>Population:</MutedText>{" "}
                  <span className="text-foreground font-semibold">
                    {planet.population.toLocaleString()}
                  </span>
                </div>

                {planet.mines != null && (
                  <div>
                    <MutedText>Mines:</MutedText>{" "}
                    <span className="text-foreground font-semibold">
                      {planet.mines.toLocaleString()}
                    </span>
                  </div>
                )}

                {planet.factories != null && (
                  <div>
                    <MutedText>Factories:</MutedText>{" "}
                    <span className="text-foreground font-semibold">
                      {planet.factories.toLocaleString()}
                    </span>
                  </div>
                )}
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

      {isOwn && planet.scanLevel === "detailed" && (
        <DetailPanelCard className="space-y-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <MutedText>Production Queue</MutedText>
            </div>
            <div className="flex gap-2">
              <Button
                size="xs"
                variant="dashed"
                onClick={() => handleAddProductionItem("mine")}
              >
                <Plus className="mr-1 h-3 w-3" />
                Mine
              </Button>
              <Button
                size="xs"
                variant="dashed"
                onClick={() => handleAddProductionItem("factory")}
              >
                <Plus className="mr-1 h-3 w-3" />
                Factory
              </Button>
            </div>
          </div>

          {productionQueue.length === 0 ? (
            <div className="rounded-md border border-dashed border-[var(--color-panel-border)] px-3 py-4 text-center text-xs text-muted-foreground">
              Queue empty. Add mines or factories to start building.
            </div>
          ) : (
            <div className="space-y-2">
              {productionQueue.map((item, index) => {
                const cost = PRODUCTION_COSTS[item.itemType];
                const progressPercent = Math.floor(
                  (item.progress.resourcesSpent / cost.resources) * 100,
                );
                return (
                  <div
                    key={item.id}
                    className="rounded-md border border-[var(--color-panel-border)] bg-black/10 p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-foreground">
                          {PRODUCTION_ITEM_LABELS[item.itemType]}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {item.quantity} remaining
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          aria-label={`Move ${PRODUCTION_ITEM_LABELS[item.itemType]} up`}
                          disabled={index === 0}
                          onClick={() => handleMoveProductionItem(item.id, -1)}
                        >
                          <ArrowUp className="h-3 w-3" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          aria-label={`Move ${PRODUCTION_ITEM_LABELS[item.itemType]} down`}
                          disabled={index === productionQueue.length - 1}
                          onClick={() => handleMoveProductionItem(item.id, 1)}
                        >
                          <ArrowDown className="h-3 w-3" />
                        </Button>
                        <Button
                          size="icon"
                          variant="dangerGhost"
                          aria-label={`Remove ${PRODUCTION_ITEM_LABELS[item.itemType]}`}
                          onClick={() => handleRemoveProductionItem(item.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="mt-3 space-y-1">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>
                          Current unit: {item.progress.resourcesSpent}/{cost.resources} resources
                        </span>
                        <span>{progressPercent}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-muted/60">
                        <div
                          className="h-full rounded-full bg-[var(--color-player-self)] transition-[width] duration-200"
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                      {cost.germanium > 0 && (
                        <div className="text-xs text-muted-foreground">
                          Germanium: {item.progress.mineralsSpent.germanium}/{cost.germanium}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="rounded-md border border-dashed border-[var(--color-panel-border)] px-3 py-2 text-xs text-muted-foreground">
            Blocked-state reason is not exposed by the current player state yet. Follow-up backend
            state is needed to distinguish mineral shortage from resource shortage in the UI.
          </div>

          <Button
            size="xs"
            variant="dangerGhost"
            disabled={productionQueue.length === 0}
            onClick={() => onSetProductionQueue(planet.id, [])}
          >
            Clear Queue
          </Button>
        </DetailPanelCard>
      )}

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
  onSetPlanetProductionQueue: (planetId: string, queue: PlayerProductionQueueItem[]) => void;
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
  onSetPlanetProductionQueue,
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
              <PlanetDetail
                planet={selectedPlanet}
                currentPlayer={currentPlayer}
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

function createDraftProductionQueueItem(itemType: ProductionItemType): PlayerProductionQueueItem {
  draftProductionQueueItemId += 1;
  return {
    id: `draft-${draftProductionQueueItemId}`,
    itemType,
    quantity: 1,
    progress: {
      resourcesSpent: 0,
      mineralsSpent: {
        ironium: 0,
        boranium: 0,
        germanium: 0,
      },
    },
  };
}
