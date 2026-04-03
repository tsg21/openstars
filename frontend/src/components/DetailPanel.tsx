import { useEffect, useRef, useMemo, useState, type ReactNode } from "react";
import { ListX, Minus, PanelRightClose, PanelRightOpen, Plus, RefreshCw, Trash2 } from "lucide-react";
import type {
  PlayerPlanet,
  PlayerFleet,
  Design,
  Position,
  Waypoint,
  WaypointTask,
  Minerals,
  Habitability,
  PlayerProductionQueueItem,
  ProductionItemType,
} from "../types";
import { PARSEC } from "../types";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../lib/planetImages";
import { cn } from "../lib/utils";
import { Button } from "./Button";
import { MutedText } from "./MutedText";
import { TransportTaskEditor, TransferTaskEditor } from "./WaypointTaskEditor";

const CIRCLED_NUMBERS = [
  "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
  "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳",
];

const PRODUCTION_ITEM_LABELS: Record<ProductionItemType, string> = {
  mine: "Mine",
  factory: "Factory",
};

const PRODUCTION_ADD_OPTIONS: Array<{
  label: string;
  description: string;
  itemType?: ProductionItemType;
  available: boolean;
}> = [
  { label: "Mine", description: "5 resources", itemType: "mine", available: true },
  { label: "Factory", description: "10 resources, 4 germanium", itemType: "factory", available: true },
  { label: "Ship", description: "Not in Phase 1 yet", available: false },
  { label: "Starbase", description: "Not in Phase 1 yet", available: false },
  { label: "Defense", description: "Not in Phase 1 yet", available: false },
];

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

// JOAT race defaults — hardcoded until race design is implemented
const JOAT_HAB_LOW = 15;
const JOAT_HAB_HIGH = 85;

const HAB_CONFIG = [
  { key: "gravity"     as const, label: "Gravity",     color: "#3b82f6" },
  { key: "temperature" as const, label: "Temperature", color: "#dc2626" },
  { key: "radiation"   as const, label: "Radiation",   color: "#16a34a" },
];

function formatHabValue(key: keyof Habitability, v: number): string {
  if (key === "gravity") {
    const g = 0.12 * Math.pow(4.0 / 0.12, v / 100);
    return `${g.toFixed(2)}g`;
  }
  if (key === "temperature") {
    return `${Math.round((v - 50) * 4)}°C`;
  }
  return `${v}mR`;
}

function HabitabilityBars({ habitability }: { habitability: Habitability }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

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

    const labelW = 80;
    const valueW = 56;
    const barX = labelW;
    const barW = W - labelW - valueW - 4;
    const rowH = H / 3;
    const barH = 10;
    const markerR = 5;

    HAB_CONFIG.forEach(({ key, label, color }, i) => {
      const v = habitability[key];
      const y = i * rowH + rowH / 2;
      const trackY = y - barH / 2;

      // Label
      ctx.font = "11px ui-monospace, monospace";
      ctx.fillStyle = "#9ca3af";
      ctx.textBaseline = "middle";
      ctx.textAlign = "left";
      ctx.fillText(label, 0, y);

      // Track background (black)
      ctx.fillStyle = "#000000";
      ctx.beginPath();
      ctx.roundRect(barX, trackY, barW, barH, 2);
      ctx.fill();

      // Race range band
      const bandX = barX + Math.round((JOAT_HAB_LOW / 100) * barW);
      const bandW = Math.round(((JOAT_HAB_HIGH - JOAT_HAB_LOW) / 100) * barW);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(bandX, trackY, bandW, barH, 2);
      ctx.fill();

      // Crosshair marker
      const mx = barX + Math.round((v / 100) * barW);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      // Circle
      ctx.beginPath();
      ctx.arc(mx, y, markerR, 0, Math.PI * 2);
      ctx.stroke();
      // Horizontal line
      ctx.beginPath();
      ctx.moveTo(mx - markerR, y);
      ctx.lineTo(mx + markerR, y);
      ctx.stroke();
      // Vertical line
      ctx.beginPath();
      ctx.moveTo(mx, y - markerR);
      ctx.lineTo(mx, y + markerR);
      ctx.stroke();

      // Value label
      ctx.fillStyle = "#f9fafb";
      ctx.textAlign = "right";
      ctx.fillText(formatHabValue(key, v), W, y);
    });
  }, [habitability]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full"
      style={{ height: 66 }}
      role="img"
      aria-label="Habitability bars"
    />
  );
}

