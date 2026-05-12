import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
} from "../../types";
import { LIGHT_YEAR } from "../../types";
import { cn } from "../../lib/utils";
import { useGameCommands } from "../../hooks/useGameCommands";
import { Button } from "../ui/Button";
import { MutedText } from "../ui/MutedText";
import { TransportTaskEditor, TransferTaskEditor } from "./WaypointTaskEditor";
import { DetailPanelCard, DetailPanelContent, DetailPanelHeading } from "../ui/DetailPanelLayout";
import { ResourceBars } from "../ui/ResourceBars";
import { FleetComposer } from "./FleetComposer";
import { validateTransportOrders, validateTransferTask } from "../../lib/waypointValidation";

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

function distanceLightYears(a: Position, b: Position): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy) / LIGHT_YEAR;
}

function estimatedTurns(distLy: number, warp: number): number {
  const w = Math.max(1, Math.min(10, warp));
  const budget = w * w;
  return Math.ceil(distLy / budget);
}

function bearingToCompass(bearing: number): string {
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(bearing / 45) % 8;
  return directions[index];
}

function getTotalCargo(cargo: Cargo): number {
  return cargo.ironium + cargo.boranium + cargo.germanium + cargo.colonists;
}

function getFleetDisplayName(fleet: Pick<PlayerFleet, "name" | "id">): string {
  return fleet.name?.trim() || fleet.id;
}

function computeWaypointValidationErrors(
  waypoints: Waypoint[] | null,
): Record<string, string> {
  if (!waypoints) {
    return {};
  }

  const errors: Record<string, string> = {};
  waypoints.forEach((wp, i) => {
    if (!wp.task) return;
    let taskErrors: Record<string, string> = {};
    if (wp.task.type === "transport") {
      taskErrors = validateTransportOrders(wp.task.orders);
    } else if (wp.task.type === "transfer") {
      taskErrors = validateTransferTask(wp.task.fleetId ?? null, wp.task.orders);
    }
    for (const [key, msg] of Object.entries(taskErrors)) {
      errors[`waypoint-${i}-${key}`] = msg;
    }
  });

  return errors;
}

function FuelBar({ fuel, fuelCapacity }: { fuel: number; fuelCapacity: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const fuelFillColour = getComputedStyle(document.documentElement)
      .getPropertyValue("--color-fuel-bar-fill")
      .trim();

    const dpr = window.devicePixelRatio ?? 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, W, H);

    const labelW = 72;
    const valueW = 88;
    const barX = labelW;
    const barW = W - labelW - valueW - 4;
    const barH = 10;
    const y = H / 2;

    ctx.font = "11px ui-monospace, monospace";
    ctx.fillStyle = "#9ca3af";
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";
    ctx.fillText("Fuel", 0, y);

    const trackY = y - barH / 2;
    ctx.fillStyle = "#1f2937";
    ctx.beginPath();
    ctx.roundRect(barX, trackY, barW, barH, 2);
    ctx.fill();

    const fillW = fuelCapacity > 0 ? Math.round((fuel / fuelCapacity) * barW) : 0;
    if (fillW > 0) {
      ctx.fillStyle = fuelFillColour;
      ctx.beginPath();
      ctx.roundRect(barX, trackY, fillW, barH, 2);
      ctx.fill();
    }

    ctx.fillStyle = "#f9fafb";
    ctx.textAlign = "right";
    ctx.fillText(`${fuel.toLocaleString()} / ${fuelCapacity.toLocaleString()} mg`, W, y);
  }, [fuel, fuelCapacity]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full"
      style={{ height: 22 }}
      role="img"
      aria-label="Fuel bar"
    />
  );
}

export interface WaypointEditorState {
  waypointEditMode: boolean;
  editingFleetId: string | null;
  editedWaypoints: Waypoint[] | null;
  onEnterWaypointMode?: () => void;
  onExitWaypointMode?: () => void;
  onAddWaypoint?: (pos: Position) => void;
  onRemoveWaypoint?: (index: number) => void;
}

export interface FleetDetailProps {
  fleet: PlayerFleet;
  currentPlayer: string;
  designs: Design[];
  knownPlanets: Array<GalaxyPlanet | PlayerPlanet>;
  onWaypointEditorStateChange?: (state: WaypointEditorState) => void;
  ownFleets: PlayerFleet[];
}

