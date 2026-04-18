import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TopBar } from "./TopBar";

describe("TopBar", () => {
  it("shows a pulsing wait message while waiting for the next turn", () => {
    render(
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
      />,
    );

    const status = screen.getByText("Waiting for the next turn");
    expect(status).toHaveClass("animate-pulse");
  });

  it("shows the brand, game name, and integrated view selector", () => {
    render(
      <TopBar
        gameName="Andromeda"
        turn={4}
        isDirty
        submitted={false}
        waitingForNextTurn={false}
        mode="designer"
        onModeChange={vi.fn()}
        onSubmit={vi.fn()}
        submissionStatus="Waiting: 0 of 2 submitted"
        allSubmitted={false}
        onResolve={vi.fn()}
        onLeave={vi.fn()}
        playerName="tim"
        error={null}
      />,
    );

    expect(screen.getByText("OpenStars!")).toBeInTheDocument();
    expect(screen.getByText("Andromeda")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Command*" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Designer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lobby" })).toBeInTheDocument();
  });
});
