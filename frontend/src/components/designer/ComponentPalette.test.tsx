import { DndContext } from "@dnd-kit/core";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ComponentPalette } from "./ComponentPalette";
import { colloidalPhaser, quickJump5, shield } from "./testFixtures";

describe("ComponentPalette", () => {
  it("groups components by canonical type order", () => {
    render(
      <DndContext>
        <ComponentPalette components={[shield, colloidalPhaser, quickJump5]} />
      </DndContext>,
    );
    const headings = screen.getAllByRole("heading", { level: 4 }).map((heading) => heading.textContent);
    expect(headings).toEqual(["engine", "weapon", "shield"]);
  });

  it("renders mass and primary stats", () => {
    render(
      <DndContext>
        <ComponentPalette components={[quickJump5, shield]} />
      </DndContext>,
    );
    expect(screen.getByText("Mass 4 kt")).toBeInTheDocument();
    expect(screen.getByText(/Fuel 25\/100/)).toBeInTheDocument();
    expect(screen.getByText("25 shield points")).toBeInTheDocument();
  });

  it("dims incompatible components for a slot category filter", () => {
    render(
      <DndContext>
        <ComponentPalette components={[quickJump5, colloidalPhaser]} slotCategoryFilter="weapon" />
      </DndContext>,
    );
    expect(screen.getByRole("button", { name: /Colloidal Phaser/i })).toHaveAttribute(
      "aria-disabled",
      "false",
    );
    expect(screen.getByRole("button", { name: /Quick Jump 5/i })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });
});
