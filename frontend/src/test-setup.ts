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
    save() {},
    restore() {},
    scale() {},
    translate() {},
    rotate() {},
    clearRect() {},
    fillRect() {},
    fillText() {},
    beginPath() {},
    closePath() {},
    roundRect() {},
    fill() {},
    arc() {},
    stroke() {},
    moveTo() {},
    lineTo() {},
    setLineDash() {},
    createRadialGradient() {
      return {
        addColorStop() {},
      } as CanvasGradient;
    },
    set font(_value: string) {},
    set fillStyle(_value: string) {},
    set strokeStyle(_value: string) {},
    set lineWidth(_value: number) {},
    set globalAlpha(_value: number) {},
    set textBaseline(_value: CanvasTextBaseline) {},
    set textAlign(_value: CanvasTextAlign) {},
  }) as unknown as CanvasRenderingContext2D) as unknown) as typeof HTMLCanvasElement.prototype.getContext;
