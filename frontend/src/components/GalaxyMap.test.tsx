import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { GalaxyMap } from "./GalaxyMap";
import { getPlanetRenderStyle } from "./galaxyMapRender";
import type { Galaxy, PlayerState, Selection } from "../types";

// Mock ResizeObserver
class MockResizeObserver {
  callback: ResizeObserverCallback;
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }
  observe(target: Element) {
    // Fire immediately with a mock entry
    this.callback(
      [
        {
          target,
          contentRect: { width: 800, height: 600 } as DOMRectReadOnly,
          borderBoxSize: [],
          contentBoxSize: [],
          devicePixelContentBoxSize: [],
        },
      ],
      this,
    );
  }
  unobserve() {}
  disconnect() {}
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
(globalThis as any).ResizeObserver = MockResizeObserver;

/** Shared default props for GalaxyMap in tests. */
const testGalaxy: Galaxy = {
  galaxy: {
    name: "Test Galaxy",
    size: "small",
    seed: 42,
  },
  planets: [
    { id: "PL000001", name: "Sol", x: 500_000_000_000, y: 500_000_000_000 },
    { id: "PL000002", name: "Rigel", x: 600_000_000_000, y: 600_000_000_000 },
  ],
};

const testPlayerState: PlayerState = {
  player: "tim",
  turn: 3,
  planets: [
    {
      id: "PL000001",
      name: "Sol",
      x: 500_000_000_000,
      y: 500_000_000_000,
      owner: "tim",
      population: 25_000,
      scanLevel: "detailed",
    },
    {
      id: "PL000002",
      name: "Rigel",
      x: 600_000_000_000,
      y: 600_000_000_000,
      owner: null,
      scanLevel: "basic",
    },
  ],
  fleets: [
    {
      id: "FL000001",
      owner: "tim",
      position: { x: 500_000_000_000, y: 500_000_000_000 },
      composition: [{ designId: "DE000001", count: 1 }],
      waypoints: [{ x: 600_000_000_000, y: 600_000_000_000 }],
    },
  ],
  designs: [
    {
      id: "DE000001",
      owner: "tim",
      name: "Scout",
      hull: "Scout",
      speed: 6,
      scanner: { normal: 150, penetrating: 0 },
    },
  ],
  events: [
    {
      type: "fleet_arrived",
      fleetId: "FL000001",
      fleetName: "Scout 1",
      planetId: "PL000001",
      planetName: "Sol",
      turn: 3,
    },
  ],
};

const defaultProps = {
  galaxy: testGalaxy,
  playerState: testPlayerState,
  selection: null as Selection,
  onSelect: vi.fn(),
  editingFleetId: null,
  editedWaypoints: null,
};

describe("GalaxyMap selection", () => {
  it("renders without crashing", () => {
    const onSelect = vi.fn();
    render(
      <GalaxyMap {...defaultProps} onSelect={onSelect} />,
    );
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeTruthy();
  });

  it("calls onSelect(null) when clicking empty space", () => {
    const onSelect = vi.fn();
    render(
      <GalaxyMap {...defaultProps} onSelect={onSelect} />,
    );

    const canvas = document.querySelector("canvas")!;

    // Click far from any planet (top-left corner, well away from centre)
    fireEvent.mouseDown(canvas, { clientX: -9999, clientY: -9999, button: 0 });
    fireEvent.mouseUp(canvas, { clientX: -9999, clientY: -9999 });

    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("deselects on Escape key", () => {
    const onSelect = vi.fn();
    const sel: Selection = { kind: "planet", id: "PLk8m3x2" };
    render(
      <GalaxyMap {...defaultProps} selection={sel} onSelect={onSelect} />,
    );

    const container = document.querySelector("[tabindex]")!;
    fireEvent.keyDown(container, { key: "Escape" });

    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("does not fire selection on drag (mouse moved)", () => {
    const onSelect = vi.fn();
    render(
      <GalaxyMap {...defaultProps} onSelect={onSelect} />,
    );

    const canvas = document.querySelector("canvas")!;

    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100, button: 0 });
    fireEvent.mouseMove(canvas, { clientX: 120, clientY: 120 });
    fireEvent.mouseUp(canvas, { clientX: 120, clientY: 120 });

    expect(onSelect).not.toHaveBeenCalled();
  });

  it("ignores right-click for selection", () => {
    const onSelect = vi.fn();
    render(
      <GalaxyMap {...defaultProps} onSelect={onSelect} />,
    );

    const canvas = document.querySelector("canvas")!;

    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100, button: 2 });
    fireEvent.mouseUp(canvas, { clientX: 100, clientY: 100 });

    expect(onSelect).not.toHaveBeenCalled();
  });

  it("renders unscanned unknown planets with the bright uncolonised colour", async () => {
    const style = getPlanetRenderStyle(
      { owner: null, scanLevel: "none" },
      { player: "tim" },
      {
        self: "#60a5fa",
        enemy: "#ef4444",
        uncolonised: "#cbd5e1",
      },
    );

    expect(style).toEqual({
      colour: "#cbd5e1",
      dotRadius: 5,
      dotAlpha: 1,
      labelAlpha: 0.8,
    });
  });
});
