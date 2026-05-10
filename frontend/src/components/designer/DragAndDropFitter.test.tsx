import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  applyComponentToFitState,
  computeDesignValidationErrors,
} from "../../lib/designerFit";
import { DragAndDropFitter } from "./DragAndDropFitter";
import { colloidalPhaser, laser, makeCruiser, quickJump5 } from "./testFixtures";

const components = [quickJump5, colloidalPhaser, laser];

describe("DragAndDropFitter", () => {
  it("applies a compatible component to a slot", () => {
    const result = applyComponentToFitState({
      hull: makeCruiser(),
      components,
      fitState: new Map(),
      slotNumber: 4,
      componentId: "colloidal_phaser",
    });
    expect(result.rejected).toBe(false);
    expect(result.fitState.get(4)).toEqual({
      componentId: "colloidal_phaser",
      componentCount: 1,
    });
  });

  it("rejects incompatible drops", () => {
    const fitState = new Map();
    const result = applyComponentToFitState({
      hull: makeCruiser(),
      components,
      fitState,
      slotNumber: 1,
      componentId: "colloidal_phaser",
    });
    expect(result.rejected).toBe(true);
    expect(result.fitState).toBe(fitState);
  });

  it("caps repeated drops at slot capacity", () => {
    let fitState = new Map([[4, { componentId: "colloidal_phaser", componentCount: 2 }]]);
    fitState = applyComponentToFitState({
      hull: makeCruiser(),
      components,
      fitState,
      slotNumber: 4,
      componentId: "colloidal_phaser",
    }).fitState;
    expect(fitState.get(4)?.componentCount).toBe(2);
  });

  it("replaces an occupied slot with another compatible component", () => {
    const result = applyComponentToFitState({
      hull: makeCruiser(),
      components,
      fitState: new Map([[4, { componentId: "colloidal_phaser", componentCount: 1 }]]),
      slotNumber: 4,
      componentId: "laser",
    });
    expect(result.replaced).toBe(true);
    expect(result.fitState.get(4)).toEqual({ componentId: "laser", componentCount: 1 });
  });

  it("adds the selected palette component to a focused slot via keyboard", () => {
    const onChange = vi.fn();
    render(
      <DragAndDropFitter
        hull={makeCruiser()}
        components={components}
        value={new Map()}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Weapons" }));
    fireEvent.click(screen.getByRole("button", { name: /Colloidal Phaser/i }));
    fireEvent.keyDown(screen.getByRole("button", { name: "Weapon fitting cell" }), {
      key: "Enter",
    });
    expect(onChange).toHaveBeenCalledWith(
      new Map([[4, { componentId: "colloidal_phaser", componentCount: 1 }]]),
    );
  });

  it("shows a fitted component image in the slot without empty text or component name", () => {
    render(
      <DragAndDropFitter
        hull={makeCruiser()}
        components={components}
        value={new Map([[1, { componentId: "quick_jump_5", componentCount: 1 }]])}
        onChange={vi.fn()}
      />,
    );
    const slot = screen.getByTestId("hull-slot-1");
    expect(slot.querySelector("img")).toHaveAttribute(
      "src",
      "https://storage.googleapis.com/openstars-assets/components/engines/quick_jump_5.gif",
    );
    expect(within(slot).queryByText("Empty")).not.toBeInTheDocument();
    expect(within(slot).queryByText("Quick Jump 5")).not.toBeInTheDocument();
  });
});

describe("computeDesignValidationErrors", () => {
  it("reports missing and partially filled required engine slots", () => {
    const hull = makeCruiser();
    expect(computeDesignValidationErrors(hull, new Map())).toContain(
      "Slot 1 (Engine) needs 2 engines",
    );
    expect(
      computeDesignValidationErrors(
        hull,
        new Map([[1, { componentId: "quick_jump_5", componentCount: 1 }]]),
      ),
    ).toContain("Slot 1 (Engine) needs 2 engines");
  });

  it("returns zero errors when required slots are full", () => {
    expect(
      computeDesignValidationErrors(
        makeCruiser(),
        new Map([[1, { componentId: "quick_jump_5", componentCount: 2 }]]),
      ),
    ).toEqual([]);
  });
});
