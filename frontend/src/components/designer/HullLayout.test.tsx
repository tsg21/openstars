import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HullLayout } from "./HullLayout";
import { makeHull } from "./testFixtures";

describe("HullLayout", () => {
  it("renders slot cells with category labels", () => {
    render(<HullLayout hull={makeHull()} />);
    expect(screen.getAllByTestId(/hull-slot-/)).toHaveLength(3);
    expect(screen.getByText("Eng")).toBeInTheDocument();
    expect(screen.getByText("Scn/Elec/Mech")).toBeInTheDocument();
  });

  it("renders slots as 2x2 cells by default", () => {
    const hull = makeHull({
      layoutGrid: { w: 4, h: 4 },
      slots: [
        {
          slotNumber: 1,
          slotCategories: ["engine"],
          capacity: 1,
          required: true,
          position: { x: 2, y: 1 },
        },
      ],
    });
    render(<HullLayout hull={hull} />);
    const slot = screen.getByTestId("hull-slot-1");
    expect(slot).toHaveAttribute("data-grid-pos", "2,1,2,2");
    expect(slot).toHaveStyle({ gridColumn: "3 / span 2", gridRow: "2 / span 2" });
  });

  it("renders cargo and dock layout rectangles", () => {
    render(
      <HullLayout
        hull={makeHull({
          dockCapacity: 200,
          dockLayout: { x: 4, y: 0, w: 2, h: 2 },
        })}
      />,
    );
    expect(screen.getByTestId("hull-cargo-layout")).toHaveTextContent("Cargo 70 kt");
    expect(screen.getByTestId("hull-dock-layout")).toHaveTextContent("Dock 200 kt");
  });
});
