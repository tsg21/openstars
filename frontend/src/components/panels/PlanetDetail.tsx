import { useEffect, useMemo, useRef, useState } from "react";
import { X } from "lucide-react";
import type {
  DesignSummary,
  Habitability,
  PlayerFleet,
  PlayerPlanet,
} from "../../types";
import { useGameCommands } from "../../hooks/useGameCommands";
import { fetchPlanetImageManifest, getPlanetImageUrl, type PlanetImageManifest } from "../../lib/planetImages";
import { buildPlanetScopeCommands } from "../../lib/productionQueueCommands";
import { summariseQueue } from "../../lib/productionSummary";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { MutedText } from "../ui/MutedText";
import { SectionLabel } from "../ui/SectionLabel";
import { DetailPanelContent, DetailPanelHeading } from "../ui/DetailPanelLayout";
import { PanelCard } from "../ui/PanelCard";
import { ResourceBars } from "../ui/ResourceBars";
import { FleetComposer } from "./FleetComposer";


const JOAT_HAB_LOW = 15;
const JOAT_HAB_HIGH = 85;

const HAB_CONFIG = [
  { key: "gravity" as const, label: "Gravity", color: "#3b82f6" },
  { key: "temperature" as const, label: "Temperature", color: "#dc2626" },
  { key: "radiation" as const, label: "Radiation", color: "#16a34a" },
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

export interface PlanetDetailProps {
  planet: PlayerPlanet;
  currentPlayer: string;
  fleetsInOrbit: PlayerFleet[];
  onSelectFleet: (fleetId: string) => void;
  shipDesigns: DesignSummary[];
  onOpenProduction?: (planetId: string) => void;
}

export function PlanetDetail({
  planet,
  currentPlayer,
  fleetsInOrbit,
  onSelectFleet,
  shipDesigns,
  onOpenProduction,
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
    planet.productionQueue != null &&
    basePlayerState?.research != null;

  const [manifest, setManifest] = useState<PlanetImageManifest | null>(null);
  const [populationDialogOpen, setPopulationDialogOpen] = useState(false);
  const [showOrbitFleetList, setShowOrbitFleetList] = useState(false);
  const [showFleetComposer, setShowFleetComposer] = useState(false);

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

  const starbase = planet.starbase;
  const isStarbasePresent = starbase != null && (starbase as { present?: boolean }).present !== false;
  const starbaseType = starbase && "type" in starbase ? starbase.type : null;
  const starbaseCanBuildShips = starbase && "canBuildShips" in starbase ? starbase.canBuildShips : null;

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
            <MutedText className="block text-xs">
              {totalShips > 0 ? `${totalShips} ship${totalShips !== 1 ? "s" : ""}` : "No ship data"}
            </MutedText>
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
            <SectionLabel>Fleets in Orbit</SectionLabel>
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
            <SectionLabel>Planet</SectionLabel>
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
              <SectionLabel>Starbase</SectionLabel>
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
              <SectionLabel>Research</SectionLabel>
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

          {planet.productionQueue != null && (
            <PanelCard variant="surface" className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <SectionLabel>Production</SectionLabel>
                <Button size="xs" variant="ghost" onClick={() => onOpenProduction?.(planet.id)}>
                  Manage →
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">
                {summariseQueue(planet.productionQueue, shipDesigns)}
              </div>
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
