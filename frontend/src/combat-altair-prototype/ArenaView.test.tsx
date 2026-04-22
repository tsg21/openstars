import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ArenaView } from "./ArenaView";
import type { FrameState } from "./types";

function makeFrame(): FrameState {
  return {
    eventIndex: 0,
    roundIndex: 0,
    tickIndex: 0,
    tokens: [
      { id: "a1", owner: "alice", x: 100, y: 200, hp: 30, alive: true },
      { id: "b1", owner: "bob", x: 400, y: 200, hp: 30, alive: true },
    ],
    lastShotEvents: [
      {
        type: "weapon_fired",
        attackerId: "a1",
        targetId: "b1",
        damage: 30,
        hit: true,
        roundIndex: 0,
      },
    ],
  };
}

describe("ArenaView", () => {
  it("renders weapon beams below ship hulls and token labels", () => {
    render(<ArenaView frame={makeFrame()} arenaSize={1000} />);

    const hulls = screen.getByTestId("token-hulls");
    const beams = screen.getByTestId("weapon-beams");
    const labels = screen.getByTestId("token-labels");

    expect(beams.compareDocumentPosition(hulls) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(hulls.compareDocumentPosition(labels) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
