import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { EventLog } from "./EventLog";
import type { GameEvent, Galaxy } from "../../types";

const galaxy: Galaxy = {
  galaxy: { name: "Test", size: "small", seed: 42 },
  planets: [{ id: "PL000001", name: "Sol", x: 100, y: 200 }],
};

describe("EventLog", () => {
  it("renders formatted event text from code and values", () => {
    const events: GameEvent[] = [
      {
        owner: "tim",
        sourceId: "PL000001",
        code: "production.completed",
        values: [1, "mine", "Sol"],
      },
    ];

    render(
      <EventLog
        collapsed={false}
        onToggle={vi.fn()}
        events={events}
        galaxy={galaxy}
        onEventClick={vi.fn()}
      />,
    );

    expect(screen.getByText("Completed 1 mine(s) at Sol")).toBeInTheDocument();
  });

  it("uses unknown-code fallback text", () => {
    const events: GameEvent[] = [
      {
        owner: "tim",
        sourceId: null,
        code: "future.unknown_code",
        values: [],
      },
    ];

    render(
      <EventLog
        collapsed={false}
        onToggle={vi.fn()}
        events={events}
        galaxy={galaxy}
        onEventClick={vi.fn()}
      />,
    );

    expect(screen.getByText("Event: future.unknown_code")).toBeInTheDocument();
  });

  it("centres map when clicking event with sourceId", () => {
    const onEventClick = vi.fn();
    const events: GameEvent[] = [
      {
        owner: "tim",
        sourceId: "PL000001",
        code: "production.completed",
        values: [1, "mine", "Sol"],
      },
    ];

    render(
      <EventLog
        collapsed={false}
        onToggle={vi.fn()}
        events={events}
        galaxy={galaxy}
        onEventClick={onEventClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Completed 1 mine\(s\) at Sol/ }));
    expect(onEventClick).toHaveBeenCalledWith(100, 200);
  });
});
