import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GalaxyMap } from "./GalaxyMap";
import { mockGalaxy } from "../mocks/galaxy";
import { mockPlayerState } from "../mocks/playerState";

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

describe("GalaxyMap selection", () => {
  it("renders without crashing", () => {
    const onSelectPlanet = vi.fn();
    render(
      <GalaxyMap
        galaxy={mockGalaxy}
        playerState={mockPlayerState}
        selectedPlanetId={null}
        onSelectPlanet={onSelectPlanet}
      />,
    );
    // Canvas should exist
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeTruthy();
  });

  it("calls onSelectPlanet(null) when clicking empty space", () => {
    const onSelectPlanet = vi.fn();
    render(
      <GalaxyMap
        galaxy={mockGalaxy}
        playerState={mockPlayerState}
        selectedPlanetId={null}
        onSelectPlanet={onSelectPlanet}
      />,
    );

    const canvas = document.querySelector("canvas")!;

    // Simulate a click on far-away empty space (no planet near (0,0) in screen coords with default viewport)
    fireEvent.mouseDown(canvas, { clientX: 0, clientY: 0, button: 0 });
    fireEvent.mouseUp(canvas, { clientX: 0, clientY: 0 });

    expect(onSelectPlanet).toHaveBeenCalledWith(null);
  });

  it("deselects on Escape key", () => {
    const onSelectPlanet = vi.fn();
    render(
      <GalaxyMap
        galaxy={mockGalaxy}
        playerState={mockPlayerState}
        selectedPlanetId="PLk8m3x2"
        onSelectPlanet={onSelectPlanet}
      />,
    );

    const container = document.querySelector("[tabindex]")!;
    fireEvent.keyDown(container, { key: "Escape" });

    expect(onSelectPlanet).toHaveBeenCalledWith(null);
  });

  it("does not fire selection on drag (mouse moved)", () => {
    const onSelectPlanet = vi.fn();
    render(
      <GalaxyMap
        galaxy={mockGalaxy}
        playerState={mockPlayerState}
        selectedPlanetId={null}
        onSelectPlanet={onSelectPlanet}
      />,
    );

    const canvas = document.querySelector("canvas")!;

    // Simulate a drag (mouse moves > 3px)
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100, button: 0 });
    fireEvent.mouseMove(canvas, { clientX: 120, clientY: 120 });
    fireEvent.mouseUp(canvas, { clientX: 120, clientY: 120 });

    expect(onSelectPlanet).not.toHaveBeenCalled();
  });
});
