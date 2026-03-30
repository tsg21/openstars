import { useRef, useEffect, useCallback, useState } from "react";
import type { Galaxy, PlayerState, Selection, Position } from "../types";
import type { ScanLevel } from "../types/game";
import { PARSEC } from "../types";
import { useViewport } from "../hooks/useViewport";
import type { Viewport } from "../hooks/useViewport";
import { useCanvasColors } from "../hooks/useCanvasColors";

// ---------------------------------------------------------------------------
// Selection / hit-detection constants
// ---------------------------------------------------------------------------

/** Maximum distance (in screen pixels) for a click to "hit" an object. */
const HIT_RADIUS_PX = 12;

/** Radius of the selection highlight ring, relative to planet dot radius. */
const SELECTION_RING_OFFSET = 4;

/** Fleet dart icon size (base dimension). */
const FLEET_ICON_SIZE = 5;

/** Fixed planet dot radius. */
const PLANET_RADIUS = 5;

/** Scanner circle colours (matching original Stars! visual style). */
const SCANNER_COLORS = {
  normal: { fill: "rgba(255, 0, 0, 0.15)", stroke: "rgba(255, 0, 0, 0.4)" },
  normalSelected: { fill: "rgba(255, 0, 0, 0.25)", stroke: "rgba(255, 0, 0, 0.6)" },
  penetrating: { fill: "rgba(0, 255, 0, 0.1)", stroke: "rgba(0, 255, 0, 0.3)" },
  penetratingSelected: { fill: "rgba(0, 255, 0, 0.2)", stroke: "rgba(0, 255, 0, 0.5)" },
};

/** Offset for first fleet ring around planet. */
const FLEET_RING_OFFSET = 7;

