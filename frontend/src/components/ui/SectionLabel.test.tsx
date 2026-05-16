import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SectionLabel } from "./SectionLabel";

describe("SectionLabel", () => {
  it("renders children", () => {
    render(<SectionLabel>Planet</SectionLabel>);
    expect(screen.getByText("Planet")).toBeInTheDocument();
  });

  it("applies base classes", () => {
    render(<SectionLabel>Starbase</SectionLabel>);
    const el = screen.getByText("Starbase");
    expect(el.className).toContain("uppercase");
    expect(el.className).toContain("tracking-widest");
    expect(el.className).toContain("text-muted-foreground");
  });

  it("merges extra className for size overrides", () => {
    render(<SectionLabel className="text-[10px]">Research</SectionLabel>);
    expect(screen.getByText("Research").className).toContain("text-[10px]");
  });

  it("renders as a different element via as prop", () => {
    render(<SectionLabel as="span">Fleets</SectionLabel>);
    const el = screen.getByText("Fleets");
    expect(el.tagName).toBe("SPAN");
  });
});
