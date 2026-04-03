import { useRef, useEffect, useCallback, useState, type ReactNode } from "react";
import { Radar, Type } from "lucide-react";
import type { Galaxy, PlayerState, Selection, Position, Waypoint } from "../types";
import type { ScanLevel } from "../types/game";
import { PARSEC } from "../types";
import { useViewport } from "../hooks/useViewport";
import type { Viewport } from "../hooks/useViewport";
import { useCanvasColors } from "../hooks/useCanvasColors";
import { getPlanetRenderStyle } from "./galaxyMapRender";

// ---------------------------------------------------------------------------
// Selection / hit-detection constants
// ---------------------------------------------------------------------------

/** Maximum distance (in screen pixels) for a click to "hit" an object. */
const HIT_RADIUS_PX = 24;

/** Fleet dart icon size (base dimension). */
const FLEET_ICON_SIZE = 5;

/** Fixed planet dot radius. */
const PLANET_RADIUS = 4;

/** Scanner circle colours (matching original Stars! visual style). */
const SCANNER_COLORS = {
  normal: { fill: "rgba(255, 0, 0, 0.15)", stroke: "rgba(255, 0, 0, 0.4)" },
  normalSelected: { fill: "rgba(255, 0, 0, 0.25)", stroke: "rgba(255, 0, 0, 0.6)" },
  penetrating: { fill: "rgba(0, 255, 0, 0.1)", stroke: "rgba(0, 255, 0, 0.3)" },
  penetratingSelected: { fill: "rgba(0, 255, 0, 0.2)", stroke: "rgba(0, 255, 0, 0.5)" },
};


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
  editedWaypoints?: Waypoint[] | null;
  /** Called when the map is clicked while editing a fleet (galaxy coords). */
  onMapClick?: (pos: Position) => void;
  /** Called to remove a waypoint by index (right-click on marker). */
  onRemoveWaypoint?: (index: number) => void;
  /** Called once when viewport is ready, provides panTo function. */
  onViewportReady?: (panTo: (x: number, y: number) => void) => void;
  /** Initial whether to show scanner range circles on the map. */
  showScanners?: boolean;
}

type MapControlButtonProps = {
  active: boolean;
  label: string;
  onClick: () => void;
  children: ReactNode;
};

type HoveredPlanet = {
  id: string;
  name: string;
  sx: number;
  sy: number;
};

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

/** Check if a fleet is at a planet (exact position match). */
function isFleetAtPlanet(
  fleet: { position: Position },
  allPlanets: { x: number; y: number }[],
): { x: number; y: number } | null {
  for (const planet of allPlanets) {
    if (fleet.position.x === planet.x && fleet.position.y === planet.y) {
      return planet;
    }
  }
  return null;
}


type MapColors = {
  self: string;
  selfEdge: string;
  selfSelected: string;
  selfSelectedEdge: string;
  enemy: string;
  uncolonised: string;
};

type ScreenPoint = {
  sx: number;
  sy: number;
};

type PlanetRenderData = {
  id: string;
  name: string;
  x: number;
  y: number;
  owner: string | null;
  scanLevel: ScanLevel;
};

type FleetRenderData = PlayerState["fleets"][number];

type RenderHelpers = {
  toS: (gx: number, gy: number) => ScreenPoint;
  isVisible: (sx: number, sy: number) => boolean;
};

function createRenderHelpers(
  viewport: Viewport,
  canvasW: number,
  canvasH: number,
): RenderHelpers {
  const margin = 50;

  return {
    toS: (gx: number, gy: number) => toScreen(gx, gy, viewport, canvasW, canvasH),
    isVisible: (sx: number, sy: number) =>
      sx > -margin &&
      sx < canvasW + margin &&
      sy > -margin &&
      sy < canvasH + margin,
  };
}

function getSelectedIds(selection: Selection): {
  selectedFleetId: string | null;
  selectedPlanetId: string | null;
} {
  return {
    selectedFleetId: selection?.kind === "fleet" ? selection.id : null,
    selectedPlanetId: selection?.kind === "planet" ? selection.id : null,
  };
}

function getFleetWaypoints(
  fleet: FleetRenderData,
  editingFleetId: string | null,
  editedWaypoints: Waypoint[] | null,
): Waypoint[] {
  const isEditing = fleet.id === editingFleetId;
  return isEditing && editedWaypoints !== null
    ? editedWaypoints
    : (fleet.waypoints ?? []);
}

