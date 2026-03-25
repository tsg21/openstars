import { useRef, useEffect, useCallback, useState } from "react";
import type { Galaxy, PlayerState } from "../types";
import { PARSEC } from "../types";
import { useViewport } from "../hooks/useViewport";
import type { Viewport } from "../hooks/useViewport";
import { Home } from "lucide-react";

// ---------------------------------------------------------------------------
// Colour constants (from PRD 08)
// ---------------------------------------------------------------------------
const COLOUR_SELF = "#3b82f6"; // blue
const COLOUR_ENEMY = "#ef4444"; // red
const COLOUR_UNCOLONISED = "#6b7280"; // grey
const COLOUR_ROUTE = "#3b82f6"; // own fleet routes

// ---------------------------------------------------------------------------
// Detail-level thresholds
// ---------------------------------------------------------------------------

type DetailLevel = "far" | "medium" | "close";

/**
 * Determine detail level from viewport scale.
 *
 * We measure "parsecs visible across 1000px" as a proxy for zoom level.
 */
function getDetailLevel(scale: number): DetailLevel {
  const parsecsPerThousandPx = 1000 / (scale * PARSEC);
  if (parsecsPerThousandPx > 300) return "far";
  if (parsecsPerThousandPx > 80) return "medium";
  return "close";
}

// ---------------------------------------------------------------------------
// Selection constants
// ---------------------------------------------------------------------------

/** Maximum distance (in screen pixels) for a click to "hit" a planet. */
const HIT_RADIUS_PX = 12;

