import { describe, expect, it } from "vitest";

import type { GameEvent } from "../types";
import { formatEventMessage } from "./eventMessages";

describe("eventMessages", () => {
  it("replaces positional inserts in known templates", () => {
    const event: GameEvent = {
      owner: "tim",
      sourceId: "PL000001",
      code: "production.completed",
      values: [2, "mine", "Sol"],
    };

    expect(formatEventMessage(event)).toBe("Completed 2 mine(s) at Sol");
  });

  it("falls back to a generic message for unknown codes", () => {
    const event: GameEvent = {
      owner: "tim",
      sourceId: null,
      code: "future.something_new",
      values: [],
    };

    expect(formatEventMessage(event)).toBe("Event: future.something_new");
  });

  it("formats colonisation events", () => {
    const event: GameEvent = {
      owner: "tim",
      sourceId: "PL000001",
      code: "colonisation.colonised",
      values: ["Colony Ship", "Proxima", 2500, 1, 1, 5],
    };

    expect(formatEventMessage(event)).toBe("Colony Ship colonised Proxima with 2500 colonists");
  });
});
