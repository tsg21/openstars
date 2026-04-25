import { useState, useCallback, useRef, useMemo } from "react";
import type { Galaxy } from "../types";
import { LIGHT_YEAR } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Viewport {
  /** Centre of the viewport in galaxy coordinates. */
  centreX: number;
  centreY: number;
  /** Pixels per galaxy-coordinate-unit (fixed). */
  scale: number;
}

export interface ViewportActions {
  /** Handle mouse down (start pan). */
  onMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  /** Handle mouse move (pan). */
  onMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  /** Handle mouse up (end pan). */
  onMouseUp: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  /** Handle key down (arrow keys). */
  onKeyDown: (e: React.KeyboardEvent) => void;
  /** Reset viewport to initial centre. */
  resetView: () => void;
  /** Pan to a specific position in galaxy coordinates. */
  panTo: (x: number, y: number) => void;
  /** Whether the user is currently dragging. */
  isPanning: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAN_SPEED_PX = 40; // pixels per arrow key press

/**
 * Fixed scale: ~400 light-years across 1000 pixels.
 * This keeps labels and routes readable while fitting about twice as much of
 * the surrounding galaxy on screen.
 */
export const FIXED_SCALE = 1000 / (400 * LIGHT_YEAR);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Find the initial centre point — the first planet owned by the player,
 * falling back to the galaxy centroid.
 */
export function computeInitialCentre(
  galaxy: Galaxy,
  playerPlanetId?: string,
): { centreX: number; centreY: number } {
  // If a player planet ID is provided, centre on it
  if (playerPlanetId) {
    const planet = galaxy.planets.find((p) => p.id === playerPlanetId);
    if (planet) {
      return { centreX: planet.x, centreY: planet.y };
    }
  }

  // Fallback: galaxy centroid
  if (galaxy.planets.length === 0) {
    return { centreX: 0, centreY: 0 };
  }
  let sumX = 0;
  let sumY = 0;
  for (const p of galaxy.planets) {
    sumX += p.x;
    sumY += p.y;
  }
  return {
    centreX: sumX / galaxy.planets.length,
    centreY: sumY / galaxy.planets.length,
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useViewport(
  galaxy: Galaxy,
  _canvasWidth: number,
  _canvasHeight: number,
  playerPlanetId?: string,
): [Viewport, ViewportActions] {
  const initialViewport = useMemo(() => {
    const initial = computeInitialCentre(galaxy, playerPlanetId);
    return {
      centreX: initial.centreX,
      centreY: initial.centreY,
      scale: FIXED_SCALE,
    };
  }, [galaxy, playerPlanetId]);

  const [viewport, setViewport] = useState<Viewport>(initialViewport);

  // Panning state
  const [isPanning, setIsPanning] = useState(false);
  const panStartRef = useRef<{
    x: number;
    y: number;
    cx: number;
    cy: number;
  } | null>(null);

  // --- Actions ---

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
      setViewport((prev) => {
        const start = panStartRef.current;
        if (!start) return prev;
        return {
          centreX: start.cx - dx / FIXED_SCALE,
          centreY: start.cy - dy / FIXED_SCALE,
          scale: FIXED_SCALE,
        };
      });
    },
    [isPanning],
  );

  const onMouseUp = useCallback(() => {
    setIsPanning(false);
    panStartRef.current = null;
  }, []);

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const panDelta = PAN_SPEED_PX / FIXED_SCALE;
      let handled = true;
      switch (e.key) {
        case "ArrowLeft":
          setViewport((prev) => ({ ...prev, centreX: prev.centreX - panDelta }));
          break;
        case "ArrowRight":
          setViewport((prev) => ({ ...prev, centreX: prev.centreX + panDelta }));
          break;
        case "ArrowUp":
          setViewport((prev) => ({ ...prev, centreY: prev.centreY - panDelta }));
          break;
        case "ArrowDown":
          setViewport((prev) => ({ ...prev, centreY: prev.centreY + panDelta }));
          break;
        case "Home":
          setViewport(initialViewport);
          break;
        default:
          handled = false;
      }
      if (handled) e.preventDefault();
    },
    [initialViewport],
  );

  const resetView = useCallback(() => {
    setViewport(initialViewport);
  }, [initialViewport]);

  const panTo = useCallback((x: number, y: number) => {
    setViewport((prev) => ({
      ...prev,
      centreX: x,
      centreY: y,
    }));
  }, []);

  return [
    viewport,
    {
      onMouseDown,
      onMouseMove,
      onMouseUp,
      onKeyDown,
      resetView,
      panTo,
      isPanning,
    },
  ];
}
