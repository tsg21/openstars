import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FleetComposer } from "./FleetComposer";
import { GameCommandsContext } from "../contexts/gameCommandsContext";

const fleets = [
  {
    id: "FL1",
    owner: "tim",
    name: "Fleet 1",
    position: { x: 0, y: 0 },
    composition: [{ designId: "D1", count: 2 }],
  },
  {
    id: "FL2",
    owner: "tim",
    name: "Fleet 2",
    position: { x: 0, y: 0 },
    composition: [{ designId: "D1", count: 1 }],
  },
];

function renderComposer(addCommand = vi.fn()) {
  return render(
    <GameCommandsContext.Provider
      value={{
        basePlayerState: null,
        addCommand,
        replaceCommands: vi.fn(),
        nextTmpFleetId: vi.fn(() => "tmp_1"),
      }}
    >
      <FleetComposer fleets={fleets} designs={[]} onClose={vi.fn()} />
    </GameCommandsContext.Provider>,
  );
}

describe("FleetComposer", () => {
  it("renders rows from fleet composition", () => {
    renderComposer();
    expect(screen.getByText("D1")).toBeInTheDocument();
  });

  it("Apply disabled when row totals invalid", () => {
    renderComposer();
    fireEvent.change(screen.getByLabelText("cell-0-0"), { target: { value: "0" } });
    expect(screen.getByRole("button", { name: "Apply Changes" })).toBeDisabled();
  });

  it("Merge All sets all ships in left column", () => {
    renderComposer();
    fireEvent.click(screen.getByRole("button", { name: "Merge All" }));
    expect((screen.getByLabelText("cell-0-0") as HTMLInputElement).value).toBe("3");
    expect((screen.getByLabelText("cell-0-1") as HTMLInputElement).value).toBe("0");
  });

  it("+ New Fleet adds a new column", () => {
    renderComposer();
    fireEvent.click(screen.getByRole("button", { name: "+ New Fleet" }));
    expect(screen.getByLabelText("Fleet name 3")).toBeInTheDocument();
  });

  it("Apply emits merge_split_fleets command", () => {
    const addCommand = vi.fn();
    renderComposer(addCommand);
    fireEvent.click(screen.getByRole("button", { name: "Apply Changes" }));
    expect(addCommand).toHaveBeenCalledWith(expect.objectContaining({ type: "merge_split_fleets" }));
  });
});
