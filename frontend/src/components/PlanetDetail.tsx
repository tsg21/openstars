import { useEffect, useMemo, useRef, useState } from "react";
import { ListX, Minus, Plus, Trash2 } from "lucide-react";
import type {
  Habitability,
  PlayerFleet,
  PlayerPlanet,
  PlayerProductionQueueItem,
  ProductionItemType,
} from "../types";
import { useGameCommands } from "../hooks/useGameCommands";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../lib/planetImages";
import { buildProductionQueueCommands } from "../lib/productionQueueCommands";
import { cn } from "../lib/utils";
import { Button } from "./Button";
import { MutedText } from "./MutedText";
import { DetailPanelCard, DetailPanelContent, DetailPanelHeading } from "./DetailPanelLayout";
import { ResourceBars } from "./ResourceBars";

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

const JOAT_HAB_LOW = 15;
const JOAT_HAB_HIGH = 85;

const HAB_CONFIG = [
  { key: "gravity" as const, label: "Gravity", color: "#3b82f6" },
  { key: "temperature" as const, label: "Temperature", color: "#dc2626" },
  { key: "radiation" as const, label: "Radiation", color: "#16a34a" },
];

let draftProductionQueueItemId = 0;

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

      ctx.font = "11px ui-monospace, monospace";
      ctx.fillStyle = "#9ca3af";
      ctx.textBaseline = "middle";
      ctx.textAlign = "left";
      ctx.fillText(label, 0, y);

      ctx.fillStyle = "#000000";
      ctx.beginPath();
      ctx.roundRect(barX, trackY, barW, barH, 2);
      ctx.fill();

      const bandX = barX + Math.round((JOAT_HAB_LOW / 100) * barW);
      const bandW = Math.round(((JOAT_HAB_HIGH - JOAT_HAB_LOW) / 100) * barW);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(bandX, trackY, bandW, barH, 2);
      ctx.fill();

      const mx = barX + Math.round((v / 100) * barW);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(mx, y, markerR, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(mx - markerR, y);
      ctx.lineTo(mx + markerR, y);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(mx, y - markerR);
      ctx.lineTo(mx, y + markerR);
      ctx.stroke();

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

function createDraftProductionQueueItem(itemType: ProductionItemType): PlayerProductionQueueItem {
  draftProductionQueueItemId += 1;
  return {
    id: `draft-${itemType}-${draftProductionQueueItemId}`,
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

export interface PlanetDetailProps {
  planet: PlayerPlanet;
  currentPlayer: string;
  fleetsInOrbit: PlayerFleet[];
  onSelectFleet: (fleetId: string) => void;
}

export function PlanetDetail({
  planet,
  currentPlayer,
  fleetsInOrbit,
  onSelectFleet,
}: PlanetDetailProps) {
  const { basePlayerState, replaceCommands } = useGameCommands();
  const isOwn = planet.owner === currentPlayer;
  const isEnemy = planet.owner != null && !isOwn;
  const isUncolonised = planet.owner === null || planet.owner === undefined;
  const productionQueue = planet.productionQueue ?? [];
  const baseProductionQueue =
    basePlayerState?.planets.find((candidate) => candidate.id === planet.id)?.productionQueue ?? [];

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
    const nextQueue = [...productionQueue, createDraftProductionQueueItem(itemType)];
    replaceCommands(
      { kind: "planet", id: planet.id },
      buildProductionQueueCommands(planet.id, baseProductionQueue, nextQueue),
    );
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

    replaceCommands(
      { kind: "planet", id: planet.id },
      buildProductionQueueCommands(planet.id, baseProductionQueue, nextQueue),
    );
  };

  const handleRemoveProductionItem = (itemId: string) => {
    const nextQueue = productionQueue.filter((item) => item.id !== itemId);
    replaceCommands(
      { kind: "planet", id: planet.id },
      buildProductionQueueCommands(planet.id, baseProductionQueue, nextQueue),
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
          <div className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">Fleets in Orbit</div>
          {fleetsInOrbit.map((fleet) => {
            const totalShips = (fleet.composition ?? []).reduce((sum, c) => sum + c.count, 0);
            const isOwnFleet = fleet.owner === currentPlayer;
            return (
              <button
                key={fleet.id}
                type="button"
                className="flex w-full items-center justify-between rounded px-2 py-1 text-left transition-colors hover:bg-white/8"
                onClick={() => onSelectFleet(fleet.id)}
              >
                <span className="min-w-0">
                  <span className="block truncate text-foreground">
                    {isOwnFleet ? fleet.name?.trim() || fleet.id : "Fleet"}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {totalShips > 0 ? `${totalShips} ship${totalShips !== 1 ? "s" : ""}` : "No ship data"}
                  </span>
                </span>
                <span className={isOwnFleet ? "text-blue-400" : "text-red-400"}>
                  {isOwnFleet ? "You" : fleet.owner}
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
                  <span className="font-semibold text-foreground">
                    {planet.population.toLocaleString()}
                  </span>
                </div>

                {planet.mines != null && (
                  <div>
                    <MutedText>Mines:</MutedText>{" "}
                    <span className="font-semibold text-foreground">
                      {planet.mines.toLocaleString()}
                    </span>
                  </div>
                )}

                {planet.factories != null && (
                  <div>
                    <MutedText>Factories:</MutedText>{" "}
                    <span className="font-semibold text-foreground">
                      {planet.factories.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}

            {planet.scanLevel === "detailed" && planet.minerals && (
              <ResourceBars
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
                  <span className="font-semibold text-foreground">
                    {planet.maxPopulation.toLocaleString()}
                  </span>
                </div>
                {planet.popGrowth != null && (
                  <div>
                    <MutedText>Growth:</MutedText>{" "}
                    <span className="font-semibold text-foreground">
                      {planet.popGrowth >= 0 ? "+" : ""}
                      {planet.popGrowth.toLocaleString()} / turn
                    </span>
                  </div>
                )}
              </div>
            )}

            {planet.scanLevel === "basic" && (
              <div className="mt-1 text-xs italic text-muted-foreground">
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
                onClick={() =>
                  replaceCommands(
                    { kind: "planet", id: planet.id },
                    buildProductionQueueCommands(planet.id, baseProductionQueue, []),
                  )
                }
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
              {productionQueue.map((item) => (
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
              ))}
            </div>
          )}
        </DetailPanelCard>
      )}
    </DetailPanelContent>
  );
}
