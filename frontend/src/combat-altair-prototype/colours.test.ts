import { describe, expect, it } from "vitest";

import { brightenColour, intensifyColour, ownerBeamColour, ownerColour } from "./colours";

describe("ownerColour", () => {
  it("returns stable palette colours for known owners", () => {
    expect(ownerColour("alice")).toBe("hsl(213 91% 67%)");
    expect(ownerColour("bob")).toBe("hsl(0 91% 71%)");
  });

  it("derives a deterministic fallback colour for unknown owners", () => {
    expect(ownerColour("zephyrus")).toBe("hsl(178 70% 60%)");
  });
});

describe("brightenColour", () => {
  it("keeps hue and saturation while increasing lightness", () => {
    expect(brightenColour("hsl(211 70% 60%)")).toBe("hsl(211 70% 78%)");
  });

  it("caps the brightened lightness", () => {
    expect(brightenColour("hsl(43 96% 84%)")).toBe("hsl(43 96% 92%)");
  });
});

describe("intensifyColour", () => {
  it("increases saturation as well as lightness", () => {
    expect(intensifyColour("hsl(211 70% 60%)")).toBe("hsl(211 88% 68%)");
  });

  it("caps the intensified saturation and lightness", () => {
    expect(intensifyColour("hsl(43 96% 76%)")).toBe("hsl(43 100% 78%)");
  });

  it("builds a more intense beam colour from the owner palette", () => {
    expect(ownerBeamColour("charlie")).toBe("hsl(158 82% 60%)");
  });
});
