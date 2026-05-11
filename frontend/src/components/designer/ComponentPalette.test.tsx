import { DndContext } from "@dnd-kit/core";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ComponentPalette } from "./ComponentPalette";
import { colloidalPhaser, quickJump5, shield } from "./testFixtures";

describe("ComponentPalette", () => {
  it("renders component type tabs in canonical order", () => {
    render(
      <DndContext>
        <ComponentPalette components={[shield, colloidalPhaser, quickJump5]} />
      </DndContext>,
    );
    const tabs = screen.getAllByRole("tab").map((tab) => tab.textContent);
    expect(tabs).toEqual(["Engines", "Weapons", "Shields"]);
    expect(screen.getByRole("tab", { name: "Engines" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("button", { name: /Quick Jump 5/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Colloidal Phaser/i })).not.toBeInTheDocument();
  });

  it("renders mass and primary stats", () => {
    render(
      <DndContext>
        <ComponentPalette components={[quickJump5, shield]} />
      </DndContext>,
    );
    expect(screen.getByRole("button", { name: /Quick Jump 5/i }).querySelector("img")).toHaveAttribute(
      "src",
      "https://storage.googleapis.com/openstars-assets/components/engines/quick_jump_5.gif",
    );
    expect(screen.getByText("Mass 4 kt")).toBeInTheDocument();
    expect(screen.getByText(/Fuel 25\/100/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Shields" }));
    expect(screen.getByText("25 shield points")).toBeInTheDocument();
  });

  it("switches the component list when a type tab is selected", () => {
    render(
      <DndContext>
        <ComponentPalette components={[shield, colloidalPhaser, quickJump5]} />
      </DndContext>,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Weapons" }));
    expect(screen.getByRole("tab", { name: "Weapons" })).toHaveAttribute("aria-selected", "true");
    const panel = screen.getByRole("tabpanel");
    expect(within(panel).getByRole("button", { name: /Colloidal Phaser/i })).toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /Quick Jump 5/i })).not.toBeInTheDocument();
  });

  it("dims incompatible components for a slot category filter", () => {
    render(
      <DndContext>
        <ComponentPalette components={[colloidalPhaser, quickJump5]} slotCategoryFilter="weapon" />
      </DndContext>,
    );
    expect(screen.getByRole("button", { name: /Quick Jump 5/i })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    fireEvent.click(screen.getByRole("tab", { name: "Weapons" }));
    expect(screen.getByRole("button", { name: /Colloidal Phaser/i })).toHaveAttribute(
      "aria-disabled",
      "false",
    );
  });
});
