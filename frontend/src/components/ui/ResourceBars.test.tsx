import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResourceBars } from "./ResourceBars";

function createMockCanvasContext() {
  let currentFillStyle: string | CanvasGradient | CanvasPattern = "";

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
    createRadialGradient: vi.fn(() => ({
      addColorStop() {},
    })),
    get fillStyle() {
      return currentFillStyle;
    },
    set fillStyle(value: string | CanvasGradient | CanvasPattern) {
      currentFillStyle = value;
    },
    set font(_value: string) {},
    set strokeStyle(_value: string) {},
    set lineWidth(_value: number) {},
    set globalAlpha(_value: number) {},
    set textBaseline(_value: CanvasTextBaseline) {},
    set textAlign(_value: CanvasTextAlign) {},
  } as unknown as CanvasRenderingContext2D & {
    moveTo: ReturnType<typeof vi.fn>;
    lineTo: ReturnType<typeof vi.fn>;
  };
}

describe("ResourceBars", () => {
  it("renders concentration diamonds on the bars and removes the concentration footer text", async () => {
    const ctx = createMockCanvasContext();
    const getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockReturnValue(ctx);
    const offsetWidthDescriptor = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, "offsetWidth");
    const offsetHeightDescriptor = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, "offsetHeight");
    Object.defineProperty(HTMLCanvasElement.prototype, "offsetWidth", {
      configurable: true,
      get() {
        return 320;
      },
    });
    Object.defineProperty(HTMLCanvasElement.prototype, "offsetHeight", {
      configurable: true,
      get() {
        return 66;
      },
    });

    try {
      render(
        <ResourceBars
          minerals={{ ironium: 300, boranium: 250, germanium: 200 }}
          miningRate={{ ironium: 10, boranium: 9, germanium: 8 }}
          concentrations={{ ironium: 0, boranium: 100, germanium: 200 }}
        />,
      );

      expect(screen.queryByText(/conc:/i)).not.toBeInTheDocument();

      await waitFor(() => {
        expect(ctx.moveTo).toHaveBeenCalledWith(72, 7);
        expect(ctx.moveTo).toHaveBeenCalledWith(162, 29);
        expect(ctx.moveTo).toHaveBeenCalledWith(252, 51);
      });
    } finally {
      if (offsetWidthDescriptor) {
        Object.defineProperty(HTMLCanvasElement.prototype, "offsetWidth", offsetWidthDescriptor);
      }
      if (offsetHeightDescriptor) {
        Object.defineProperty(HTMLCanvasElement.prototype, "offsetHeight", offsetHeightDescriptor);
      }
      getContextSpy.mockRestore();
    }
  });
});
