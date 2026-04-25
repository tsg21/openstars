import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResearchDialog } from "./ResearchDialog";
import type { PlayerStateResearch } from "../types";

const research: PlayerStateResearch = {
  levels: { energy: 3, weapons: 1, propulsion: 26, construction: 2, electronics: 0, biotechnology: 0 },
  progress: { energy: 20, weapons: 10, propulsion: 0, construction: 0, electronics: 0, biotechnology: 0 },
  currentField: "energy",
  nextField: "weapons",
  allocationPercent: 15,
  remainingCost: { energy: 80, weapons: 90, propulsion: 0, construction: 100, electronics: 100, biotechnology: 100 },
  reservableResourcesThisTurn: 200,
};

describe("ResearchDialog", () => {
  it("renders and closes via backdrop/escape", () => {
    const onClose = vi.fn();
    render(<ResearchDialog open onClose={onClose} research={research} ownedPlanetsLeftoverOnlyCount={1} ownedPlanetsCount={3} pendingCommand={null} onApply={vi.fn()} />);
    expect(screen.getByText("Research")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("apply is disabled until edited", () => {
    render(<ResearchDialog open onClose={vi.fn()} research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onApply={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Apply" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Allocation percent"), { target: { value: "60" } });
    fireEvent.blur(screen.getByLabelText("Allocation percent"));
    expect(screen.getByRole("button", { name: "Apply" })).toBeEnabled();
  });

  it("applies changed fields only", () => {
    const onApply = vi.fn();
    render(<ResearchDialog open onClose={vi.fn()} research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onApply={onApply} />);
    fireEvent.change(screen.getByLabelText("Current field"), { target: { value: "construction" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(onApply).toHaveBeenCalledWith({ type: "set_research", currentField: "construction" });
  });

  it("handles slider/number clamp and no reservable resources", () => {
    render(<ResearchDialog open onClose={vi.fn()} research={{ ...research, reservableResourcesThisTurn: 0 }} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onApply={vi.fn()} />);
    expect(screen.getByText("— (no reservable resources)")).toBeInTheDocument();
    const input = screen.getByLabelText("Allocation percent");
    fireEvent.change(input, { target: { value: "150" } });
    fireEvent.blur(input);
    expect(input).toHaveValue(100);
  });
});
