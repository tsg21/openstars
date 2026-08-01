import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TopBar } from "./TopBar";
import type { PlayerStateResearch } from "../../types";

const baseResearch: PlayerStateResearch = {
  levels: {
    energy: 3,
    weapons: 2,
    propulsion: 1,
    construction: 0,
    electronics: 0,
    biotechnology: 0,
  },
  progress: {
    energy: 20,
    weapons: 0,
    propulsion: 0,
    construction: 0,
    electronics: 0,
    biotechnology: 0,
  },
  currentField: "energy",
  nextField: "weapons",
  allocationPercent: 15,
  remainingCost: {
    energy: 80,
    weapons: 100,
    propulsion: 100,
    construction: 100,
    electronics: 100,
    biotechnology: 100,
  },
  reservableResourcesThisTurn: 200,
};

function renderTopBar(
  research: PlayerStateResearch | null,
  onModeChange = vi.fn(),
  mode: "command" | "production" | "designer" | "research" = "command",
  extra: { productionEnabled?: boolean; raceSelectionActive?: boolean } = {},
) {
  return render(
    <TopBar
      gameName="Andromeda"
      turn={4}
      waitingForNextTurn
      mode={mode}
      onModeChange={onModeChange}
      onSubmit={vi.fn()}
      submissionStatus="Waiting for the next turn"
      onLeave={vi.fn()}
      playerName="tim"
      error={null}
      research={research}
      productionEnabled={extra.productionEnabled ?? true}
      raceSelectionActive={extra.raceSelectionActive ?? false}
    />,
  );
}

describe("TopBar", () => {
  it("shows a pulsing wait message while waiting for the next turn", () => {
    renderTopBar(baseResearch);
    const status = screen.getByText("Waiting for the next turn");
    expect(status).toHaveClass("animate-pulse");
  });

  it("renders research as a top-left tab", () => {
    renderTopBar(baseResearch);
    expect(screen.getByRole("button", { name: "Research" })).toBeInTheDocument();
  });

  it("does not render the old top-right research readout", () => {
    renderTopBar({
      ...baseResearch,
      levels: { ...baseResearch.levels, energy: 26 },
      remainingCost: { ...baseResearch.remainingCost, energy: 0 },
    });

    expect(screen.queryByText(/Energy · lvl 26 · MAX/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("does not add paused text to the research tab", () => {
    renderTopBar({ ...baseResearch, allocationPercent: 0 });
    expect(screen.getByRole("button", { name: "Research" })).toBeInTheDocument();
    expect(screen.queryByText("paused")).not.toBeInTheDocument();
  });

  it("hides research tab when research is null", () => {
    renderTopBar(null);
    expect(screen.queryByRole("button", { name: "Research" })).not.toBeInTheDocument();
  });

  it("clicking the research tab changes mode to research", () => {
    const onModeChange = vi.fn();
    renderTopBar(baseResearch, onModeChange);
    fireEvent.click(screen.getByRole("button", { name: "Research" }));
    expect(onModeChange).toHaveBeenCalledWith("research");
  });

  it("shows the research tab as selected while research mode is active", () => {
    renderTopBar(baseResearch, vi.fn(), "research");
    expect(screen.getByRole("button", { name: "Research" })).toHaveClass("text-white");
    expect(screen.getByRole("button", { name: "Command" })).toHaveClass("text-muted-foreground");
  });

  it("renders Production tab between Command and Designer", () => {
    renderTopBar(null);
    const buttons = screen.getAllByRole("button");
    const names = buttons.map((b) => b.textContent);
    const cmdIdx = names.indexOf("Command");
    const prodIdx = names.indexOf("Production");
    const desIdx = names.indexOf("Designer");
    expect(prodIdx).toBeGreaterThan(cmdIdx);
    expect(prodIdx).toBeLessThan(desIdx);
  });

  it("clicking Production tab calls onModeChange('production')", () => {
    const onModeChange = vi.fn();
    renderTopBar(null, onModeChange);
    fireEvent.click(screen.getByRole("button", { name: "Production" }));
    expect(onModeChange).toHaveBeenCalledWith("production");
  });

  it("Production tab is disabled when productionEnabled is false", () => {
    const onModeChange = vi.fn();
    renderTopBar(null, onModeChange, "command", { productionEnabled: false });
    const btn = screen.getByRole("button", { name: "Production" });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(onModeChange).not.toHaveBeenCalled();
  });

  it("Production tab shows primary variant when mode is production", () => {
    renderTopBar(null, vi.fn(), "production");
    expect(screen.getByRole("button", { name: "Production" })).toHaveClass("text-white");
    expect(screen.getByRole("button", { name: "Command" })).toHaveClass("text-muted-foreground");
  });

  it("hides Production tab during race selection", () => {
    renderTopBar(null, vi.fn(), "command", { raceSelectionActive: true });
    expect(screen.queryByRole("button", { name: "Production" })).not.toBeInTheDocument();
  });
});
