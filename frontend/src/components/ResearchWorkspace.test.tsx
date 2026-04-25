import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResearchWorkspace } from "./ResearchWorkspace";
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

describe("ResearchWorkspace", () => {
  it("renders as an in-flow workspace", () => {
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={1} ownedPlanetsCount={3} pendingCommand={null} onChange={vi.fn()} />);
    expect(screen.getByText("Research")).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Close research dialog")).not.toBeInTheDocument();
  });

  it("does not render manual apply or cancel buttons", () => {
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={vi.fn()} />);
    expect(screen.queryByRole("button", { name: "Apply" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument();
  });

  it("auto-saves changed fields only", () => {
    const onChange = vi.fn();
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Current field"), { target: { value: "construction" } });
    expect(onChange).toHaveBeenCalledWith({ type: "set_research", currentField: "construction" });
  });

  it("auto-clears the pending command when the controls return to committed state", () => {
    const onChange = vi.fn();
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Current field"), { target: { value: "construction" } });
    fireEvent.change(screen.getByLabelText("Current field"), { target: { value: "energy" } });
    expect(onChange).toHaveBeenLastCalledWith(null);
  });

  it("increments and decrements allocation with visible stepper buttons", () => {
    const onChange = vi.fn();
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={onChange} />);
    const input = screen.getByLabelText("Allocation percent");
    fireEvent.click(screen.getByRole("button", { name: "Increase allocation" }));
    expect(input).toHaveValue(16);
    expect(onChange).toHaveBeenCalledWith({ type: "set_research", allocationPercent: 16 });
    fireEvent.click(screen.getByRole("button", { name: "Decrease allocation" }));
    expect(input).toHaveValue(15);
    expect(onChange).toHaveBeenLastCalledWith(null);
  });

  it("shows the reserved resources estimate in the bottom summary", () => {
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={vi.fn()} />);
    expect(screen.getByText(/Reserved this turn:/)).toHaveTextContent("≈ 30 resources");
  });

  it("renders field levels as bold pills beside the field labels", () => {
    render(<ResearchWorkspace research={research} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={vi.fn()} />);
    const energyRow = screen.getByTestId("research-row-energy");
    const levelPill = within(energyRow).getByText("3");
    expect(levelPill).toHaveClass("font-bold");
    expect(levelPill).toHaveStyle({ color: "#fbbf24" });
  });

  it("handles number clamp and no reservable resources", () => {
    render(<ResearchWorkspace research={{ ...research, reservableResourcesThisTurn: 0 }} ownedPlanetsLeftoverOnlyCount={0} ownedPlanetsCount={2} pendingCommand={null} onChange={vi.fn()} />);
    expect(screen.getByText(/no reservable resources/)).toBeInTheDocument();
    const input = screen.getByLabelText("Allocation percent");
    fireEvent.change(input, { target: { value: "150" } });
    fireEvent.blur(input);
    expect(input).toHaveValue(100);
  });
});
