import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TopBar } from "./TopBar";

describe("TopBar", () => {
  it("shows a pulsing wait message while waiting for the next turn", () => {
    render(
      <TopBar
        gameName="OpenStars!"
        turn={4}
        isDirty={false}
        submitted
        waitingForNextTurn
        onSubmit={vi.fn()}
        submissionStatus="Waiting for the next turn"
        allSubmitted={false}
        onResolve={vi.fn()}
        onLeave={vi.fn()}
        playerName="tim"
        error={null}
      />,
    );

    const status = screen.getByText("Waiting for the next turn");
    expect(status).toHaveClass("animate-pulse");
  });
});
