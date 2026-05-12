import { useEffect, useMemo, useRef, useState } from "react";
import { ListX, Minus, Plus, Trash2, X } from "lucide-react";
import type {
  DesignSummary,
  Habitability,
  PlayerFleet,
  PlayerPlanet,
  PlayerProductionQueueItem,
  ProductionItemType,
  StarbaseType,
} from "../../types";
import { useGameCommands } from "../../hooks/useGameCommands";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../../lib/planetImages";
import { buildPlanetScopeCommands } from "../../lib/productionQueueCommands";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { MutedText } from "../ui/MutedText";
import { DetailPanelContent, DetailPanelHeading } from "../ui/DetailPanelLayout";
import { PanelCard } from "../ui/PanelCard";
import { ResourceBars } from "../ui/ResourceBars";
import { FleetComposer } from "./FleetComposer";

const PRODUCTION_ITEM_LABELS: Record<ProductionItemType, string> = {
  mine: "Mine",
  factory: "Factory",
  starbase: "Starbase",
  ship: "Ship",
  planetary_scanner: "Planetary Scanner",
};

const BASE_PRODUCTION_ADD_OPTIONS: Array<{
  label: string;
  description: string;
  itemType?: ProductionItemType;
  targetType?: StarbaseType;
  available: boolean;
}> = [
  { label: "Mine", description: "5 resources", itemType: "mine", available: true },
  { label: "Factory", description: "10 resources, 4 germanium", itemType: "factory", available: true },
  { label: "Orbital Fort", description: "Build/upgrade starbase (no shipbuilding)", itemType: "starbase", targetType: "orbital_fort", available: true },
  { label: "Space Station", description: "Build/upgrade starbase (shipbuilding)", itemType: "starbase", targetType: "space_station", available: true },
  { label: "Planetary Scanner", description: "100 resources, 10 ironium, 10 boranium, 70 germanium", itemType: "planetary_scanner", available: true },
  { label: "Defense", description: "Not in Phase 1 yet", available: false },
];

type ProductionAddOption = (typeof BASE_PRODUCTION_ADD_OPTIONS)[number];

type ShipDesignOption = {
  label: string;
  description: string;
  itemType: "ship";
  designId: string;
  available: boolean;
};

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

