import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TopBar } from "./TopBar";
import type { PlayerStateResearch } from "../types";

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

function renderTopBar(research: PlayerStateResearch | null, onOpenResearch = vi.fn()) {
  return render(
    <TopBar
      gameName="Andromeda"
      turn={4}
      isDirty={false}
      submitted
      waitingForNextTurn
      mode="command"
      onModeChange={vi.fn()}
      onSubmit={vi.fn()}
      submissionStatus="Waiting for the next turn"
      allSubmitted={false}
      onResolve={vi.fn()}
      onLeave={vi.fn()}
      playerName="tim"
      error={null}
      research={research}
      onOpenResearch={onOpenResearch}
    />,
  );
}

describe("TopBar", () => {
  it("shows a pulsing wait message while waiting for the next turn", () => {
    renderTopBar(baseResearch);
    const status = screen.getByText("Waiting for the next turn");
    expect(status).toHaveClass("animate-pulse");
  });

  it("renders research label, level, and percent", () => {
    renderTopBar(baseResearch);
    expect(screen.getByRole("button", { name: /Energy · lvl 3 · 20% → lvl 4/i })).toBeInTheDocument();
  });

  it("renders MAX with no percent at level cap", () => {
    renderTopBar({
      ...baseResearch,
      levels: { ...baseResearch.levels, energy: 26 },
      remainingCost: { ...baseResearch.remainingCost, energy: 0 },
    });

    expect(screen.getByRole("button", { name: /Energy · lvl 26 · MAX/i })).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("shows paused and dimmed when allocation is zero", () => {
    renderTopBar({ ...baseResearch, allocationPercent: 0 });
    expect(screen.getByText("paused")).toBeInTheDocument();
  });

  it("hides research indicator when research is null", () => {
    renderTopBar(null);
    expect(screen.queryByText(/lvl/)).not.toBeInTheDocument();
  });

  it("clicking indicator calls onOpenResearch", () => {
    const onOpenResearch = vi.fn();
    renderTopBar(baseResearch, onOpenResearch);
    fireEvent.click(screen.getByRole("button", { name: /Energy · lvl 3/i }));
    expect(onOpenResearch).toHaveBeenCalledTimes(1);
  });
});
