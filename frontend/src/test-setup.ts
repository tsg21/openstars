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
    arc() {},
    stroke() {},
    moveTo() {},
    lineTo() {},
    set font(_value: string) {},
    set fillStyle(_value: string) {},
    set strokeStyle(_value: string) {},
    set lineWidth(_value: number) {},
    set textBaseline(_value: CanvasTextBaseline) {},
    set textAlign(_value: CanvasTextAlign) {},
  }) as unknown as CanvasRenderingContext2D) as unknown) as typeof HTMLCanvasElement.prototype.getContext;