/** Spacing between multiple fleet rings. */
const FLEET_RING_SPACING = 6;

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
  /** Called once when viewport is ready, provides panTo function. */
  onViewportReady?: (panTo: (x: number, y: number) => void) => void;
  /** Whether to show scanner range circles on the map. */
  showScanners?: boolean;
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
function planetColour(
  owner: string | null,
  currentPlayer: string,
  selfColor: string,
  enemyColor: string,
  uncolonisedColor: string,
): string {
  if (owner === currentPlayer) return selfColor;
  if (owner !== null) return enemyColor;
  return uncolonisedColor;
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

/** Group fleets by their position for rendering multiple fleets at same location. */
function groupFleetsByPosition(
  fleets: { id: string; position: Position; owner: string }[],
): Map<string, { id: string; position: Position; owner: string }[]> {
  const groups = new Map<string, { id: string; position: Position; owner: string }[]>();
  for (const fleet of fleets) {
    const key = `${fleet.position.x},${fleet.position.y}`;
    const group = groups.get(key) || [];
    group.push(fleet);
    groups.set(key, group);
  }
  return groups;
}

type MapColors = {
  self: string;
  selfSelected: string;
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
  editedWaypoints: Position[] | null,
): Position[] {
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
  editedWaypoints: Position[] | null,
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
  editedWaypoints: Position[] | null,
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

function renderPlanets(
  ctx: CanvasRenderingContext2D,
  planetsToRender: PlanetRenderData[],
  playerState: PlayerState,
  selectedPlanetId: string | null,
  colors: MapColors,
  toS: RenderHelpers["toS"],
  isVisible: RenderHelpers["isVisible"],
) {
  for (const planet of planetsToRender) {
    const { sx, sy } = toS(planet.x, planet.y);
    if (!isVisible(sx, sy)) continue;

    const isUnscanned = planet.scanLevel === "none";
    const colour = isUnscanned
      ? "#444444"
      : planetColour(
          planet.owner,
          playerState.player,
          colors.self,
          colors.enemy,
          colors.uncolonised,
        );
    const dotRadius = isUnscanned ? PLANET_RADIUS - 1 : PLANET_RADIUS;

    ctx.beginPath();
    ctx.arc(sx, sy, dotRadius, 0, Math.PI * 2);
    ctx.fillStyle = colour;
    ctx.globalAlpha = isUnscanned ? 0.5 : 1.0;
    ctx.fill();
    ctx.globalAlpha = 1.0;

    ctx.fillStyle = colour;
    ctx.globalAlpha = isUnscanned ? 0.3 : 0.8;
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(planet.name, sx, sy + PLANET_RADIUS + 4);
    ctx.globalAlpha = 1.0;

    if (planet.id === selectedPlanetId) {
      ctx.beginPath();
      ctx.arc(sx, sy, PLANET_RADIUS + SELECTION_RING_OFFSET, 0, Math.PI * 2);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.9;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }
  }
}

function renderFleetsAtPlanets(
  ctx: CanvasRenderingContext2D,
  galaxy: Galaxy,
  playerState: PlayerState,
  selectedFleetId: string | null,
  colors: MapColors,
  toS: RenderHelpers["toS"],
  isVisible: RenderHelpers["isVisible"],
): Set<string> {
  const allPlanets = galaxy.planets.map((planet) => ({ x: planet.x, y: planet.y }));
  const fleetGroups = groupFleetsByPosition(playerState.fleets);
  const processedFleets = new Set<string>();

  for (const fleetsAtPosition of fleetGroups.values()) {
    const firstFleet = fleetsAtPosition[0];
    const planet = isFleetAtPlanet(firstFleet, allPlanets);
    if (!planet) continue;

    const { sx, sy } = toS(planet.x, planet.y);
    if (!isVisible(sx, sy)) continue;

    const sortedFleets = [...fleetsAtPosition].sort((a, b) => a.id.localeCompare(b.id));

    for (let index = 0; index < sortedFleets.length; index++) {
      const fleet = sortedFleets[index];
      processedFleets.add(fleet.id);

      const colour = fleet.owner === playerState.player ? colors.self : colors.enemy;
      const isSelected = fleet.id === selectedFleetId;
      const ringRadius = PLANET_RADIUS + FLEET_RING_OFFSET + (index * FLEET_RING_SPACING);

      ctx.beginPath();
      ctx.arc(sx, sy, ringRadius, 0, Math.PI * 2);
      ctx.strokeStyle = colour;
      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.globalAlpha = isSelected ? 1.0 : 0.8;
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      if (isSelected) {
        ctx.beginPath();
        ctx.arc(sx, sy, ringRadius + 1, 0, Math.PI * 2);
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.6;
        ctx.stroke();
        ctx.globalAlpha = 1.0;
      }

      const labelAngle = (index * Math.PI * 0.4) + Math.PI * 0.25;
      const labelDist = ringRadius + 8;
      const labelX = sx + Math.cos(labelAngle) * labelDist;
      const labelY = sy + Math.sin(labelAngle) * labelDist;

      ctx.fillStyle = colour;
      ctx.globalAlpha = 0.7;
      ctx.font = "9px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(fleet.id, labelX, labelY);
      ctx.globalAlpha = 1.0;
    }
  }

  return processedFleets;
}

function renderDeepSpaceFleets(
  ctx: CanvasRenderingContext2D,
  playerState: PlayerState,
  processedFleets: Set<string>,
  selectedFleetId: string | null,
  editingFleetId: string | null,
  editedWaypoints: Position[] | null,
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

    ctx.fillStyle = colour;
    ctx.globalAlpha = 0.7;
    ctx.font = "9px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(fleet.id, sx + size + 4, sy - 4);
    ctx.globalAlpha = 1.0;
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
  editedWaypoints: Position[] | null,
  colors: {
    self: string;
    selfSelected: string;
    enemy: string;
    uncolonised: string;
  },
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
    toS,
    isVisible,
  );

  const processedFleets = renderFleetsAtPlanets(
    ctx,
    galaxy,
    playerState,
    selectedFleetId,
    colors,
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
      editingFleetId, editedWaypoints, colors, showScanners,
    );
  }, [galaxy, playerState, viewport, containerSize, selection, editingFleetId, editedWaypoints, colors, showScanners]);

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

          // Build planet list for fleet position checking
          const allPlanets = galaxy.planets.map((p) => ({ x: p.x, y: p.y }));

          // Fleet hit detection
          for (const fleet of playerState.fleets) {
            const { sx, sy } = toScreen(
              fleet.position.x, fleet.position.y,
              viewport, containerSize.w, containerSize.h,
            );

            const planet = isFleetAtPlanet(fleet, allPlanets);

            if (planet) {
              // Fleet is at a planet - check ring hit
              const { sx: planetSx, sy: planetSy } = toScreen(
                planet.x, planet.y,
                viewport, containerSize.w, containerSize.h,
              );
              const distSq =
                (clickX - planetSx) * (clickX - planetSx) +
                (clickY - planetSy) * (clickY - planetSy);

              // Calculate which ring this fleet is in
              const fleetsAtPlanet = playerState.fleets
                .filter((f) => f.position.x === planet.x && f.position.y === planet.y)
                .sort((a, b) => a.id.localeCompare(b.id));
              const fleetIndex = fleetsAtPlanet.findIndex((f) => f.id === fleet.id);
              const ringRadius = PLANET_RADIUS + FLEET_RING_OFFSET + (fleetIndex * FLEET_RING_SPACING);
              const ringRadiusSq = ringRadius * ringRadius;
              const innerRadius = fleetIndex > 0
                ? PLANET_RADIUS + FLEET_RING_OFFSET + ((fleetIndex - 1) * FLEET_RING_SPACING)
                : PLANET_RADIUS;
              const innerRadiusSq = innerRadius * innerRadius;

              // Check if click is within the ring area (between inner and outer radius)
              if (distSq <= ringRadiusSq && distSq >= innerRadiusSq) {
                candidates.push({
                  sel: { kind: "fleet", id: fleet.id },
                  distSq,
                });
              }
            } else {
              // Fleet is in deep space - check dart hit (centered on fleet position)
              const distSq =
                (clickX - sx) * (clickX - sx) + (clickY - sy) * (clickY - sy);
              if (distSq < maxDistSq) {
                candidates.push({
                  sel: { kind: "fleet", id: fleet.id },
                  distSq,
                });
              }
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
