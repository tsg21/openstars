import { describe, it, expect, vi } from "vitest";
import { render, fireEvent, screen, waitFor } from "@testing-library/react";
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

function createCanvasGradientMock(): CanvasGradient {
  return {
    addColorStop() {},
  } as CanvasGradient;
}

function createMockCanvasContext() {
  const strokeStyleValues: string[] = [];
  const fillStyleValues: Array<string | CanvasGradient> = [];
  return {
    save: vi.fn(),
    restore: vi.fn(),
    scale: vi.fn(),
    translate: vi.fn(),
    rotate: vi.fn(),
    clearRect: vi.fn(),
    fillRect: vi.fn(),
    fillText: vi.fn(),
    beginPath: vi.fn(),
    closePath: vi.fn(),
    roundRect: vi.fn(),
    fill: vi.fn(),
    arc: vi.fn(),
    stroke: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    setLineDash: vi.fn(),
    createRadialGradient: vi.fn(createCanvasGradientMock),
    set font(_value: string) {},
    set fillStyle(value: string | CanvasGradient) {
      fillStyleValues.push(value);
    },
    set strokeStyle(value: string) {
      strokeStyleValues.push(value);
    },
    set lineWidth(_value: number) {},
    set globalAlpha(_value: number) {},
    set textBaseline(_value: CanvasTextBaseline) {},
    set textAlign(_value: CanvasTextAlign) {},
    strokeStyleValues,
    fillStyleValues,
  } as unknown as CanvasRenderingContext2D & {
    arc: ReturnType<typeof vi.fn>;
    strokeStyleValues: string[];
    fillStyleValues: Array<string | CanvasGradient>;
  };
}

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
      scanAge: 0,
    },
    {
      id: "PL000002",
      name: "Rigel",
      x: 600_000_000_000,
      y: 600_000_000_000,
      owner: null,
      scanLevel: "basic",
      scanAge: 0,
    },
  ],
  fleets: [
    {
      id: "FL000001",
      owner: "tim",
      position: { x: 500_000_000_000, y: 500_000_000_000 },
      composition: [{ designId: "DE000001", count: 1 }],
      waypoints: [{ x: 600_000_000_000, y: 600_000_000_000, warp: 5 }],
    },
  ],
  designs: [
    {
      id: "DE000001",
      owner: "tim",
      name: "Scout",
      hull: "Scout",
      components: [],
      mass: 25,
      fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
      fuelCapacity: 50,
      scanner: { normal: 150, penetrating: 0 },
      cargoCapacity: 0,
      cost: {
        resources: 15,
        minerals: { ironium: 5, boranium: 3, germanium: 2 },
      },
    },
  ],
  events: [
    {
      owner: "tim",
      sourceId: "PL000001",
      code: "movement.fleet_arrived",
      values: ["Scout 1", "Sol"],
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
      { owner: null, scanLevel: "none", scanAge: 0 },
      { player: "tim" },
      {
        self: "#01f803",
        selfEdge: "#017a03",
        enemy: "#ef4444",
        uncolonised: "#cbd5e1",
      },
    );

    expect(style).toEqual({
      colour: "#cbd5e1",
      edgeColour: null,
      dotRadius: 4,
      dotAlpha: 1,
      labelAlpha: 0.65,
    });
  });

  it("hides planet labels when requested", () => {
    const style = getPlanetRenderStyle(
      { owner: null, scanLevel: "none", scanAge: 0 },
      { player: "tim" },
      {
        self: "#01f803",
        selfEdge: "#017a03",
        enemy: "#ef4444",
        uncolonised: "#cbd5e1",
      },
      false,
    );

    expect(style.labelAlpha).toBe(0);
  });

  it("uses a darker edge colour for player-owned planets", () => {
    const style = getPlanetRenderStyle(
      { owner: "tim", scanLevel: "detailed", scanAge: 0 },
      { player: "tim" },
      {
        self: "#01f803",
        selfEdge: "#017a03",
        enemy: "#ef4444",
        uncolonised: "#cbd5e1",
      },
    );

    expect(style.colour).toBe("#01f803");
    expect(style.edgeColour).toBe("#017a03");
  });

  it("renders stale planet dots with reduced opacity", () => {
    const style = getPlanetRenderStyle(
      { owner: "sara", scanLevel: "basic", scanAge: 2 },
      { player: "tim" },
      {
        self: "#01f803",
        selfEdge: "#017a03",
        enemy: "#ef4444",
        uncolonised: "#cbd5e1",
      },
    );

    expect(style.colour).toBe("#ef4444");
    expect(style.dotAlpha).toBe(0.5);
    expect(style.labelAlpha).toBe(0.45);
  });

  it("renders top-row map toggle buttons", () => {
    render(
      <GalaxyMap {...defaultProps} />,
    );

    const planetNamesButton = screen.getByRole("button", { name: "Show planet names" });
    const scannersButton = screen.getByRole("button", { name: "Show scanners" });

    expect(planetNamesButton).toHaveAttribute("aria-pressed", "true");
    expect(scannersButton).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(planetNamesButton);
    fireEvent.click(scannersButton);

    expect(planetNamesButton).toHaveAttribute("aria-pressed", "false");
    expect(scannersButton).toHaveAttribute("aria-pressed", "true");
  });

  it("shows a hover popover for planets", async () => {
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap {...defaultProps} />,
      );

      const canvas = document.querySelector("canvas")!;
      fireEvent.mouseMove(canvas, { clientX: 400, clientY: 300, buttons: 0 });

      await waitFor(() => {
        expect(screen.getByText("Sol")).toBeInTheDocument();
        expect(screen.getByText("Click to select")).toBeInTheDocument();
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
    }
  });

  it("hides the hover popover when leaving the map", async () => {
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap {...defaultProps} />,
      );

      const canvas = document.querySelector("canvas")!;
      fireEvent.mouseMove(canvas, { clientX: 400, clientY: 300, buttons: 0 });
      await waitFor(() => {
        expect(screen.getByText("Click to select")).toBeInTheDocument();
      });

      fireEvent.mouseLeave(canvas);
      await waitFor(() => {
        expect(screen.queryByText("Click to select")).not.toBeInTheDocument();
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
    }
  });

  it("changes the cursor to indicate a hovered planet is selectable", async () => {
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap {...defaultProps} />,
      );

      const canvas = document.querySelector("canvas")!;
      expect(canvas).toHaveClass("cursor-grab");

      fireEvent.mouseMove(canvas, { clientX: 420, clientY: 300, buttons: 0 });

      await waitFor(() => {
        expect(canvas).toHaveClass("cursor-pointer");
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
    }
  });

  it("renders a yellow starbase marker at the top right of planets with starbases", async () => {
    const ctx = createMockCanvasContext();
    const getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockReturnValue(ctx);
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap
          {...defaultProps}
          playerState={{
            ...testPlayerState,
            planets: testPlayerState.planets.map((planet) =>
              planet.id === "PL000001"
                ? {
                    ...planet,
                    starbase: { type: "space_station", canBuildShips: true },
                  }
                : planet,
            ),
          }}
        />,
      );

      await waitFor(() => {
        expect(ctx.arc).toHaveBeenCalledWith(406, 294, 2, 0, Math.PI * 2);
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
      getContextSpy.mockRestore();
    }
  });

  it("renders four inward-pointing selection chevrons around a selected planet", async () => {
    const ctx = createMockCanvasContext();
    const getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockReturnValue(ctx);
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap
          {...defaultProps}
          selection={{ kind: "planet", id: "PL000001" }}
        />,
      );

      await waitFor(() => {
        expect(ctx.arc).toHaveBeenCalledWith(400, 300, 20, expect.any(Number), expect.any(Number));
        expect(ctx.moveTo).toHaveBeenCalledWith(395, 272);
        expect(ctx.lineTo).toHaveBeenCalledWith(400, 280);
        expect(ctx.moveTo).toHaveBeenCalledWith(428, 295);
        expect(ctx.lineTo).toHaveBeenCalledWith(420, 300);
        expect(ctx.moveTo).toHaveBeenCalledWith(395, 328);
        expect(ctx.lineTo).toHaveBeenCalledWith(400, 320);
        expect(ctx.moveTo).toHaveBeenCalledWith(372, 295);
        expect(ctx.lineTo).toHaveBeenCalledWith(380, 300);
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
      getContextSpy.mockRestore();
    }
  });

  it("renders scanner overlays as separate filled shapes without an outer stroke", async () => {
    const ctx = createMockCanvasContext();
    const getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockReturnValue(ctx);
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap
          {...defaultProps}
          showScanners
          playerState={{
            ...testPlayerState,
            fleets: [
              {
                ...testPlayerState.fleets[0],
                position: { x: 500_000_001_000, y: 500_000_001_000 },
                waypoints: [],
              },
            ],
            designs: [
              {
                ...testPlayerState.designs[0],
                scanner: { normal: 150, penetrating: 75 },
              },
            ],
          }}
        />,
      );

      await waitFor(() => {
        expect(ctx.fillStyleValues).toContain("#260000");
        expect(ctx.fillStyleValues).toContain("#001a00");
      });

      expect(ctx.fill).not.toHaveBeenCalledWith("evenodd");
      expect(ctx.stroke).not.toHaveBeenCalled();
    } finally {
      getBoundingClientRectSpy.mockRestore();
      getContextSpy.mockRestore();
    }
  });

  it("brightens only the selected scout fleet's scanner circle", async () => {
    const ctx = createMockCanvasContext();
    const getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockReturnValue(ctx);
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap
          {...defaultProps}
          showScanners
          selection={{ kind: "fleet", id: "FL000001" }}
          playerState={{
            ...testPlayerState,
            fleets: [
              {
                ...testPlayerState.fleets[0],
                position: { x: 500_000_001_000, y: 500_000_001_000 },
                waypoints: [],
              },
            ],
            designs: [
              {
                ...testPlayerState.designs[0],
                scanner: { normal: 150, penetrating: 0 },
              },
            ],
          }}
        />,
      );

      await waitFor(() => {
        expect(ctx.fillStyleValues).toContain("#4a0000");
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
      getContextSpy.mockRestore();
    }
  });

  it("keeps a stationary deep-space fleet pointed along its bearing", async () => {
    const ctx = createMockCanvasContext();
    const getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockReturnValue(ctx);
    const getBoundingClientRectSpy = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    getBoundingClientRectSpy.mockReturnValue({
      x: 0,
      y: 0,
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      toJSON() {
        return {};
      },
    } as DOMRect);

    try {
      render(
        <GalaxyMap
          {...defaultProps}
          playerState={{
            ...testPlayerState,
            fleets: [
              {
                ...testPlayerState.fleets[0],
                position: { x: 500_000_001_000, y: 500_000_001_000 },
                waypoints: [],
                bearing: 180,
              },
            ],
          }}
        />,
      );

      await waitFor(() => {
        expect(ctx.rotate).toHaveBeenCalledWith(Math.PI / 2);
      });
    } finally {
      getBoundingClientRectSpy.mockRestore();
      getContextSpy.mockRestore();
    }
  });
});
