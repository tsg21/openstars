import "@testing-library/jest-dom";

// Polyfill ResizeObserver for jsdom (used by GalaxyMap canvas)
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof globalThis.ResizeObserver;
}

HTMLCanvasElement.prototype.getContext = ((() =>
  ({
    scale() {},
    clearRect() {},
    fillText() {},
    beginPath() {},
    roundRect() {},
    fill() {},
    set font(_value: string) {},
    set fillStyle(_value: string) {},
    set textBaseline(_value: CanvasTextBaseline) {},
    set textAlign(_value: CanvasTextAlign) {},
  }) as unknown as CanvasRenderingContext2D) as unknown) as typeof HTMLCanvasElement.prototype.getContext;