function PlanetDetail({
  planet,
  currentPlayer,
  fleetsInOrbit,
  onSelectFleet,
  onSetProductionQueue,
}: {
  planet: PlayerPlanet;
  currentPlayer: string;
  fleetsInOrbit: PlayerFleet[];
  onSelectFleet: (fleetId: string) => void;
  onSetProductionQueue: (planetId: string, queue: PlayerProductionQueueItem[]) => void;
}) {
  const isOwn = planet.owner === currentPlayer;
  const isEnemy = planet.owner != null && !isOwn;
  const isUncolonised = planet.owner === null || planet.owner === undefined;
  const productionQueue = planet.productionQueue ?? [];

  const [manifest, setManifest] = useState<PlanetImageManifest | null>(null);
  const [productionPickerOpen, setProductionPickerOpen] = useState(false);
  const productionPickerRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    if (!productionPickerOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      if (!productionPickerRef.current?.contains(event.target as Node)) {
        setProductionPickerOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [productionPickerOpen]);

  const handleAddProductionItem = (itemType: ProductionItemType) => {
    onSetProductionQueue(planet.id, [
      ...productionQueue,
      createDraftProductionQueueItem(itemType),
    ]);
    setProductionPickerOpen(false);
  };

  const handleAdjustProductionItemQuantity = (itemId: string, delta: -1 | 1) => {
    const nextQueue = productionQueue.flatMap((item) => {
      if (item.id !== itemId) {
        return [item];
      }

      const quantity = item.quantity + delta;
      if (quantity <= 0) {
        return [];
      }

      return [{ ...item, quantity }];
    });

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

      {fleetsInOrbit.length > 0 && (
        <DetailPanelCard className="space-y-1 text-sm">
          <div className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Fleets in Orbit</div>
          {fleetsInOrbit.map((fleet) => {
            const totalShips = (fleet.composition ?? []).reduce((sum, c) => sum + c.count, 0);
            const isOwn = fleet.owner === currentPlayer;
            return (
              <button
                key={fleet.id}
                type="button"
                className="w-full flex items-center justify-between rounded px-2 py-1 text-left hover:bg-white/8 transition-colors"
                onClick={() => onSelectFleet(fleet.id)}
              >
                <span className="text-foreground">
                  {totalShips > 0 ? `${totalShips} ship${totalShips !== 1 ? "s" : ""}` : "Fleet"}
                </span>
                <span className={isOwn ? "text-blue-400" : "text-red-400"}>
                  {isOwn ? "You" : fleet.owner}
                </span>
              </button>
            );
          })}
        </DetailPanelCard>
      )}

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

            {planet.scanLevel === "detailed" && planet.habitability && (
              <HabitabilityBars habitability={planet.habitability} />
            )}

            {isOwn && planet.scanLevel === "detailed" && planet.maxPopulation != null && (
              <div className="space-y-1">
                <div>
                  <MutedText>Max pop:</MutedText>{" "}
                  <span className="text-foreground font-semibold">
                    {planet.maxPopulation.toLocaleString()}
                  </span>
                </div>
                {planet.popGrowth != null && (
                  <div>
                    <MutedText>Growth:</MutedText>{" "}
                    <span className="text-foreground font-semibold">
                      {planet.popGrowth >= 0 ? "+" : ""}
                      {planet.popGrowth.toLocaleString()} / turn
                    </span>
                  </div>
                )}
              </div>
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
          <div className="relative flex items-center justify-between gap-3" ref={productionPickerRef}>
            <div>
              <MutedText>Production Queue</MutedText>
            </div>
            <div className="flex items-center gap-1">
              <Button
                size="icon"
                variant="dangerGhost"
                aria-label="Clear Queue"
                disabled={productionQueue.length === 0}
                onClick={() => onSetProductionQueue(planet.id, [])}
              >
                <ListX className="h-3 w-3" />
              </Button>
              <Button
                size="icon"
                variant="dashed"
                aria-label={productionPickerOpen ? "Close production item picker" : "Add production item"}
                aria-expanded={productionPickerOpen}
                onClick={() => setProductionPickerOpen((open) => !open)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>

            {productionPickerOpen && (
              <div className="absolute right-0 top-full z-10 mt-2 w-52 rounded-md border border-[var(--color-panel-border)] bg-black/95 p-1.5 shadow-2xl backdrop-blur">
                <div className="px-2 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Add To Queue
                </div>
                <div className="space-y-1">
                  {PRODUCTION_ADD_OPTIONS.map((option) => (
                    <button
                      key={option.label}
                      type="button"
                      disabled={!option.available}
                      className={cn(
                        "w-full rounded-md px-2 py-1.5 text-left transition-colors",
                        option.available
                          ? "hover:bg-white/8"
                          : "cursor-not-allowed opacity-45",
                      )}
                      onClick={() => {
                        if (option.itemType) {
                          handleAddProductionItem(option.itemType);
                        }
                      }}
                    >
                      <div className="text-sm text-foreground">{option.label}</div>
                      <div className="text-[11px] text-muted-foreground">{option.description}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {productionQueue.length === 0 ? (
            <div className="rounded-md border border-dashed border-[var(--color-panel-border)] px-3 py-4 text-center text-xs text-muted-foreground">
              Queue empty. Use + to add production items.
            </div>
          ) : (
            <div className="space-y-1.5">
              {productionQueue.map((item) => {
                return (
                  <div
                    key={item.id}
                    className="grid grid-cols-[minmax(0,1fr)_auto_auto_auto] items-center gap-2 rounded-md border border-[var(--color-panel-border)] bg-black/10 px-2 py-1.5"
                  >
                    <div className="truncate font-medium text-foreground">
                      {PRODUCTION_ITEM_LABELS[item.itemType]}
                    </div>
                    <div className="text-xs font-semibold text-muted-foreground">
                      {item.quantity}x
                    </div>
                    <div className="flex items-center gap-0.5">
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label={`Increase ${PRODUCTION_ITEM_LABELS[item.itemType]} quantity`}
                        onClick={() => handleAdjustProductionItemQuantity(item.id, 1)}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label={`Decrease ${PRODUCTION_ITEM_LABELS[item.itemType]} quantity`}
                        onClick={() => handleAdjustProductionItemQuantity(item.id, -1)}
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                    </div>
                    <div className="flex items-center justify-end">
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
                );
              })}
            </div>
          )}

        </DetailPanelCard>
      )}

      <div className="mt-auto pt-4 text-xs text-muted-foreground/50">ID: {planet.id}</div>
    </DetailPanelContent>
  );
}

const TASK_LABELS: Record<WaypointTask["type"], string> = {
  transport: "Transport",
  transfer: "Transfer",
};

const TASK_CHIP_CLASS: Record<WaypointTask["type"], string> = {
  transport: "bg-blue-900/50 text-blue-300 border border-blue-700/50",
  transfer: "bg-amber-900/50 text-amber-300 border border-amber-700/50",
};

function FleetDetail({
  fleet,
  currentPlayer,
  designs,
  waypointEditMode,
  editedWaypoints,
  editRepeat,
  onEnterWaypointMode,
  onExitWaypointMode,
  onRemoveWaypoint,
  onClearAllWaypoints,
  onToggleRepeat,
  onUpdateWaypointTask,
  waypointValidationErrors,
  ownFleets,
}: {
  fleet: PlayerFleet;
  currentPlayer: string;
  designs: Design[];
  waypointEditMode: boolean;
  editedWaypoints: Waypoint[] | null;
  editRepeat: boolean;
  onEnterWaypointMode: () => void;
  onExitWaypointMode: () => void;
  onRemoveWaypoint: (index: number) => void;
  onClearAllWaypoints: () => void;
  onToggleRepeat: () => void;
  onUpdateWaypointTask: (index: number, task: WaypointTask | null) => void;
  waypointValidationErrors: Record<string, string>;
  ownFleets: PlayerFleet[];
}) {
  const [activeTaskEdit, setActiveTaskEdit] = useState<number | null>(null);

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
    waypoint: Waypoint;
    distPc: number;
    legTurns: number;
    cumulativeTurns: number;
  }[] = [];
  let prevPos: Position = fleet.position;
  let totalTurns = 0;

  for (const wp of waypoints) {
    const distPc = distanceParsecs(prevPos, wp);
    const legTurns = estimatedTurns(distPc, effectiveSpeed);
    totalTurns += legTurns;
    waypointInfo.push({
      waypoint: wp,
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

        {isOwn && !waypointEditMode && fleet.repeat && (
          <div className="flex items-center gap-1.5 text-xs text-blue-300">
            <RefreshCw className="h-3 w-3" />
            Repeating route
          </div>
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
            <ol className="mt-1 space-y-2 pl-3">
              {waypointInfo.map((wp, i) => (
                <li key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-foreground gap-2">
                    <span className="font-mono text-xs flex-1">
                      {CIRCLED_NUMBERS[i] ?? `(${i + 1})`} ({Math.round(wp.waypoint.x / PARSEC)},{" "}
                      {Math.round(wp.waypoint.y / PARSEC)})
                    </span>
                    {wp.waypoint.task ? (
                      <span className={cn("text-xs rounded px-1.5 py-0.5 font-medium", TASK_CHIP_CLASS[wp.waypoint.task.type])}>
                        {TASK_LABELS[wp.waypoint.task.type]}
                      </span>
                    ) : (
                      <span className="text-xs rounded px-1.5 py-0.5 font-medium bg-neutral-800 text-muted-foreground border border-neutral-700">
                        No task
                      </span>
                    )}
                    <MutedText className="text-xs">
                      ~{wp.cumulativeTurns} turn{wp.cumulativeTurns !== 1 ? "s" : ""}
                    </MutedText>
                    {waypointEditMode && (
                      <>
                        <Button
                          onClick={() => setActiveTaskEdit((prev) => (prev === i ? null : i))}
                          variant="ghost"
                          size="xs"
                          className="px-1"
                        >
                          Edit task
                        </Button>
                        <Button
                          onClick={() => onRemoveWaypoint(i)}
                          variant="dangerGhost"
                          size="icon"
                          className="p-0.5"
                          aria-label="Delete waypoint"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </>
                    )}
                  </div>
                  {waypointEditMode && activeTaskEdit === i && (
                    <div className="ml-4 rounded border border-[var(--color-panel-border)] bg-black/20 p-2 text-xs space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Task type:</span>
                        {(["none", "transport", "transfer"] as const).map((type) => (
                          <button
                            key={type}
                            onClick={() => {
                              if (type === "none") {
                                onUpdateWaypointTask(i, null);
                              } else if (type !== wp.waypoint.task?.type) {
                                onUpdateWaypointTask(i, { type, orders: [] });
                              }
                            }}
                            className={cn(
                              "rounded px-2 py-0.5 font-medium capitalize border",
                              type === "none" && !wp.waypoint.task
                                ? "bg-neutral-700 text-foreground border-neutral-500"
                                : type === wp.waypoint.task?.type
                                  ? type === "transport"
                                    ? "bg-blue-800 text-blue-200 border-blue-600"
                                    : "bg-amber-800 text-amber-200 border-amber-600"
                                  : "bg-neutral-800 text-muted-foreground border-neutral-700 hover:bg-neutral-700",
                            )}
                          >
                            {type === "none" ? "None" : type === "transport" ? "Transport" : "Transfer"}
                          </button>
                        ))}
                      </div>
                      {wp.waypoint.task?.type === "transport" && (
                        <TransportTaskEditor
                          orders={wp.waypoint.task.orders}
                          onChange={(orders) =>
                            onUpdateWaypointTask(i, { type: "transport", orders })
                          }
                          validationErrors={Object.fromEntries(
                            Object.entries(waypointValidationErrors)
                              .filter(([k]) => k.startsWith(`waypoint-${i}-`))
                              .map(([k, v]) => [k.replace(`waypoint-${i}-`, ""), v]),
                          )}
                        />
                      )}
                      {wp.waypoint.task?.type === "transfer" && (
                        <TransferTaskEditor
                          fleetId={wp.waypoint.task.fleetId ?? null}
                          orders={wp.waypoint.task.orders}
                          ownFleets={ownFleets}
                          onChange={(fleetId, orders) =>
                            onUpdateWaypointTask(i, {
                              type: "transfer",
                              orders,
                              fleetId,
                            })
                          }
                          validationErrors={Object.fromEntries(
                            Object.entries(waypointValidationErrors)
                              .filter(([k]) => k.startsWith(`waypoint-${i}-`))
                              .map(([k, v]) => [k.replace(`waypoint-${i}-`, ""), v]),
                          )}
                        />
                      )}
                      <Button
                        size="xs"
                        variant="ghost"
                        onClick={() => setActiveTaskEdit(null)}
                      >
                        Close
                      </Button>
                    </div>
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
                <label className="flex items-center gap-2 cursor-pointer select-none text-sm">
                  <input
                    type="checkbox"
                    checked={editRepeat}
                    onChange={onToggleRepeat}
                    className="rounded"
                  />
                  <span>Repeat route</span>
                </label>
                <div className="text-xs text-muted-foreground bg-blue-950/30 border border-blue-900/50 rounded px-2 py-1.5">
                  Click the map to add waypoints
                </div>
                <Button
                  onClick={onExitWaypointMode}
                  variant="success"
                  fullWidth
                  disabled={Object.keys(waypointValidationErrors).length > 0}
                >
                  {Object.keys(waypointValidationErrors).length > 0
                    ? "Fix errors to save"
                    : "Done"}
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
  editedWaypoints: Waypoint[] | null;
  editRepeat: boolean;
  onEnterWaypointMode: () => void;
  onExitWaypointMode: () => void;
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
  onEnterWaypointMode,
  onExitWaypointMode,
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
                editRepeat={editRepeat}
                onEnterWaypointMode={onEnterWaypointMode}
                onExitWaypointMode={onExitWaypointMode}
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