function createDraftProductionQueueItem(
  itemType: ProductionItemType,
  targetType: StarbaseType | null = null,
  designId: string | null = null,
): PlayerProductionQueueItem {
  draftProductionQueueItemId += 1;
  return {
    id: `draft-${itemType}-${draftProductionQueueItemId}`,
    itemType,
    targetType,
    designId,
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
  shipDesigns: DesignSummary[];
}

export function PlanetDetail({
  planet,
  currentPlayer,
  fleetsInOrbit,
  onSelectFleet,
  shipDesigns,
}: PlanetDetailProps) {
  const { basePlayerState, replaceCommands } = useGameCommands();
  const isOwn = planet.owner === currentPlayer;
  const isStale = planet.scanAge > 0;
  const isEnemy = planet.owner != null && !isOwn;
  const isUncolonised = planet.owner === null || planet.owner === undefined;
  const productionQueue = planet.productionQueue ?? [];
  const baseProductionQueue =
    basePlayerState?.planets.find((candidate) => candidate.id === planet.id)?.productionQueue ?? [];
  const baseContributeOnlyLeftoverToResearch =
    basePlayerState?.planets.find((candidate) => candidate.id === planet.id)?.contributeOnlyLeftoverToResearch ?? null;
  const showResearchContribution =
    planet.contributeOnlyLeftoverToResearch !== null &&
    basePlayerState?.research != null &&
    planet.scanLevel === "detailed" &&
    planet.scanAge === 0;

  const [manifest, setManifest] = useState<PlanetImageManifest | null>(null);
  const [productionPickerOpen, setProductionPickerOpen] = useState(false);
  const [populationDialogOpen, setPopulationDialogOpen] = useState(false);
  const [showOrbitFleetList, setShowOrbitFleetList] = useState(false);
  const [showFleetComposer, setShowFleetComposer] = useState(false);
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

  const handleAddProductionItem = (
    itemType: ProductionItemType,
    targetType?: StarbaseType,
    designId?: string,
  ) => {
    const nextQueue = [
      ...productionQueue,
      createDraftProductionQueueItem(itemType, targetType ?? null, designId ?? null),
    ];
    replaceCommands(
      { kind: "planet", id: planet.id },
      buildPlanetScopeCommands(
        planet.id,
        baseProductionQueue,
        nextQueue,
        baseContributeOnlyLeftoverToResearch,
        planet.contributeOnlyLeftoverToResearch,
      ),
    );
    setProductionPickerOpen(false);
  };
  const starbase = planet.starbase;
  const isStarbasePresent = starbase != null && (starbase as { present?: boolean }).present !== false;
  const starbaseType = starbase && "type" in starbase ? starbase.type : null;
  const starbaseCanBuildShips = starbase && "canBuildShips" in starbase ? starbase.canBuildShips : null;
  const productionAddOptions = BASE_PRODUCTION_ADD_OPTIONS.map((option) => {
    if (option.itemType !== "starbase") return option;
    const isDuplicate = productionQueue.some((item) => item.itemType === "starbase");
    if (isDuplicate) return { ...option, available: false, description: "Starbase already queued" };
    if (option.targetType != null && option.targetType === starbaseType) {
      return { ...option, available: false, description: "Already this starbase type" };
    }
    return option;
  });
  const hasQueuedPlanetaryScanner = productionQueue.some((item) => item.itemType === "planetary_scanner");
  const scannerInstalled = planet.scanner?.installed === true;
  const filteredProductionAddOptions = productionAddOptions.flatMap((option) => {
    if (option.itemType !== "planetary_scanner") {
      return [option];
    }
    if (scannerInstalled) {
      return [];
    }
    if (hasQueuedPlanetaryScanner) {
      return [];
    }
    return [option];
  });
  const shipDesignOptions: ShipDesignOption[] = shipDesigns.map((design) => ({
      label: design.name,
      description: `${design.cost.resources} resources, ${design.cost.minerals.ironium} ironium, ${design.cost.minerals.boranium} boranium, ${design.cost.minerals.germanium} germanium`,
      itemType: "ship" as const,
      designId: design.id,
      available: isStarbasePresent && starbaseCanBuildShips === true,
    }));
  const productionPickerOptions: Array<ProductionAddOption | ShipDesignOption> = [
    ...filteredProductionAddOptions,
    ...shipDesignOptions,
  ];

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
      buildPlanetScopeCommands(
        planet.id,
        baseProductionQueue,
        nextQueue,
        baseContributeOnlyLeftoverToResearch,
        planet.contributeOnlyLeftoverToResearch,
      ),
    );
  };

  const handleRemoveProductionItem = (itemId: string) => {
    const nextQueue = productionQueue.filter((item) => item.id !== itemId);
    replaceCommands(
      { kind: "planet", id: planet.id },
      buildPlanetScopeCommands(
        planet.id,
        baseProductionQueue,
        nextQueue,
        baseContributeOnlyLeftoverToResearch,
        planet.contributeOnlyLeftoverToResearch,
      ),
    );
  };

  const ownFleetsInOrbit = fleetsInOrbit.filter((fleet) => fleet.owner === currentPlayer);
  const handleOrbitSummaryClick = () => {
    if (fleetsInOrbit.length === 1) {
      onSelectFleet(fleetsInOrbit[0].id);
      return;
    }

    if (fleetsInOrbit.length > 1) {
      setShowOrbitFleetList(true);
    }
  };

  const renderOrbitFleetRows = () =>
    fleetsInOrbit.map((fleet) => {
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
    });

  return (
    <DetailPanelContent>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <DetailPanelHeading>{planet.name}</DetailPanelHeading>
          {isOwn && <div className="mt-1 text-sm text-blue-400">You</div>}
          {isEnemy && <div className="mt-1 text-sm text-red-400">{planet.owner}</div>}
          {fleetsInOrbit.length > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <button
                type="button"
                className="inline-flex items-center rounded-md border border-[var(--color-panel-border)] bg-white/5 px-2.5 py-1 text-left text-sm text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground"
                onClick={handleOrbitSummaryClick}
              >
                {fleetsInOrbit.length === 1
                  ? `${fleetsInOrbit[0].name?.trim() || fleetsInOrbit[0].id} in orbit`
                  : `${fleetsInOrbit.length} fleets in orbit`}
              </button>
              {ownFleetsInOrbit.length >= 1 && (
                <Button variant="secondary" onClick={() => setShowFleetComposer(true)}>
                  Manage Fleets
                </Button>
              )}
            </div>
          )}
        </div>

        <div className="h-20 w-20 shrink-0 overflow-hidden rounded-md border border-[var(--color-panel-border)] bg-black/20">
          {planetImageUrl ? (
            <img
              src={planetImageUrl}
              alt={`${planet.name} render`}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center px-2 text-center text-[10px] text-muted-foreground">
              No planet image available
            </div>
          )}
        </div>
      </div>

      {showOrbitFleetList && fleetsInOrbit.length > 1 ? (
        <PanelCard variant="surface" className="space-y-1 text-sm">
          <div className="mb-1 flex items-center justify-between gap-3">
            <div className="text-xs uppercase tracking-widest text-muted-foreground">Fleets in Orbit</div>
            <Button
              size="icon"
              variant="ghost"
              aria-label="Close fleets in orbit"
              onClick={() => setShowOrbitFleetList(false)}
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
          {renderOrbitFleetRows()}
        </PanelCard>
      ) : (
        <>
          <PanelCard variant="surface" className="space-y-2 text-sm">
            <div className="text-xs uppercase tracking-widest text-muted-foreground">Planet</div>
            {planet.scanLevel === "none" ? (
              <div className="text-zinc-500 italic">Unexplored — no scanner data</div>
            ) : (
              <>
                {isStale && (
                  <div className="rounded border border-amber-300/30 bg-amber-200/10 px-2 py-1 text-xs text-amber-200">
                    Scan age: {planet.scanAge} {planet.scanAge === 1 ? "turn" : "turns"}
                  </div>
                )}
                <div className={cn(isStale && "opacity-50")}>
                  {isUncolonised && <div className="text-zinc-500">Uncolonised</div>}

                  {(planet.scanLevel === "detailed") && planet.population != null && (
                    <div className="space-y-1">
                      <div className="relative">
                        <MutedText>Population:</MutedText>{" "}
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 font-semibold text-foreground",
                            isOwn && planet.maxPopulation != null && "cursor-help",
                          )}
                          onMouseEnter={() => {
                            if (isOwn && planet.maxPopulation != null) {
                              setPopulationDialogOpen(true);
                            }
                          }}
                          onMouseLeave={() => setPopulationDialogOpen(false)}
                          onFocus={() => {
                            if (isOwn && planet.maxPopulation != null) {
                              setPopulationDialogOpen(true);
                            }
                          }}
                          onBlur={() => setPopulationDialogOpen(false)}
                          tabIndex={isOwn && planet.maxPopulation != null ? 0 : undefined}
                          aria-label={isOwn && planet.maxPopulation != null ? "Population details" : undefined}
                        >
                          <span>{planet.population.toLocaleString()}</span>
                          {isOwn && planet.popGrowth != null && (
                            <span className="font-semibold text-foreground">
                              ({planet.popGrowth >= 0 ? "+" : ""}
                              {planet.popGrowth.toLocaleString()} / turn)
                            </span>
                          )}
                        </span>
                        {isOwn && planet.maxPopulation != null && populationDialogOpen && (
                          <div
                            role="dialog"
                            aria-label="Population details"
                            className="absolute left-0 top-full z-10 mt-2 min-w-40 rounded-md border border-[var(--color-panel-border)] bg-black/95 px-3 py-2 text-xs shadow-2xl backdrop-blur"
                          >
                            <MutedText>Max pop:</MutedText>{" "}
                            <span className="font-semibold text-foreground">
                              {planet.maxPopulation.toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>

                      {(planet.resources != null || planet.mines != null || planet.factories != null) && (
                        <div className="flex flex-wrap gap-x-4 gap-y-1">
                          {planet.resources != null && (
                            <div>
                              <MutedText>Resources:</MutedText>{" "}
                              <span className="font-semibold text-foreground">
                                {planet.resources.toLocaleString()}
                              </span>
                            </div>
                          )}

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
                    </div>
                  )}

                  {(planet.scanLevel === "detailed") && (
                    <div>
                      <MutedText>Scanner:</MutedText>{" "}
                      {isOwn ? (
                        planet.scanner && "name" in planet.scanner ? (
                          <span className="font-semibold text-foreground">{planet.scanner.name}</span>
                        ) : (
                          <span className="italic text-zinc-500">None installed</span>
                        )
                      ) : (
                        <span className={planet.scanner?.installed ? "text-foreground" : "text-zinc-500"}>
                          {planet.scanner?.installed ? "Installed" : "None"}
                        </span>
                      )}
                    </div>
                  )}

                  {(planet.scanLevel === "detailed") && planet.minerals && (
                    <ResourceBars
                      minerals={planet.minerals}
                      miningRate={isStale ? undefined : planet.miningRate}
                      concentrations={planet.concentrations}
                    />
                  )}

                  {(planet.scanLevel === "detailed") && planet.habitability && (
                    <HabitabilityBars habitability={planet.habitability} />
                  )}

                  {planet.scanLevel === "basic" && (
                    <div className="mt-1 text-xs italic text-muted-foreground">
                      Basic scan — no detailed intel
                    </div>
                  )}
                </div>

              </>
            )}
          </PanelCard>

          {planet.scanLevel !== "none" && (
            <PanelCard variant="surface" className="space-y-2 text-sm">
              <div className="text-xs uppercase tracking-widest text-muted-foreground">Starbase</div>
              <div>
                {isStarbasePresent ? (
                  <span className={starbaseCanBuildShips ? "text-yellow-400" : "text-blue-400"}>
                    {starbaseType ? starbaseType.replace("_", " ") : "Present"}
                    {starbaseCanBuildShips != null
                      ? starbaseCanBuildShips
                        ? " (can build ships)"
                        : " (cannot build ships)"
                      : ""}
                  </span>
                ) : (
                  <span className="text-zinc-500">None</span>
                )}
              </div>
            </PanelCard>
          )}

          {showResearchContribution && (
            <PanelCard variant="surface" className="space-y-2 text-sm">
              <div className="text-xs uppercase tracking-widest text-muted-foreground">Research</div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={planet.contributeOnlyLeftoverToResearch === true}
                  onChange={(event) => {
                    const newValue = event.target.checked;
                    replaceCommands(
                      { kind: "planet", id: planet.id },
                      buildPlanetScopeCommands(
                        planet.id,
                        baseProductionQueue,
                        productionQueue,
                        baseContributeOnlyLeftoverToResearch,
                        newValue,
                      ),
                    );
                  }}
                />
                <span>Contribute only leftover resources to research</span>
              </label>
              <div>
                {planet.contributeOnlyLeftoverToResearch ? (
                  <span>Reserved this turn: — (leftover only)</span>
                ) : (
                  <span>
                    Reserved this turn: ≈ {Math.floor(((planet.resources ?? 0) * (basePlayerState?.research?.allocationPercent ?? 0)) / 100)} resources ({basePlayerState?.research?.allocationPercent ?? 0}% of {planet.resources ?? 0})
                  </span>
                )}
              </div>
            </PanelCard>
          )}

          {isOwn && planet.scanLevel === "detailed" && !isStale && (
        <PanelCard variant="surface" className="space-y-3 text-sm">
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
                    buildPlanetScopeCommands(
                      planet.id,
                      baseProductionQueue,
                      [],
                      baseContributeOnlyLeftoverToResearch,
                      planet.contributeOnlyLeftoverToResearch,
                    ),
                  )
                }
              >
                <ListX className="h-3 w-3" />
              </Button>
              <div className="relative">
                <Button
                  size="icon"
                  variant="dashed"
                  aria-label={productionPickerOpen ? "Close production item picker" : "Add production item"}
                  aria-expanded={productionPickerOpen}
                  onClick={() => setProductionPickerOpen((open) => !open)}
                >
                  <Plus className="h-3 w-3" />
                </Button>

                {productionPickerOpen && (
                  <div
                    className="absolute right-full top-1/2 z-10 mr-2 w-44 -translate-y-1/2 rounded-md border border-[var(--color-panel-border)] bg-black/95 p-1.5 shadow-2xl backdrop-blur"
                  >
                    <div className="px-2 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Add To Queue
                    </div>
                    <div className="space-y-1">
                      {productionPickerOptions.map((option) => (
                        <button
                          key={`${option.label}-${option.itemType ?? "none"}-${"designId" in option ? option.designId : ""}`}
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
                              handleAddProductionItem(
                                option.itemType,
                                "targetType" in option ? option.targetType : undefined,
                                "designId" in option ? option.designId : undefined,
                              );
                            }
                          }}
                        >
                          <div className="text-sm text-foreground">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
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
                  <div className="min-w-0">
                    <div className="truncate font-medium text-foreground">
                      {item.itemType === "ship"
                        ? (shipDesigns.find((design) => design.id === item.designId)?.name ?? "Ship")
                        : PRODUCTION_ITEM_LABELS[item.itemType]}
                    </div>
                    <div className="truncate text-[11px] text-muted-foreground">
                      {item.quantity} remaining • {item.progress.resourcesSpent} resources spent
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-muted-foreground">{item.quantity}x</div>
                  <div className="flex items-center gap-0.5">
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Increase ${PRODUCTION_ITEM_LABELS[item.itemType]} quantity`}
                      disabled={item.itemType === "planetary_scanner"}
                      onClick={() => handleAdjustProductionItemQuantity(item.id, 1)}
                    >
                      <Plus className="h-3 w-3" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Decrease ${PRODUCTION_ITEM_LABELS[item.itemType]} quantity`}
                      disabled={item.itemType === "planetary_scanner"}
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
        </PanelCard>
          )}
        </>
      )}
      {showFleetComposer && (
        <FleetComposer
          fleets={ownFleetsInOrbit}
          designs={shipDesigns}
          onClose={() => setShowFleetComposer(false)}
        />
      )}
    </DetailPanelContent>
  );
}
