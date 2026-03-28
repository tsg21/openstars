import { useRef, useEffect, useCallback, useState } from "react";
import type { Galaxy, PlayerState, Selection, Position } from "../types";
import { useViewport } from "../hooks/useViewport";
import type { Viewport } from "../hooks/useViewport";

// ---------------------------------------------------------------------------
// Colour constants (from PRD 08)
// ---------------------------------------------------------------------------
const COLOUR_SELF = "#3b82f6"; // blue
const COLOUR_ENEMY = "#ef4444"; // red
const COLOUR_UNCOLONISED = "#6b7280"; // grey
const COLOUR_ROUTE = "#3b82f6"; // own fleet routes
const COLOUR_SELECTED_ROUTE = "#60a5fa"; // brighter blue for selected fleet

// ---------------------------------------------------------------------------
// Selection / hit-detection constants
// ---------------------------------------------------------------------------

/** Maximum distance (in screen pixels) for a click to "hit" an object. */
const HIT_RADIUS_PX = 12;

/** Radius of the selection highlight ring, relative to planet dot radius. */
const SELECTION_RING_OFFSET = 4;

/** Fleet triangle size (must match rendering). */
const FLEET_ICON_SIZE = 5;

/** Fixed planet dot radius. */
const PLANET_RADIUS = 5;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface GalaxyMapProps {
  galaxy: Galaxy;
  playerState: PlayerState;
  selection: Selection;
  onSelect: (sel: Selection) => void;
  /** Fleet ID currently being edited (own fleet selected). */
  editingFleetId?: string | null;
  /** Edited waypoints for the editing fleet (overrides player state). */
  editedWaypoints?: Position[] | null;
  /** Called when the map is clicked while editing a fleet (galaxy coords). */
  onMapClick?: (pos: Position) => void;
  /** Called to remove a waypoint by index (right-click on marker). */
  onRemoveWaypoint?: (index: number) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Galaxy coords → screen pixel coords. */
function toScreen(
  gx: number,
  gy: number,
  viewport: Viewport,
  canvasW: number,
  canvasH: number,
): { sx: number; sy: number } {
  return {
    sx: (gx - viewport.centreX) * viewport.scale + canvasW / 2,
    sy: (gy - viewport.centreY) * viewport.scale + canvasH / 2,
  };
}

/** Screen coords → galaxy coords (inverse of toScreen). */
function toGalaxy(
  sx: number,
  sy: number,
  viewport: Viewport,
  canvasW: number,
  canvasH: number,
): Position {
  return {
    x: viewport.centreX + (sx - canvasW / 2) / viewport.scale,
    y: viewport.centreY + (sy - canvasH / 2) / viewport.scale,
  };
}

/** Planet colour based on ownership. */
function planetColour(owner: string | null, currentPlayer: string): string {
  if (owner === currentPlayer) return COLOUR_SELF;
  if (owner !== null) return COLOUR_ENEMY;
  return COLOUR_UNCOLONISED;
}

/** Compute the screen-space centre of a fleet's triangle icon. */
function fleetIconCentre(
  sx: number,
  sy: number,
): { fx: number; fy: number } {
  return {
    fx: sx + PLANET_RADIUS + 4,
    fy: sy - PLANET_RADIUS - 2,
  };
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function renderGalaxy(
  ctx: CanvasRenderingContext2D,
  dpr: number,
  canvasW: number,
  canvasH: number,
  galaxy: Galaxy,
  playerState: PlayerState,
  viewport: Viewport,
  selection: Selection,
  editingFleetId: string | null,
  editedWaypoints: Position[] | null,
) {
  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, canvasW, canvasH);

  const toS = (gx: number, gy: number) =>
    toScreen(gx, gy, viewport, canvasW, canvasH);

  // Helper: check if a screen point is roughly visible (with margin)
  const margin = 50;
  const isVisible = (sx: number, sy: number) =>
    sx > -margin &&
    sx < canvasW + margin &&
    sy > -margin &&
    sy < canvasH + margin;

  const selectedFleetId =
    selection?.kind === "fleet" ? selection.id : null;
  const selectedPlanetId =
    selection?.kind === "planet" ? selection.id : null;

  // --- Fleet routes ---
  for (const fleet of playerState.fleets) {
    if (fleet.owner !== playerState.player) continue;

    const isEditing = fleet.id === editingFleetId;
    const waypoints = isEditing && editedWaypoints !== null
      ? editedWaypoints
      : (fleet.waypoints ?? []);
    if (waypoints.length === 0) continue;

    const isSelected = fleet.id === selectedFleetId;

    ctx.strokeStyle = isSelected ? COLOUR_SELECTED_ROUTE : COLOUR_ROUTE;
    ctx.lineWidth = isSelected ? 2 : 1;
    ctx.globalAlpha = isSelected ? 0.9 : 0.5;
    ctx.setLineDash(isSelected ? [] : [4, 4]);
    ctx.beginPath();

    const start = toS(fleet.position.x, fleet.position.y);
    ctx.moveTo(start.sx, start.sy);

    for (const wp of waypoints) {
      const dest = toS(wp.x, wp.y);
      ctx.lineTo(dest.sx, dest.sy);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1.0;
  }

  // --- Waypoint markers ---
  for (const fleet of playerState.fleets) {
    if (fleet.owner !== playerState.player) continue;

    const isEditing = fleet.id === editingFleetId;
    const waypoints = isEditing && editedWaypoints !== null
      ? editedWaypoints
      : (fleet.waypoints ?? []);
    if (waypoints.length === 0) continue;

    const isSelected = fleet.id === selectedFleetId;

    for (let i = 0; i < waypoints.length; i++) {
      const wp = waypoints[i];
      const { sx, sy } = toS(wp.x, wp.y);
      if (!isVisible(sx, sy)) continue;

      const r = 8;
      ctx.beginPath();
      ctx.arc(sx, sy, r, 0, Math.PI * 2);
      ctx.strokeStyle = isSelected ? COLOUR_SELECTED_ROUTE : COLOUR_ROUTE;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = isSelected ? 0.9 : 0.7;
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      ctx.fillStyle = isSelected ? COLOUR_SELECTED_ROUTE : COLOUR_ROUTE;
      ctx.font = "bold 9px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(i + 1), sx, sy);
    }
  }

  // --- Planets ---
  // Build a combined list from galaxy planets + player state ownership
  const planetsToRender = galaxy.planets.map((gp) => {
    const pp = playerState.planets.find((p) => p.id === gp.id);
    return {
      id: gp.id,
      name: gp.name,
      x: gp.x,
      y: gp.y,
      owner: pp?.owner ?? null,
    };
  });

  for (const planet of planetsToRender) {
    const { sx, sy } = toS(planet.x, planet.y);
    if (!isVisible(sx, sy)) continue;

    const colour = planetColour(planet.owner, playerState.player);

    ctx.beginPath();
    ctx.arc(sx, sy, PLANET_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = colour;
    ctx.fill();

    // Planet name label
    ctx.fillStyle = colour;
    ctx.globalAlpha = 0.8;
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(planet.name, sx, sy + PLANET_RADIUS + 4);
    ctx.globalAlpha = 1.0;

    // Selection highlight ring
    if (planet.id === selectedPlanetId) {
      const ringRadius = PLANET_RADIUS + SELECTION_RING_OFFSET;
      ctx.beginPath();
      ctx.arc(sx, sy, ringRadius, 0, Math.PI * 2);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.9;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }
  }

  // --- Fleets (small triangles) ---
  for (const fleet of playerState.fleets) {
    const { sx, sy } = toS(fleet.position.x, fleet.position.y);
    if (!isVisible(sx, sy)) continue;

    const colour =
      fleet.owner === playerState.player ? COLOUR_SELF : COLOUR_ENEMY;

    const { fx, fy } = fleetIconCentre(sx, sy);
    const isSelected = fleet.id === selectedFleetId;

    const size = FLEET_ICON_SIZE;
    ctx.beginPath();
    ctx.moveTo(fx - size, fy - size);
    ctx.lineTo(fx + size, fy);
    ctx.lineTo(fx - size, fy + size);
    ctx.closePath();
    ctx.fillStyle = colour;
    ctx.fill();

    // Selection highlight for fleet
    if (isSelected) {
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.9;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }

    // Fleet ID label
    ctx.fillStyle = colour;
    ctx.globalAlpha = 0.7;
    ctx.font = "9px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(fleet.id, fx + size + 4, fy - 4);
    ctx.globalAlpha = 1.0;
  }

  ctx.restore();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function GalaxyMap({
  galaxy,
  playerState,
  selection,
  onSelect,
  editingFleetId = null,
  editedWaypoints = null,
  onMapClick,
  onRemoveWaypoint,
}: GalaxyMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);
  const mouseDownPosRef = useRef<{ x: number; y: number } | null>(null);

  // Track container size as state
  const [containerSize, setContainerSize] = useState<{
    w: number;
    h: number;
  }>({ w: 0, h: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerSize({
          w: entry.contentRect.width,
          h: entry.contentRect.height,
        });
      }
    });
    observer.observe(container);
    const rect = container.getBoundingClientRect();
    setContainerSize({ w: rect.width, h: rect.height });
    return () => observer.disconnect();
  }, []);

  // Find the player's first owned planet to centre on
  const playerHomePlanetId = playerState.planets.find(
    (p) => p.owner === playerState.player,
  )?.id;

  const [viewport, viewportActions] = useViewport(
    galaxy,
    containerSize.w,
    containerSize.h,
    playerHomePlanetId,
  );

  // Render via requestAnimationFrame
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const w = containerSize.w;
    const h = containerSize.h;

    if (w === 0 || h === 0) return;

    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    canvas.width = w * dpr;
    canvas.height = h * dpr;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    renderGalaxy(
      ctx, dpr, w, h, galaxy, playerState, viewport, selection,
      editingFleetId, editedWaypoints,
    );
  }, [galaxy, playerState, viewport, containerSize, selection, editingFleetId, editedWaypoints]);

  // Re-render on viewport/size changes
  useEffect(() => {
    rafRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(rafRef.current);
  }, [draw]);

  return (
    <div
      ref={containerRef}
      className="relative flex-1 bg-[var(--color-map-bg)] outline-none"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          onSelect(null);
          return;
        }
        viewportActions.onKeyDown(e);
      }}
    >
      <canvas
        ref={canvasRef}
        className={
          viewportActions.isPanning ? "cursor-grabbing" : "cursor-grab"
        }
        onMouseDown={(e) => {
          containerRef.current?.focus();
          if (e.button === 0) {
            mouseDownPosRef.current = { x: e.clientX, y: e.clientY };
          }
          viewportActions.onMouseDown(e);
        }}
        onMouseMove={viewportActions.onMouseMove}
        onMouseUp={(e) => {
          viewportActions.onMouseUp(e);
          const downPos = mouseDownPosRef.current;
          mouseDownPosRef.current = null;
          if (!downPos) return;
          const dx = e.clientX - downPos.x;
          const dy = e.clientY - downPos.y;
          if (dx * dx + dy * dy > 9) return; // drag, not click

          const canvas = canvasRef.current;
          if (!canvas) return;
          const rect = canvas.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const clickY = e.clientY - rect.top;

          const maxDistSq = HIT_RADIUS_PX * HIT_RADIUS_PX;

          // --- Waypoint editing mode ---
          if (editingFleetId && onMapClick) {
            let snappedPos: Position | null = null;

            // Check player-known planets
            for (const planet of playerState.planets) {
              const { sx, sy } = toScreen(
                planet.x, planet.y, viewport, containerSize.w, containerSize.h,
              );
              const distSq =
                (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
              if (distSq < maxDistSq) {
                snappedPos = { x: planet.x, y: planet.y };
                break;
              }
            }

            // Check galaxy planets not in player state
            if (!snappedPos) {
              for (const gp of galaxy.planets) {
                if (playerState.planets.some((pp) => pp.id === gp.id)) continue;
                const { sx, sy } = toScreen(
                  gp.x, gp.y, viewport, containerSize.w, containerSize.h,
                );
                const distSq =
                  (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
                if (distSq < maxDistSq) {
                  snappedPos = { x: gp.x, y: gp.y };
                  break;
                }
              }
            }

            if (snappedPos) {
              onMapClick(snappedPos);
            } else {
              const galaxyPos = toGalaxy(
                clickX, clickY, viewport, containerSize.w, containerSize.h,
              );
              onMapClick(galaxyPos);
            }
            return;
          }

          // --- Normal selection mode ---
          const candidates: { sel: Selection; distSq: number }[] = [];

          // Fleet hit detection
          for (const fleet of playerState.fleets) {
            const { sx, sy } = toScreen(
              fleet.position.x, fleet.position.y,
              viewport, containerSize.w, containerSize.h,
            );
            const { fx, fy } = fleetIconCentre(sx, sy);
            const distSq =
              (clickX - fx) * (clickX - fx) + (clickY - fy) * (clickY - fy);
            if (distSq < maxDistSq) {
              candidates.push({
                sel: { kind: "fleet", id: fleet.id },
                distSq,
              });
            }
          }

          // Planet hit detection
          for (const planet of playerState.planets) {
            const { sx, sy } = toScreen(
              planet.x, planet.y, viewport, containerSize.w, containerSize.h,
            );
            const distSq =
              (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
            if (distSq < maxDistSq) {
              candidates.push({
                sel: { kind: "planet", id: planet.id },
                distSq,
              });
            }
          }

          // Galaxy-only planets
          for (const gp of galaxy.planets) {
            if (playerState.planets.some((pp) => pp.id === gp.id)) continue;
            const { sx, sy } = toScreen(
              gp.x, gp.y, viewport, containerSize.w, containerSize.h,
            );
            const distSq =
              (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
            if (distSq < maxDistSq) {
              candidates.push({
                sel: { kind: "planet", id: gp.id },
                distSq,
              });
            }
          }

          if (candidates.length === 0) {
            onSelect(null);
            return;
          }

          // Cycle through overlapping objects
          if (candidates.length > 1 && selection !== null) {
            const currentIdx = candidates.findIndex(
              (c) =>
                c.sel?.kind === selection.kind &&
                c.sel?.id === selection.id,
            );
            if (currentIdx !== -1) {
              const nextIdx = (currentIdx + 1) % candidates.length;
              onSelect(candidates[nextIdx].sel);
              return;
            }
          }

          candidates.sort((a, b) => a.distSq - b.distSq);
          onSelect(candidates[0].sel);
        }}
        onContextMenu={(e) => {
          if (!editingFleetId || !onRemoveWaypoint || !editedWaypoints) return;

          const canvas = canvasRef.current;
          if (!canvas) return;
          const rect = canvas.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const clickY = e.clientY - rect.top;
          const maxDistSq = HIT_RADIUS_PX * HIT_RADIUS_PX;

          for (let i = 0; i < editedWaypoints.length; i++) {
            const wp = editedWaypoints[i];
            const { sx, sy } = toScreen(
              wp.x, wp.y, viewport, containerSize.w, containerSize.h,
            );
            const distSq =
              (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
            if (distSq < maxDistSq) {
              e.preventDefault();
              onRemoveWaypoint(i);
              return;
            }
          }
        }}
        onMouseLeave={(e) => {
          viewportActions.onMouseUp(e);
          mouseDownPosRef.current = null;
        }}
      />
    </div>
  );
}
