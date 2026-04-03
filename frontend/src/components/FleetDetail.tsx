import { useState } from "react";
import { RefreshCw, Trash2 } from "lucide-react";
import type { Design, PlayerFleet, Position, Waypoint, WaypointTask } from "../types";
import { PARSEC } from "../types";
import { cn } from "../lib/utils";
import { Button } from "./Button";
import { MutedText } from "./MutedText";
import { TransportTaskEditor, TransferTaskEditor } from "./WaypointTaskEditor";
import { DetailPanelCard, DetailPanelContent, DetailPanelHeading } from "./DetailPanelLayout";

const CIRCLED_NUMBERS = [
  "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
  "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳",
];

const TASK_LABELS: Record<WaypointTask["type"], string> = {
  transport: "Transport",
  transfer: "Transfer",
};

const TASK_CHIP_CLASS: Record<WaypointTask["type"], string> = {
  transport: "bg-blue-900/50 text-blue-300 border border-blue-700/50",
  transfer: "bg-amber-900/50 text-amber-300 border border-amber-700/50",
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

export interface FleetDetailProps {
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
}

export function FleetDetail({
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
}: FleetDetailProps) {
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
            <span className="font-semibold text-foreground">{effectiveSpeed} pc/turn</span>
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
                  <div className="flex items-center justify-between gap-2 text-foreground">
                    <span className="flex-1 font-mono text-xs">
                      {CIRCLED_NUMBERS[i] ?? `(${i + 1})`} ({Math.round(wp.waypoint.x / PARSEC)},{" "}
                      {Math.round(wp.waypoint.y / PARSEC)})
                    </span>
                    {wp.waypoint.task ? (
                      <span className={cn("rounded px-1.5 py-0.5 text-xs font-medium", TASK_CHIP_CLASS[wp.waypoint.task.type])}>
                        {TASK_LABELS[wp.waypoint.task.type]}
                      </span>
                    ) : (
                      <span className="rounded border border-neutral-700 bg-neutral-800 px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
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
                    <div className="ml-4 space-y-2 rounded border border-[var(--color-panel-border)] bg-black/20 p-2 text-xs">
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
                              "rounded border px-2 py-0.5 font-medium capitalize",
                              type === "none" && !wp.waypoint.task
                                ? "border-neutral-500 bg-neutral-700 text-foreground"
                                : type === wp.waypoint.task?.type
                                  ? type === "transport"
                                    ? "border-blue-600 bg-blue-800 text-blue-200"
                                    : "border-amber-600 bg-amber-800 text-amber-200"
                                  : "border-neutral-700 bg-neutral-800 text-muted-foreground hover:bg-neutral-700",
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
                className="transition-all hover:-translate-y-px"
              >
                Edit Waypoints
              </Button>
            ) : (
              <div className="space-y-2">
                <label className="flex cursor-pointer select-none items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editRepeat}
                    onChange={onToggleRepeat}
                    className="rounded"
                  />
                  <span>Repeat route</span>
                </label>
                <div className="rounded border border-blue-900/50 bg-blue-950/30 px-2 py-1.5 text-xs text-muted-foreground">
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
    </DetailPanelContent>
  );
}
