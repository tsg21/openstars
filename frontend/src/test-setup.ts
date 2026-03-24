import "@testing-library/jest-dom";

// Polyfill ResizeObserver for jsdom (used by GalaxyMap canvas)
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof globalThis.ResizeObserver;
}