/** Radius of the selection highlight ring, relative to planet dot radius. */
const SELECTION_RING_OFFSET = 4;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface GalaxyMapProps {
  galaxy: Galaxy;
  playerState: PlayerState;
  selectedPlanetId: string | null;
  onSelectPlanet: (id: string | null) => void;
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

/** Planet colour based on ownership. */
function planetColour(owner: string | null, currentPlayer: string): string {
  if (owner === currentPlayer) return COLOUR_SELF;
  if (owner !== null) return COLOUR_ENEMY;
  return COLOUR_UNCOLONISED;
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
  selectedPlanetId: string | null,
) {
  const detail = getDetailLevel(viewport.scale);

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

  // --- Fleet routes (draw before fleets/planets so they're behind) ---
  if (detail !== "far") {
    for (const fleet of playerState.fleets) {
      if (fleet.owner !== playerState.player) continue;
      if (!fleet.waypoints || fleet.waypoints.length === 0) continue;

      ctx.strokeStyle = COLOUR_ROUTE;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();

      const start = toS(fleet.position.x, fleet.position.y);
      ctx.moveTo(start.sx, start.sy);

      for (const wp of fleet.waypoints) {
        const dest = toS(wp.x, wp.y);
        ctx.lineTo(dest.sx, dest.sy);
      }
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1.0;
    }
  }

  // --- Waypoint markers (close zoom only) ---
  if (detail === "close") {
    for (const fleet of playerState.fleets) {
      if (fleet.owner !== playerState.player) continue;
      if (!fleet.waypoints || fleet.waypoints.length === 0) continue;

      for (let i = 0; i < fleet.waypoints.length; i++) {
        const wp = fleet.waypoints[i];
        const { sx, sy } = toS(wp.x, wp.y);
        if (!isVisible(sx, sy)) continue;

        const r = 8;
        ctx.beginPath();
        ctx.arc(sx, sy, r, 0, Math.PI * 2);
        ctx.strokeStyle = COLOUR_ROUTE;
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.7;
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        ctx.fillStyle = COLOUR_ROUTE;
        ctx.font = "bold 9px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(i + 1), sx, sy);
      }
    }
  }

  // --- Planets ---
  const basePlanetRadius = Math.max(3, 5 * viewport.scale * PARSEC * 0.02);
  const clampedRadius = Math.min(Math.max(basePlanetRadius, 3), 8);

  // Use galaxy planets for far view (shows all), player planets for others
  const planetsToRender =
    detail === "far"
      ? galaxy.planets.map((gp) => {
          const pp = playerState.planets.find((p) => p.id === gp.id);
          return {
            id: gp.id,
            name: gp.name,
            x: gp.x,
            y: gp.y,
            owner: pp?.owner ?? null,
          };
        })
      : playerState.planets;

  for (const planet of planetsToRender) {
    const { sx, sy } = toS(planet.x, planet.y);
    if (!isVisible(sx, sy)) continue;

    const colour = planetColour(planet.owner, playerState.player);

    ctx.beginPath();
    ctx.arc(sx, sy, clampedRadius, 0, Math.PI * 2);
    ctx.fillStyle = colour;
    ctx.fill();

    // Planet name label (medium and close only)
    if (detail !== "far") {
      ctx.fillStyle = colour;
      ctx.globalAlpha = 0.8;
      ctx.font = "10px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(planet.name, sx, sy + clampedRadius + 4);
      ctx.globalAlpha = 1.0;
    }

    // Selection highlight ring
    if (planet.id === selectedPlanetId) {
      const ringRadius = clampedRadius + SELECTION_RING_OFFSET;
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
  if (detail !== "far") {
    for (const fleet of playerState.fleets) {
      const { sx, sy } = toS(fleet.position.x, fleet.position.y);
      if (!isVisible(sx, sy)) continue;

      const colour =
        fleet.owner === playerState.player ? COLOUR_SELF : COLOUR_ENEMY;

      const offsetX = sx + clampedRadius + 4;
      const offsetY = sy - clampedRadius - 2;

      const size = 5;
      ctx.beginPath();
      ctx.moveTo(offsetX - size, offsetY - size);
      ctx.lineTo(offsetX + size, offsetY);
      ctx.lineTo(offsetX - size, offsetY + size);
      ctx.closePath();
      ctx.fillStyle = colour;
      ctx.fill();

      // Fleet name/ID label (close zoom only)
      if (detail === "close") {
        ctx.fillStyle = colour;
        ctx.globalAlpha = 0.7;
        ctx.font = "9px system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText(fleet.id, offsetX + size + 4, offsetY - 4);
        ctx.globalAlpha = 1.0;
      }
    }
  }

  ctx.restore();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function GalaxyMap({
  galaxy,
  playerState,
  selectedPlanetId,
  onSelectPlanet,
}: GalaxyMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);
  const mouseDownPosRef = useRef<{ x: number; y: number } | null>(null);

  // Track container size as state (so useViewport gets updated values)
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
    // Initial size
    const rect = container.getBoundingClientRect();
    setContainerSize({ w: rect.width, h: rect.height });
    return () => observer.disconnect();
  }, []);

  const [viewport, viewportActions] = useViewport(
    galaxy,
    containerSize.w,
    containerSize.h,
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

    renderGalaxy(ctx, dpr, w, h, galaxy, playerState, viewport, selectedPlanetId);
  }, [galaxy, playerState, viewport, containerSize, selectedPlanetId]);

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
          onSelectPlanet(null);
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
        onWheel={viewportActions.onWheel}
        onMouseDown={(e) => {
          // Focus the container so keyboard events fire after mouse interaction
          containerRef.current?.focus();
          mouseDownPosRef.current = { x: e.clientX, y: e.clientY };
          viewportActions.onMouseDown(e);
        }}
        onMouseMove={viewportActions.onMouseMove}
        onMouseUp={(e) => {
          viewportActions.onMouseUp(e);
          // Only treat as a click if the mouse didn't move much (not a drag)
          const downPos = mouseDownPosRef.current;
          mouseDownPosRef.current = null;
          if (!downPos) return;
          const dx = e.clientX - downPos.x;
          const dy = e.clientY - downPos.y;
          if (dx * dx + dy * dy > 9) return; // > 3px movement = drag, not click

          // Hit detection: find nearest planet within HIT_RADIUS_PX
          const canvas = canvasRef.current;
          if (!canvas) return;
          const rect = canvas.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const clickY = e.clientY - rect.top;

          let bestId: string | null = null;
          let bestDistSq = HIT_RADIUS_PX * HIT_RADIUS_PX;

          // Check all planets visible to the player
          for (const planet of playerState.planets) {
            const { sx, sy } = toScreen(
              planet.x,
              planet.y,
              viewport,
              containerSize.w,
              containerSize.h,
            );
            const distSq = (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
            if (distSq < bestDistSq) {
              bestDistSq = distSq;
              bestId = planet.id;
            }
          }

          // Also check galaxy planets not in player state (far zoom shows all)
          if (bestId === null) {
            for (const gp of galaxy.planets) {
              // Skip if already checked via playerState
              if (playerState.planets.some((pp) => pp.id === gp.id)) continue;
              const { sx, sy } = toScreen(
                gp.x,
                gp.y,
                viewport,
                containerSize.w,
                containerSize.h,
              );
              const distSq = (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
              if (distSq < bestDistSq) {
                bestDistSq = distSq;
                bestId = gp.id;
              }
            }
          }

          onSelectPlanet(bestId); // null if nothing hit = deselect
        }}
        onMouseLeave={(e) => {
          viewportActions.onMouseUp(e);
          mouseDownPosRef.current = null;
        }}
      />
      {/* Fit to galaxy button */}
      <button
        onClick={viewportActions.fitToGalaxy}
        className="absolute bottom-3 right-3 flex h-8 w-8 items-center justify-center rounded bg-zinc-800/80 text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-zinc-200"
        title="Fit to galaxy (Home)"
        aria-label="Fit to galaxy"
      >
        <Home size={16} />
      </button>
    </div>
  );
}
