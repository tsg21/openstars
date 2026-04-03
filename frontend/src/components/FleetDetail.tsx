import { useState } from "react";
import { Trash2 } from "lucide-react";
import type {
  Cargo,
  Design,
  GalaxyPlanet,
  PlayerFleet,
  PlayerPlanet,
  Position,
  Waypoint,
  WaypointTask,
} from "../types";
import { PARSEC } from "../types";
import { cn } from "../lib/utils";
import { Button } from "./Button";
import { MutedText } from "./MutedText";
import { TransportTaskEditor, TransferTaskEditor } from "./WaypointTaskEditor";
import { DetailPanelCard, DetailPanelContent, DetailPanelHeading } from "./DetailPanelLayout";
import { ResourceBars } from "./ResourceBars";

const TASK_LABELS: Record<WaypointTask["type"], string> = {
  transport: "Transport",
  transfer: "Transfer",
  colonise: "Colonise",
};

const TASK_CHIP_CLASS: Record<WaypointTask["type"], string> = {
  transport: "bg-blue-900/50 text-blue-300 border border-blue-700/50",
  transfer: "bg-amber-900/50 text-amber-300 border border-amber-700/50",
  colonise: "bg-emerald-900/50 text-emerald-300 border border-emerald-700/50",
};

function distanceParsecs(a: Position, b: Position): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy) / PARSEC;
}

function estimatedTurns(distPc: number, speed: number): number {
  if (speed <= 0) return Infinity;
  return Math.ceil(distPc / speed);
}

function bearingToCompass(bearing: number): string {
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(bearing / 45) % 8;
  return directions[index];
}

function getTotalCargo(cargo: Cargo): number {
  return cargo.ironium + cargo.boranium + cargo.germanium + cargo.colonists;
}

export interface FleetDetailProps {
  fleet: PlayerFleet;
  currentPlayer: string;
  designs: Design[];
  knownPlanets: Array<GalaxyPlanet | PlayerPlanet>;
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
}