export function FleetDetail({
  fleet,
  currentPlayer,
  designs,
  knownPlanets,
  onWaypointEditorStateChange,
  ownFleets,
}: FleetDetailProps) {
  const { addCommand } = useGameCommands();
  const [activeTaskPopover, setActiveTaskPopover] = useState<number | null>(null);
  const [waypointEditMode, setWaypointEditMode] = useState(false);
  const [editedWaypoints, setEditedWaypoints] = useState<Waypoint[] | null>(null);
  const [editRepeat, setEditRepeat] = useState(false);
  const [showFleetComposer, setShowFleetComposer] = useState(false);

  const isOwn = fleet.owner === currentPlayer;
  const cargo = fleet.cargo ?? {
    ironium: 0,
    boranium: 0,
    germanium: 0,
    colonists: 0,
  };
  const showCargo = isOwn && (fleet.cargoCapacity ?? 0) > 0;
  const showFuel = isOwn && fleet.fuelCapacity != null && fleet.fuelCapacity > 0;
  const usedCapacity = getTotalCargo(cargo);

  const colocatedOwnFleets = ownFleets.filter(
    (candidate) =>
      candidate.position.x === fleet.position.x &&
      candidate.position.y === fleet.position.y,
  );

  const composition = (fleet.composition ?? []).map((c) => {
    const design = designs.find((d) => d.id === c.designId);
    return {
      name: design?.name ?? c.designId,
      count: c.count,
    };
  });

  const waypointValidationErrors = useMemo(
    () => (waypointEditMode ? computeWaypointValidationErrors(editedWaypoints) : {}),
    [editedWaypoints, waypointEditMode],
  );

  const handleEnterWaypointMode = useCallback(() => {
    if (!isOwn) {
      return;
    }

    setWaypointEditMode(true);
    setEditedWaypoints(fleet.waypoints ?? []);
    setEditRepeat(fleet.repeat ?? false);
  }, [fleet.repeat, fleet.waypoints, isOwn]);

  const handleCancelWaypointMode = useCallback(() => {
    setWaypointEditMode(false);
    setEditedWaypoints(null);
    setEditRepeat(false);
    setActiveTaskPopover(null);
  }, []);

  const handleAddWaypoint = useCallback((pos: Position) => {
    setEditedWaypoints((prev) =>
      prev
        ? [...prev, { x: pos.x, y: pos.y, warp: 5, task: null }]
        : [{ x: pos.x, y: pos.y, warp: 5, task: null }],
    );
  }, []);

  const handleRemoveWaypoint = useCallback((index: number) => {
    setEditedWaypoints((prev) =>
      prev ? prev.filter((_, i) => i !== index) : null,
    );
  }, []);

  const handleClearAllWaypoints = useCallback(() => {
    setEditedWaypoints([]);
  }, []);

  const handleToggleRepeat = useCallback(() => {
    setEditRepeat((value) => !value);
  }, []);

  const handleUpdateWaypointTask = useCallback((index: number, task: WaypointTask | null) => {
    setEditedWaypoints((prev) =>
      prev ? prev.map((wp, i) => (i === index ? { ...wp, task } : wp)) : null,
    );
  }, []);

  const handleUpdateWaypointWarp = useCallback((index: number, warpInput: string) => {
    const parsedWarp = Number(warpInput);
    if (!Number.isFinite(parsedWarp)) {
      return;
    }

    const clampedWarp = Math.max(1, Math.min(10, Math.trunc(parsedWarp)));
    setEditedWaypoints((prev) =>
      prev
        ? prev.map((wp, i) => (i === index ? { ...wp, warp: clampedWarp } : wp))
        : null,
    );
  }, []);

  const handleSaveWaypoints = useCallback(() => {
    if (editedWaypoints === null) {
      handleCancelWaypointMode();
      return;
    }

    const errors = computeWaypointValidationErrors(editedWaypoints);
    if (Object.keys(errors).length > 0) {
      return;
    }

    const originalWaypoints = fleet.waypoints ?? [];
    const hasChanged =
      editRepeat !== (fleet.repeat ?? false) ||
      editedWaypoints.length !== originalWaypoints.length ||
      editedWaypoints.some(
        (wp, i) =>
          wp.x !== originalWaypoints[i]?.x ||
          wp.y !== originalWaypoints[i]?.y ||
          wp.warp !== originalWaypoints[i]?.warp ||
          JSON.stringify(wp.task) !== JSON.stringify(originalWaypoints[i]?.task),
      );

    if (hasChanged) {
      addCommand({
        type: "set_waypoints",
        fleetId: fleet.id,
        waypoints: editedWaypoints,
        repeat: editRepeat,
      });
    }

    handleCancelWaypointMode();
  }, [addCommand, editedWaypoints, editRepeat, fleet.id, fleet.repeat, fleet.waypoints, handleCancelWaypointMode]);

  useEffect(() => {
    if (!onWaypointEditorStateChange) {
      return;
    }

    onWaypointEditorStateChange({
      waypointEditMode,
      editingFleetId: waypointEditMode ? fleet.id : null,
      editedWaypoints: waypointEditMode ? editedWaypoints : null,
      onEnterWaypointMode: handleEnterWaypointMode,
      onExitWaypointMode: handleCancelWaypointMode,
      onAddWaypoint: waypointEditMode ? handleAddWaypoint : undefined,
      onRemoveWaypoint: waypointEditMode ? handleRemoveWaypoint : undefined,
    });

    return () => {
      onWaypointEditorStateChange({
        waypointEditMode: false,
        editingFleetId: null,
        editedWaypoints: null,
      });
    };
  }, [
    editedWaypoints,
    fleet.id,
    handleAddWaypoint,
    handleCancelWaypointMode,
    handleEnterWaypointMode,
    handleRemoveWaypoint,
    onWaypointEditorStateChange,
    waypointEditMode,
  ]);

  const getWaypointLabel = (waypoint: Waypoint): string => {
    const matchingPlanet = knownPlanets.find(
      (planet) => planet.x === waypoint.x && planet.y === waypoint.y,
    );

    if (matchingPlanet) {
      return matchingPlanet.name;
    }

    return `(${Math.round(waypoint.x / LIGHT_YEAR)}, ${Math.round(waypoint.y / LIGHT_YEAR)})`;
  };

  const waypoints = waypointEditMode && editedWaypoints !== null ? editedWaypoints : fleet.waypoints ?? [];
  const waypointInfo: {
    waypoint: Waypoint;
    distLy: number;
    legTurns: number;
    cumulativeTurns: number;
  }[] = [];
  let prevPos: Position = fleet.position;
  let totalTurns = 0;

  for (const wp of waypoints) {
    const distLy = distanceLightYears(prevPos, wp);
    const legTurns = estimatedTurns(distLy, wp.warp ?? 5);
    totalTurns += legTurns;
    waypointInfo.push({
      waypoint: wp,
      distLy,
      legTurns,
      cumulativeTurns: totalTurns,
    });
    prevPos = wp;
  }

  return (
    <DetailPanelContent>
      {isOwn ? (
        <div className="flex items-start justify-between gap-3">
          <DetailPanelHeading title={`Fleet ID: ${fleet.id}`}>
            {getFleetDisplayName(fleet)}
          </DetailPanelHeading>
          <div className="flex shrink-0 gap-2">
            <Button
              onClick={() => setShowFleetComposer(true)}
              variant="secondary"
              size="xs"
            >
              Manage Fleets
            </Button>
          </div>
        </div>
      ) : (
        <DetailPanelHeading>Enemy Fleet</DetailPanelHeading>
      )}

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

        {showFuel && (
          <DetailPanelCard className="space-y-2">
            <FuelBar
              fuel={fleet.fuel ?? 0}
              fuelCapacity={fleet.fuelCapacity ?? 0}
            />
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
                  onChange={waypointEditMode ? handleToggleRepeat : undefined}
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
                      {waypointEditMode ? (
                        <input
                          type="number"
                          min={1}
                          max={10}
                          value={wp.waypoint.warp ?? 5}
                          onChange={(e) => handleUpdateWaypointWarp(i, e.target.value)}
                          className="w-10 rounded border border-neutral-700 bg-black/30 px-1 text-center text-xs text-foreground"
                          aria-label={`Warp for waypoint ${i + 1}`}
                        />
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          W{wp.waypoint.warp ?? 5}
                        </span>
                      )}
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
                            onClick={() => handleRemoveWaypoint(i)}
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
                                  handleUpdateWaypointTask(i, null);
                                  return;
                                }

                                if (type !== wp.waypoint.task?.type) {
                                  handleUpdateWaypointTask(i, { type, orders: [] });
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
                              handleUpdateWaypointTask(i, { type: "transport", orders })
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
                              handleUpdateWaypointTask(i, {
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
                  onClick={handleEnterWaypointMode}
                  variant="action"
                fullWidth
                  className="transition-all hover:-translate-y-px"
                >
                  Edit Waypoints
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                    onClick={handleClearAllWaypoints}
                    variant="secondary"
                    fullWidth
                  >
                    Clear Waypoints
                  </Button>
                  <Button
                    onClick={handleSaveWaypoints}
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
        {showFleetComposer && (
          <FleetComposer
            fleets={colocatedOwnFleets}
            designs={designs}
            onClose={() => setShowFleetComposer(false)}
          />
        )}
      </div>
    </DetailPanelContent>
  );
}
