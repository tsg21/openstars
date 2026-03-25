import { useState, useCallback, useRef, useMemo } from "react";
import type { Galaxy } from "../types";
import { PARSEC } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Viewport {
  /** Centre of the viewport in galaxy coordinates. */
  centreX: number;
  centreY: number;
  /** Pixels per galaxy-coordinate-unit. */
  scale: number;
}

export interface ViewportActions {
  /** Handle mouse wheel for zoom (centred on cursor). */
  onWheel: (e: React.WheelEvent<HTMLCanvasElement>) => void;
  /** Handle mouse down (start pan). */
  onMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  /** Handle mouse move (pan). */
  onMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  /** Handle mouse up (end pan). */
  onMouseUp: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  /** Handle key down (arrow keys, +/-). */
  onKeyDown: (e: React.KeyboardEvent) => void;
  /** Reset viewport to fit the entire galaxy. */
  fitToGalaxy: () => void;
  /** Whether the user is currently dragging. */
  isPanning: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ZOOM_FACTOR = 1.15;
const MIN_SCALE_FACTOR = 0.1; // 10% of fit scale
const MAX_SCALE_FACTOR = 50; // 50× fit scale
const PAN_SPEED_PX = 40; // pixels per arrow key press
const PADDING_PARSECS = 20;

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
export function computeFitViewport(
  galaxy: Galaxy,
  canvasW: number,
  canvasH: number,
): Viewport {
  const bounds = galaxyBounds(galaxy);
  const padding = PADDING_PARSECS * PARSEC;
  const worldW = bounds.maxX - bounds.minX + padding * 2;
  const worldH = bounds.maxY - bounds.minY + padding * 2;
  const centreX = (bounds.minX + bounds.maxX) / 2;
  const centreY = (bounds.minY + bounds.maxY) / 2;
  const scale = Math.min(canvasW / worldW, canvasH / worldH);
  return { centreX, centreY, scale };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Sentinel value meaning "no user interaction yet — use the fit viewport".
 * Once the user pans/zooms/resets, we store a real Viewport.
 */
const UNSET: Viewport = { centreX: NaN, centreY: NaN, scale: NaN };
function isUnset(v: Viewport): boolean {
  return Number.isNaN(v.scale);
}

export function useViewport(
  galaxy: Galaxy,
  canvasWidth: number,
  canvasHeight: number,
): [Viewport, ViewportActions] {
  // Derive the "fit" viewport from props (no effect / setState needed)
  const fitViewport = useMemo(() => {
    if (canvasWidth > 0 && canvasHeight > 0) {
      return computeFitViewport(galaxy, canvasWidth, canvasHeight);
    }
    return { centreX: 0, centreY: 0, scale: 1 };
  }, [galaxy, canvasWidth, canvasHeight]);

  // User viewport starts as UNSET — we'll use fitViewport until they interact
  const [userViewport, setUserViewport] = useState<Viewport>(UNSET);

  // Effective viewport: user's if set, otherwise fit
  const viewport = isUnset(userViewport) ? fitViewport : userViewport;

  // Panning state
  const [isPanning, setIsPanning] = useState(false);
  const panStartRef = useRef<{
    x: number;
    y: number;
    cx: number;
    cy: number;
  } | null>(null);

  // --- Actions ---

  const clampScale = useCallback(
    (s: number) => {
      const min = fitViewport.scale * MIN_SCALE_FACTOR;
      const max = fitViewport.scale * MAX_SCALE_FACTOR;
      return Math.max(min, Math.min(max, s));
    },
    [fitViewport.scale],
  );

  const onWheel = useCallback(
    (e: React.WheelEvent<HTMLCanvasElement>) => {
      e.preventDefault();
      const canvas = e.currentTarget;
      const rect = canvas.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;

      setUserViewport((prev) => {
        const current = isUnset(prev) ? fitViewport : prev;
        // Galaxy coordinate under the cursor before zoom
        const gx =
          current.centreX + (cursorX - rect.width / 2) / current.scale;
        const gy =
          current.centreY + (cursorY - rect.height / 2) / current.scale;

        const direction = e.deltaY < 0 ? 1 : -1;
        const factor = direction > 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR;
        const newScale = clampScale(current.scale * factor);

        // Adjust centre so the galaxy point under cursor stays under cursor
        const newCentreX = gx - (cursorX - rect.width / 2) / newScale;
        const newCentreY = gy - (cursorY - rect.height / 2) / newScale;

        return { centreX: newCentreX, centreY: newCentreY, scale: newScale };
      });
    },
    [clampScale, fitViewport],
  );

  const onMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (e.button !== 0) return;
      setIsPanning(true);
      panStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        cx: viewport.centreX,
        cy: viewport.centreY,
      };
    },
    [viewport.centreX, viewport.centreY],
  );

  const onMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isPanning || !panStartRef.current) return;
      const dx = e.clientX - panStartRef.current.x;
      const dy = e.clientY - panStartRef.current.y;
      setUserViewport((prev) => {
        // Guard: ref may have been cleared by onMouseUp between the outer
        // check and when React processes this updater
        const start = panStartRef.current;
        if (!start) return prev;
        return {
          centreX: start.cx - dx / viewport.scale,
          centreY: start.cy - dy / viewport.scale,
          scale: viewport.scale,
        };
      });
    },
    [isPanning, viewport.scale],
  );

  const onMouseUp = useCallback(() => {
    setIsPanning(false);
    panStartRef.current = null;
  }, []);

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      let handled = true;
      setUserViewport((prev) => {
        const current = isUnset(prev) ? fitViewport : prev;
        const panDelta = PAN_SPEED_PX / current.scale;
        switch (e.key) {
          case "ArrowLeft":
            return { ...current, centreX: current.centreX - panDelta };
          case "ArrowRight":
            return { ...current, centreX: current.centreX + panDelta };
          case "ArrowUp":
            return { ...current, centreY: current.centreY - panDelta };
          case "ArrowDown":
            return { ...current, centreY: current.centreY + panDelta };
          case "+":
          case "=":
            return {
              ...current,
              scale: clampScale(current.scale * ZOOM_FACTOR),
            };
          case "-":
          case "_":
            return {
              ...current,
              scale: clampScale(current.scale / ZOOM_FACTOR),
            };
          case "Home":
            return fitViewport;
          default:
            handled = false;
            return prev;
        }
      });
      if (handled) e.preventDefault();
    },
    [clampScale, fitViewport],
  );

  const fitToGalaxy = useCallback(() => {
    setUserViewport(fitViewport);
  }, [fitViewport]);

  return [
    viewport,
    {
      onWheel,
      onMouseDown,
      onMouseMove,
      onMouseUp,
      onKeyDown,
      fitToGalaxy,
      isPanning,
    },
  ];
}
