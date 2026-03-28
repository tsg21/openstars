import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { GalaxyMap } from "./GalaxyMap";
import { mockGalaxy } from "../mocks/galaxy";
import { mockPlayerState } from "../mocks/playerState";
import type { Selection } from "../types";

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
const defaultProps = {
  galaxy: mockGalaxy,
  playerState: mockPlayerState,
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
});