function renderBackground(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
) {
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, canvasW, canvasH);
}

function renderScannerCircles(
  ctx: CanvasRenderingContext2D,
  playerState: PlayerState,
  viewport: Viewport,
  selectedFleetId: string | null,
  toS: RenderHelpers["toS"],
) {
  const designScanners = new Map<string, { normal: number; penetrating: number }>();
  for (const design of playerState.designs) {
    designScanners.set(design.id, design.scanner);
  }

  for (const fleet of playerState.fleets) {
    if (fleet.owner !== playerState.player) continue;

    let maxNormal = 0;
    let maxPenetrating = 0;
    if (fleet.composition) {
      for (const ship of fleet.composition) {
        const scanner = designScanners.get(ship.designId);
        if (!scanner) continue;
        if (scanner.normal > maxNormal) maxNormal = scanner.normal;
        if (scanner.penetrating > maxPenetrating) maxPenetrating = scanner.penetrating;
      }
    }

    if (maxNormal === 0) continue;

    const { sx, sy } = toS(fleet.position.x, fleet.position.y);
    const isSelected = fleet.id === selectedFleetId;
    const normalRadiusPx = maxNormal * PARSEC * viewport.scale;
    const penetratingRadiusPx = maxPenetrating * PARSEC * viewport.scale;

    if (normalRadiusPx > 2) {
      const normalColors = isSelected ? SCANNER_COLORS.normalSelected : SCANNER_COLORS.normal;
      ctx.beginPath();
      ctx.arc(sx, sy, normalRadiusPx, 0, Math.PI * 2);
      ctx.fillStyle = normalColors.fill;
      ctx.fill();
      ctx.strokeStyle = normalColors.stroke;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    if (penetratingRadiusPx > 2) {
      const penetratingColors = isSelected
        ? SCANNER_COLORS.penetratingSelected
        : SCANNER_COLORS.penetrating;
      ctx.beginPath();
      ctx.arc(sx, sy, penetratingRadiusPx, 0, Math.PI * 2);
      ctx.fillStyle = penetratingColors.fill;
      ctx.fill();
      ctx.strokeStyle = penetratingColors.stroke;
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }
}

function renderFleetRoutes(
  ctx: CanvasRenderingContext2D,
  playerState: PlayerState,
  selectedFleetId: string | null,
  editingFleetId: string | null,
  editedWaypoints: Waypoint[] | null,
  colors: MapColors,
  toS: RenderHelpers["toS"],
) {
  for (const fleet of playerState.fleets) {
    if (fleet.owner !== playerState.player) continue;

    const waypoints = getFleetWaypoints(fleet, editingFleetId, editedWaypoints);
    if (waypoints.length === 0) continue;

    const isSelected = fleet.id === selectedFleetId;
    ctx.strokeStyle = isSelected ? colors.selfSelected : colors.self;
    ctx.lineWidth = isSelected ? 2 : 1;
    ctx.globalAlpha = isSelected ? 0.9 : 0.5;
    ctx.setLineDash(isSelected ? [] : [4, 4]);
    ctx.beginPath();

    const start = toS(fleet.position.x, fleet.position.y);
    ctx.moveTo(start.sx, start.sy);

    for (const waypoint of waypoints) {
      const dest = toS(waypoint.x, waypoint.y);
      ctx.lineTo(dest.sx, dest.sy);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1.0;
  }
}

function renderWaypointMarkers(
  ctx: CanvasRenderingContext2D,
  playerState: PlayerState,
  selectedFleetId: string | null,
  editingFleetId: string | null,
  editedWaypoints: Waypoint[] | null,
  colors: MapColors,
  toS: RenderHelpers["toS"],
  isVisible: RenderHelpers["isVisible"],
) {
  for (const fleet of playerState.fleets) {
    if (fleet.owner !== playerState.player) continue;

    const waypoints = getFleetWaypoints(fleet, editingFleetId, editedWaypoints);
    if (waypoints.length === 0) continue;

    const isSelected = fleet.id === selectedFleetId;

    for (let index = 0; index < waypoints.length; index++) {
      const waypoint = waypoints[index];
      const { sx, sy } = toS(waypoint.x, waypoint.y);
      if (!isVisible(sx, sy)) continue;

      ctx.beginPath();
      ctx.arc(sx, sy, 8, 0, Math.PI * 2);
      ctx.strokeStyle = isSelected ? colors.selfSelected : colors.self;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = isSelected ? 0.9 : 0.7;
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      ctx.fillStyle = isSelected ? colors.selfSelected : colors.self;
      ctx.font = "bold 9px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(index + 1), sx, sy);
    }
  }
}

function getPlanetsToRender(
  galaxy: Galaxy,
  playerState: PlayerState,
): PlanetRenderData[] {
  return galaxy.planets.map((galaxyPlanet) => {
    const playerPlanet = playerState.planets.find((planet) => planet.id === galaxyPlanet.id);
    return {
      id: galaxyPlanet.id,
      name: galaxyPlanet.name,
      x: galaxyPlanet.x,
      y: galaxyPlanet.y,
      owner: playerPlanet?.owner ?? null,
      scanLevel: playerPlanet?.scanLevel ?? "none",
    };
  });
}

function getHoveredPlanet(
  galaxy: Galaxy,
  playerState: PlayerState,
  viewport: Viewport,
  containerSize: { w: number; h: number },
  mouseX: number,
  mouseY: number,
): HoveredPlanet | null {
  const maxDistSq = HIT_RADIUS_PX * HIT_RADIUS_PX;
  let closestPlanet: HoveredPlanet | null = null;
  let closestDistSq = Number.POSITIVE_INFINITY;

  for (const planet of getPlanetsToRender(galaxy, playerState)) {
    const { sx, sy } = toScreen(
      planet.x,
      planet.y,
      viewport,
      containerSize.w,
      containerSize.h,
    );
    const distSq = (mouseX - sx) * (mouseX - sx) + (mouseY - sy) * (mouseY - sy);
    if (distSq >= maxDistSq || distSq >= closestDistSq) continue;

    closestPlanet = {
      id: planet.id,
      name: planet.name,
      sx,
      sy,
    };
    closestDistSq = distSq;
  }

  return closestPlanet;
}

function renderPlanets(
  ctx: CanvasRenderingContext2D,
  planetsToRender: PlanetRenderData[],
  playerState: PlayerState,
  selectedPlanetId: string | null,
  colors: MapColors,
  showPlanetNames: boolean,
  toS: RenderHelpers["toS"],
  isVisible: RenderHelpers["isVisible"],
) {
  for (const planet of planetsToRender) {
    const { sx, sy } = toS(planet.x, planet.y);
    if (!isVisible(sx, sy)) continue;

    const style = getPlanetRenderStyle(planet, playerState, {
      self: colors.self,
      selfEdge: colors.selfEdge,
      enemy: colors.enemy,
      uncolonised: colors.uncolonised,
    }, showPlanetNames);

    if (planet.id === selectedPlanetId) {
      // Upward-pointing dart drawn behind the planet dot
      ctx.beginPath();
      ctx.moveTo(sx, sy - PLANET_RADIUS);
      ctx.lineTo(sx - 9, sy - PLANET_RADIUS - 18);
      ctx.lineTo(sx, sy - PLANET_RADIUS - 10);
      ctx.lineTo(sx + 9, sy - PLANET_RADIUS - 18);
      ctx.closePath();
      ctx.fillStyle = "#facc15";
      ctx.globalAlpha = 0.9;
      ctx.fill();
      ctx.globalAlpha = 1.0;
    }

    ctx.beginPath();
    ctx.arc(sx, sy, style.dotRadius, 0, Math.PI * 2);
    if (style.edgeColour) {
      const gradient = ctx.createRadialGradient(
        sx - 1,
        sy - 1,
        0.5,
        sx,
        sy,
        style.dotRadius,
      );
      gradient.addColorStop(0, style.colour);
      gradient.addColorStop(0.68, style.colour);
      gradient.addColorStop(1, style.edgeColour);
      ctx.fillStyle = gradient;
    } else {
      ctx.fillStyle = style.colour;
    }
    ctx.globalAlpha = style.dotAlpha;
    ctx.fill();
    ctx.globalAlpha = 1.0;

    if (style.labelAlpha > 0) {
      ctx.fillStyle = style.colour;
      ctx.globalAlpha = style.labelAlpha;
      ctx.font = "10px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(planet.name, sx, sy + PLANET_RADIUS + 4);
      ctx.globalAlpha = 1.0;
    }

  }
}

function renderFleetsAtPlanets(
  ctx: CanvasRenderingContext2D,
  galaxy: Galaxy,
  playerState: PlayerState,
  toS: RenderHelpers["toS"],
  isVisible: RenderHelpers["isVisible"],
): Set<string> {
  const allPlanets = galaxy.planets.map((planet) => ({ x: planet.x, y: planet.y }));
  const processedFleets = new Set<string>();
  const indicatedPlanets = new Set<string>();

  for (const fleet of playerState.fleets) {
    const planet = isFleetAtPlanet(fleet, allPlanets);
    if (!planet) continue;

    processedFleets.add(fleet.id);

    const planetKey = `${planet.x},${planet.y}`;
    if (indicatedPlanets.has(planetKey)) continue;
    indicatedPlanets.add(planetKey);

    const { sx, sy } = toS(planet.x, planet.y);
    if (!isVisible(sx, sy)) continue;

    // Blue ring centered on the planet to indicate fleet(s) in orbit
    ctx.beginPath();
    ctx.arc(sx, sy, PLANET_RADIUS + 6, 0, Math.PI * 2);
    ctx.strokeStyle = "#60a5fa";
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.85;
    ctx.stroke();
    ctx.globalAlpha = 1.0;
  }

  return processedFleets;
}

function renderDeepSpaceFleets(
  ctx: CanvasRenderingContext2D,
  playerState: PlayerState,
  processedFleets: Set<string>,
  selectedFleetId: string | null,
  editingFleetId: string | null,
  editedWaypoints: Waypoint[] | null,
  colors: MapColors,
  toS: RenderHelpers["toS"],
  isVisible: RenderHelpers["isVisible"],
) {
  for (const fleet of playerState.fleets) {
    if (processedFleets.has(fleet.id)) continue;

    const { sx, sy } = toS(fleet.position.x, fleet.position.y);
    if (!isVisible(sx, sy)) continue;

    const colour = fleet.owner === playerState.player ? colors.self : colors.enemy;
    const isSelected = fleet.id === selectedFleetId;
    const waypoints = getFleetWaypoints(fleet, editingFleetId, editedWaypoints);

    let angle = 0;
    if (waypoints.length > 0) {
      const target = waypoints[0];
      angle = Math.atan2(target.y - fleet.position.y, target.x - fleet.position.x);
    }

    ctx.save();
    ctx.translate(sx, sy);
    ctx.rotate(angle);

    const size = FLEET_ICON_SIZE;
    const sizeX = size * 2.7;
    const sizeY = size * 1.2;
    ctx.beginPath();
    ctx.moveTo(sizeX, 0);
    ctx.lineTo(0, sizeY);
    ctx.lineTo(sizeX * 0.3, 0);
    ctx.lineTo(0, -sizeY);
    ctx.closePath();
    ctx.fillStyle = colour;
    ctx.fill();

    if (isSelected) {
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.9;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }

    ctx.restore();

  }
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
  editedWaypoints: Waypoint[] | null,
  colors: {
    self: string;
    selfEdge: string;
    selfSelected: string;
    selfSelectedEdge: string;
    enemy: string;
    uncolonised: string;
  },
  showPlanetNames: boolean,
  showScanners: boolean,
) {
  ctx.save();
  ctx.scale(dpr, dpr);
  renderBackground(ctx, canvasW, canvasH);

  const { toS, isVisible } = createRenderHelpers(viewport, canvasW, canvasH);
  const { selectedFleetId, selectedPlanetId } = getSelectedIds(selection);
  const planetsToRender = getPlanetsToRender(galaxy, playerState);

  if (showScanners) {
    renderScannerCircles(ctx, playerState, viewport, selectedFleetId, toS);
  }

  renderFleetRoutes(
    ctx,
    playerState,
    selectedFleetId,
    editingFleetId,
    editedWaypoints,
    colors,
    toS,
  );
  renderWaypointMarkers(
    ctx,
    playerState,
    selectedFleetId,
    editingFleetId,
    editedWaypoints,
    colors,
    toS,
    isVisible,
  );
  renderPlanets(
    ctx,
    planetsToRender,
    playerState,
    selectedPlanetId,
    colors,
    showPlanetNames,
    toS,
    isVisible,
  );

  const processedFleets = renderFleetsAtPlanets(
    ctx,
    galaxy,
    playerState,
    toS,
    isVisible,
  );
  renderDeepSpaceFleets(
    ctx,
    playerState,
    processedFleets,
    selectedFleetId,
    editingFleetId,
    editedWaypoints,
    colors,
    toS,
    isVisible,
  );

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
  onViewportReady,
  showScanners = false,
}: GalaxyMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);
  const mouseDownPosRef = useRef<{ x: number; y: number } | null>(null);
  const [showPlanetNames, setShowPlanetNames] = useState(true);
  const [showScannerOverlays, setShowScannerOverlays] = useState(showScanners);
  const [hoveredPlanet, setHoveredPlanet] = useState<HoveredPlanet | null>(null);

  // Read colors from CSS variables
  const colors = useCanvasColors();

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
  const canvasCursorClass = viewportActions.isPanning
    ? "cursor-grabbing"
    : hoveredPlanet
      ? "cursor-pointer"
      : "cursor-grab";

  // Notify parent when viewport is ready
  useEffect(() => {
    if (onViewportReady) {
      onViewportReady(viewportActions.panTo);
    }
  }, [onViewportReady, viewportActions.panTo]);

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
      editingFleetId, editedWaypoints, colors, showPlanetNames, showScannerOverlays,
    );
  }, [galaxy, playerState, viewport, containerSize, selection, editingFleetId, editedWaypoints, colors, showPlanetNames, showScannerOverlays]);

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
      <div className="pointer-events-none absolute inset-x-0 top-3 z-10 flex justify-center">
        <div className="pointer-events-auto flex items-center gap-1 rounded-md border border-white/15 bg-black/70 p-1 shadow-[0_8px_24px_rgba(0,0,0,0.35)] backdrop-blur-sm">
          <MapControlButton
            active={showPlanetNames}
            label="Show planet names"
            onClick={() => setShowPlanetNames((current) => !current)}
          >
            <Type className="h-3.5 w-3.5" />
          </MapControlButton>
          <MapControlButton
            active={showScannerOverlays}
            label="Show scanners"
            onClick={() => setShowScannerOverlays((current) => !current)}
          >
            <Radar className="h-3.5 w-3.5" />
          </MapControlButton>
        </div>
      </div>
      <canvas
        ref={canvasRef}
        className={canvasCursorClass}
        onMouseDown={(e) => {
          containerRef.current?.focus();
          setHoveredPlanet(null);
          if (e.button === 0) {
            mouseDownPosRef.current = { x: e.clientX, y: e.clientY };
          }
          viewportActions.onMouseDown(e);
        }}
        onMouseMove={(e) => {
          viewportActions.onMouseMove(e);

          const canvas = canvasRef.current;
          if (!canvas || viewportActions.isPanning || e.buttons !== 0) {
            setHoveredPlanet(null);
            return;
          }

          const rect = canvas.getBoundingClientRect();
          const hoverX = e.clientX - rect.left;
          const hoverY = e.clientY - rect.top;

          setHoveredPlanet(
            getHoveredPlanet(
              galaxy,
              playerState,
              viewport,
              containerSize,
              hoverX,
              hoverY,
            ),
          );
        }}
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

          // Build planet list for fleet position checking
          const allPlanets = galaxy.planets.map((p) => ({ x: p.x, y: p.y }));

          // Fleet hit detection — orbit fleets are not click-selectable (use planet detail panel)
          for (const fleet of playerState.fleets) {
            const planet = isFleetAtPlanet(fleet, allPlanets);
            if (planet) continue;

            const { sx, sy } = toScreen(
              fleet.position.x, fleet.position.y,
              viewport, containerSize.w, containerSize.h,
            );
            const distSq =
              (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
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
          setHoveredPlanet(null);
        }}
      />
      {hoveredPlanet ? (
        <div
          className="pointer-events-none absolute z-10 min-w-32 rounded-md border border-white/15 bg-black/85 px-3 py-2 text-xs text-[var(--color-foreground)] shadow-[0_10px_30px_rgba(0,0,0,0.4)] backdrop-blur-sm"
          style={{
            left: hoveredPlanet.sx + 12,
            top: hoveredPlanet.sy - 10,
            transform: "translateY(-100%)",
          }}
        >
          <div className="font-medium leading-tight">{hoveredPlanet.name}</div>
          <div className="mt-1 text-[11px] uppercase tracking-[0.14em] text-white/60">
            Click to select
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MapControlButton({
  active,
  label,
  onClick,
  children,
}: MapControlButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      title={label}
      onClick={onClick}
      className={
        "flex h-8 w-8 items-center justify-center rounded-sm border text-[var(--color-foreground)] transition-colors " +
        (active
          ? "border-white/40 bg-white/18 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]"
          : "border-white/15 bg-white/6 hover:bg-white/12")
      }
    >
      {children}
    </button>
  );
}