export function FleetDetail({
  fleet,
  currentPlayer,
  designs,
  knownPlanets,
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
}: FleetDetailProps) {
  const [activeTaskPopover, setActiveTaskPopover] = useState<number | null>(null);

  const isOwn = fleet.owner === currentPlayer;
  const cargo = fleet.cargo ?? {
    ironium: 0,
    boranium: 0,
    germanium: 0,
    colonists: 0,
  };
  const showCargo = isOwn && (fleet.cargoCapacity ?? 0) > 0;
  const usedCapacity = getTotalCargo(cargo);

  const composition = (fleet.composition ?? []).map((c) => {
    const design = designs.find((d) => d.id === c.designId);
    return {
      name: design?.name ?? c.designId,
      count: c.count,
      speed: design?.speed ?? 0,
    };
  });

  const effectiveSpeed = composition.length > 0 ? Math.min(...composition.map((c) => c.speed)) : 0;
  const getWaypointLabel = (waypoint: Waypoint): string => {
    const matchingPlanet = knownPlanets.find(
      (planet) => planet.x === waypoint.x && planet.y === waypoint.y,
    );

    if (matchingPlanet) {
      return matchingPlanet.name;
    }

    return `(${Math.round(waypoint.x / PARSEC)}, ${Math.round(waypoint.y / PARSEC)})`;
  };

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
            <span className="font-semibold text-foreground">{effectiveSpeed} pc/turn</span>
          </DetailPanelCard>
        )}

        {showCargo && (
          <DetailPanelCard className="space-y-2">
            <div className="flex items-center justify-between">
              <MutedText>Cargo:</MutedText>
              <span className="text-xs text-muted-foreground">
                {usedCapacity.toLocaleString()} / {(fleet.cargoCapacity ?? 0).toLocaleString()} used
              </span>
            </div>
            <ResourceBars
              minerals={{
                ironium: cargo.ironium,
                boranium: cargo.boranium,
                germanium: cargo.germanium,
              }}
              colonists={cargo.colonists}
              maxValue={fleet.cargoCapacity}
            />
          </DetailPanelCard>
        )}

        {isOwn && (
          <DetailPanelCard>
            <div className="flex items-center justify-between">
              <MutedText>Waypoints:</MutedText>
              <label className="flex cursor-pointer select-none items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={waypointEditMode ? editRepeat : Boolean(fleet.repeat)}
                  onChange={waypointEditMode ? onToggleRepeat : undefined}
                  disabled={!waypointEditMode}
                  className="rounded"
                />
                <span>Repeat route</span>
              </label>
            </div>
            {waypointInfo.length > 0 ? (
              <ol className="mt-3 space-y-2 pl-3">
                {waypointInfo.map((wp, i) => (
                  <li key={i} className="relative space-y-1">
                    <div className="flex items-center justify-between gap-2 text-foreground">
                      <span className="flex-1 font-mono text-xs">
                        {getWaypointLabel(wp.waypoint)}
                      </span>
                      <MutedText className="text-xs">
                        ~{wp.cumulativeTurns} turn{wp.cumulativeTurns !== 1 ? "s" : ""}
                      </MutedText>
                      {waypointEditMode ? (
                        <button
                          type="button"
                          onClick={() =>
                            setActiveTaskPopover((prev) => (prev === i ? null : i))
                          }
                          className={cn(
                            "rounded px-1.5 py-0.5 text-xs font-medium transition-colors",
                            wp.waypoint.task
                              ? TASK_CHIP_CLASS[wp.waypoint.task.type]
                              : "border border-neutral-700 bg-neutral-800 text-muted-foreground hover:bg-neutral-700",
                          )}
                        >
                          {wp.waypoint.task ? TASK_LABELS[wp.waypoint.task.type] : "No task"}
                        </button>
                      ) : wp.waypoint.task ? (
                        <span className={cn("rounded px-1.5 py-0.5 text-xs font-medium", TASK_CHIP_CLASS[wp.waypoint.task.type])}>
                          {TASK_LABELS[wp.waypoint.task.type]}
                        </span>
                      ) : (
                        <span className="rounded border border-neutral-700 bg-neutral-800 px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
                          No task
                        </span>
                      )}
                      <div className="flex w-6 justify-end">
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
                      </div>
                    </div>
                    {waypointEditMode && activeTaskPopover === i && (
                      <div
                        role="dialog"
                        aria-label="Waypoint task type"
                        className="absolute right-7 top-7 z-20 min-w-32 rounded-md border border-white/15 bg-black/90 p-1.5 shadow-[0_10px_30px_rgba(0,0,0,0.4)] backdrop-blur-sm"
                      >
                        <div className="flex flex-col gap-1">
                          {(["none", "transport", "transfer", "colonise"] as const).map((type) => (
                            <button
                              key={type}
                              type="button"
                              onClick={() => {
                                setActiveTaskPopover(null);

                                if (type === "none") {
                                  onUpdateWaypointTask(i, null);
                                  return;
                                }

                                if (type !== wp.waypoint.task?.type) {
                                  onUpdateWaypointTask(i, { type, orders: [] });
                                }
                              }}
                              className={cn(
                                "rounded border px-2 py-1 text-left text-xs font-medium capitalize transition-colors",
                                type === "none" && !wp.waypoint.task
                                  ? "border-neutral-500 bg-neutral-700 text-foreground"
                                  : type === wp.waypoint.task?.type
                                    ? type === "transport"
                                      ? "border-blue-600 bg-blue-800 text-blue-200"
                                      : type === "transfer"
                                        ? "border-amber-600 bg-amber-800 text-amber-200"
                                        : "border-emerald-600 bg-emerald-800 text-emerald-200"
                                    : "border-neutral-700 bg-neutral-800 text-muted-foreground hover:bg-neutral-700 hover:text-foreground",
                              )}
                            >
                              {type}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {(wp.waypoint.task?.type === "transport" ||
                      wp.waypoint.task?.type === "transfer") && (
                      <div className="ml-4 space-y-2 rounded border border-[var(--color-panel-border)] bg-black/20 p-2 text-xs">
                        {wp.waypoint.task?.type === "transport" && (
                          <TransportTaskEditor
                            orders={wp.waypoint.task.orders}
                            onChange={(orders) =>
                              onUpdateWaypointTask(i, { type: "transport", orders })
                            }
                            disabled={!waypointEditMode}
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
                            disabled={!waypointEditMode}
                            validationErrors={Object.fromEntries(
                              Object.entries(waypointValidationErrors)
                                .filter(([k]) => k.startsWith(`waypoint-${i}-`))
                                .map(([k, v]) => [k.replace(`waypoint-${i}-`, ""), v]),
                            )}
                          />
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ol>
            ) : (
              <div className="mt-3 text-muted-foreground italic">Stationary</div>
            )}
            <div className="mt-3 space-y-2">
              {waypointEditMode && (
                <>
                  <div className="rounded border border-blue-900/50 bg-blue-950/30 px-2 py-1.5 text-xs text-muted-foreground">
                    Click the map to add waypoints
                  </div>
                </>
              )}
              {!waypointEditMode ? (
                <Button
                  onClick={onEnterWaypointMode}
                  variant="action"
                fullWidth
                  className="transition-all hover:-translate-y-px"
                >
                  Edit Waypoints
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                    onClick={onClearAllWaypoints}
                    variant="secondary"
                    fullWidth
                  >
                    Clear Waypoints
                  </Button>
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
            </div>
          </DetailPanelCard>
        )}
      </div>
    </DetailPanelContent>
  );
}
