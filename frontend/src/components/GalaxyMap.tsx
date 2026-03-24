import { useRef, useEffect, useCallback } from "react";
import type { Galaxy, PlayerState } from "../types";
import { PARSEC } from "../types";

// ---------------------------------------------------------------------------
// Colour constants (from PRD 08)
// ---------------------------------------------------------------------------
const COLOUR_SELF = "#3b82f6"; // blue
const COLOUR_ENEMY = "#ef4444"; // red
const COLOUR_UNCOLONISED = "#6b7280"; // grey
const COLOUR_ROUTE = "#3b82f6"; // own fleet routes

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface GalaxyMapProps {
  galaxy: Galaxy;
  playerState: PlayerState;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Bounding box of all galaxy planets, in galaxy coordinates. */
function galaxyBounds(galaxy: Galaxy) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const p of galaxy.planets) {
    if (p.x < minX) minX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.x > maxX) maxX = p.x;
    if (p.y > maxY) maxY = p.y;
  }
  return { minX, minY, maxX, maxY };
}

/** Compute viewport that fits all planets with padding. */
function fitViewport(
  galaxy: Galaxy,
  canvasW: number,
  canvasH: number,
): { centreX: number; centreY: number; scale: number } {
  const bounds = galaxyBounds(galaxy);
  const padding = 20 * PARSEC; // 20 parsecs of padding
  const worldW = bounds.maxX - bounds.minX + padding * 2;
  const worldH = bounds.maxY - bounds.minY + padding * 2;
  const centreX = (bounds.minX + bounds.maxX) / 2;
  const centreY = (bounds.minY + bounds.maxY) / 2;
  const scale = Math.min(canvasW / worldW, canvasH / worldH);
  return { centreX, centreY, scale };
}

/** Galaxy coords → screen pixel coords. */
function toScreen(
  gx: number,
  gy: number,
  centreX: number,
  centreY: number,
  scale: number,
  canvasW: number,
  canvasH: number,
): { sx: number; sy: number } {
  return {
    sx: (gx - centreX) * scale + canvasW / 2,
    sy: (gy - centreY) * scale + canvasH / 2,
  };
}

/** Planet colour based on ownership. */
function planetColour(
  owner: string | null,
  currentPlayer: string,
): string {
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
) {
  const { centreX, centreY, scale } = fitViewport(galaxy, canvasW, canvasH);

  // Clear
  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, canvasW, canvasH);

  const toS = (gx: number, gy: number) =>
    toScreen(gx, gy, centreX, centreY, scale, canvasW, canvasH);

  // --- Fleet routes (draw before fleets/planets so they're behind) ---
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

  // --- Planets ---
  const planetRadius = Math.max(3, 5 * scale * PARSEC * 0.02);
  const clampedRadius = Math.min(Math.max(planetRadius, 3), 8);

  for (const planet of playerState.planets) {
    const { sx, sy } = toS(planet.x, planet.y);
    const colour = planetColour(planet.owner, playerState.player);

    // Planet dot
    ctx.beginPath();
    ctx.arc(sx, sy, clampedRadius, 0, Math.PI * 2);
    ctx.fillStyle = colour;
    ctx.fill();

    // Planet name label
    ctx.fillStyle = colour;
    ctx.globalAlpha = 0.8;
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(planet.name, sx, sy + clampedRadius + 12);
    ctx.globalAlpha = 1.0;
  }

  // --- Fleets (small triangles) ---
  for (const fleet of playerState.fleets) {
    const { sx, sy } = toS(fleet.position.x, fleet.position.y);
    const colour =
      fleet.owner === playerState.player ? COLOUR_SELF : COLOUR_ENEMY;

    // Offset fleet icon slightly so it doesn't overlap a planet at the same position
    const offsetX = sx + clampedRadius + 4;
    const offsetY = sy - clampedRadius - 2;

    // Draw a small chevron/triangle pointing right
    const size = 5;
    ctx.beginPath();
    ctx.moveTo(offsetX - size, offsetY - size);
    ctx.lineTo(offsetX + size, offsetY);
    ctx.lineTo(offsetX - size, offsetY + size);
    ctx.closePath();
    ctx.fillStyle = colour;
    ctx.fill();
  }

  ctx.restore();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function GalaxyMap({ galaxy, playerState }: GalaxyMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = container.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;

    // Size the canvas element (CSS pixels) and backing store (device pixels)
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    canvas.width = w * dpr;
    canvas.height = h * dpr;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    renderGalaxy(ctx, dpr, w, h, galaxy, playerState);
  }, [galaxy, playerState]);

  useEffect(() => {
    draw();

    const observer = new ResizeObserver(() => draw());
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    return () => observer.disconnect();
  }, [draw]);

  return (
    <div
      ref={containerRef}
      className="flex-1 bg-[var(--color-map-bg)]"
    >
      <canvas ref={canvasRef} />
    </div>
  );
}
