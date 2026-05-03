import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RaceSelectionScreen } from "./RaceSelectionScreen";
import { DEFAULT_RACE, type RaceCostBreakdown } from "../types";
import { GameCommandsContext } from "../contexts/gameCommandsContext";

const apiMocks = vi.hoisted(() => ({
  getPredefinedRaces: vi.fn(),
  getRace: vi.fn(),
  previewRace: vi.fn(),
  submitCommands: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    code: string;

    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
    }
  },
}));

vi.mock("../api/client", () => apiMocks);

const costBreakdown: RaceCostBreakdown = {
  prt: 0,
  lrts: 0,
  habitability: 0,
  growth: 0,
  economy: 0,
  research: 0,
  leftover: 0,
  total: 0,
  pointsLeft: 1650,
};

function renderScreen(replaceCommands = vi.fn()) {
  return render(
    <GameCommandsContext.Provider
      value={{
        basePlayerState: null,
        addCommand: vi.fn(),
        replaceCommands,
        nextTmpFleetId: vi.fn(() => "tmp_1"),
      }}
    >
      <RaceSelectionScreen
        gameId="game-1"
        player="alice"
      />
    </GameCommandsContext.Provider>,
  );
}

async function finishInitialLoad() {
  await screen.findByText("Race Points");
  await waitFor(() => {
    expect(apiMocks.previewRace).toHaveBeenCalled();
  });
  apiMocks.previewRace.mockClear();
}

describe("RaceSelectionScreen", () => {
  beforeEach(() => {
    apiMocks.getPredefinedRaces.mockReset();
    apiMocks.getRace.mockReset();
    apiMocks.previewRace.mockReset();
    apiMocks.submitCommands.mockReset();

    apiMocks.getPredefinedRaces.mockResolvedValue([
      { id: "humanoid", race: DEFAULT_RACE },
    ]);
    apiMocks.getRace.mockResolvedValue({ race: null, costBreakdown: null });
    apiMocks.previewRace.mockResolvedValue({ costBreakdown, pointsLeft: 1650 });
    apiMocks.submitCommands.mockResolvedValue({
      status: "submitted",
      turn: 0,
      commandCount: 1,
    });
  });

  it("stages the Humanoid preset as a select_race command", async () => {
    const replaceCommands = vi.fn();
    renderScreen(replaceCommands);
    await finishInitialLoad();

    await waitFor(() => {
      expect(replaceCommands).toHaveBeenCalledWith({ kind: "race" }, [
        { type: "select_race", predefinedId: "humanoid" },
      ]);
    });
  });

  it("debounces preview calls after custom edits", async () => {
    renderScreen();
    await finishInitialLoad();

    fireEvent.change(screen.getByLabelText("Race name"), {
      target: { value: "New Race" },
    });

    expect(apiMocks.previewRace).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(apiMocks.previewRace).toHaveBeenCalledWith(
        expect.objectContaining({ name: "New Race" }),
        "alice",
      );
    });
  });

  it("updates visible race points from preview results after economy edits", async () => {
    renderScreen();
    await finishInitialLoad();
    apiMocks.previewRace.mockResolvedValue({
      costBreakdown: { ...costBreakdown, economy: 600, total: 600, pointsLeft: 1050 },
      pointsLeft: 1050,
    });

    fireEvent.change(screen.getByLabelText("Colonists per resource"), {
      target: { value: "700" },
    });

    await waitFor(() => {
      expect(screen.getAllByText("+1050").length).toBeGreaterThan(0);
    });
  });

  it("clears the staged command when the preview has no points left", async () => {
    const replaceCommands = vi.fn();
    apiMocks.previewRace.mockResolvedValue({
      costBreakdown: { ...costBreakdown, pointsLeft: -10 },
      pointsLeft: -10,
    });

    renderScreen(replaceCommands);
    await finishInitialLoad();

    await waitFor(() => {
      expect(replaceCommands).toHaveBeenLastCalledWith({ kind: "race" }, []);
    });
  });

  it("shows structured preview errors", async () => {
    apiMocks.previewRace.mockRejectedValue(new apiMocks.ApiError(400, "RACE_OVERSPENT", "Race is overspent"));
    renderScreen();
    await finishInitialLoad();

    fireEvent.change(screen.getByLabelText("Race name"), {
      target: { value: "Too Fancy" },
    });

    await waitFor(() => {
      expect(screen.getAllByText(/RACE_OVERSPENT/).length).toBeGreaterThan(0);
    });
  });

  it("disables habitability range inputs when a factor is immune", async () => {
    renderScreen();
    await finishInitialLoad();

    fireEvent.click(screen.getAllByLabelText("Immune")[0]);

    expect(screen.getByLabelText("gravity low")).toBeDisabled();
    expect(screen.getByLabelText("gravity high")).toBeDisabled();
  });

  it("rehydrates an existing saved race", async () => {
    apiMocks.getRace.mockResolvedValue({
      race: { ...DEFAULT_RACE, name: "Saved Folk", pluralName: "Saved Folks" },
      costBreakdown,
    });

    renderScreen();

    expect(await screen.findByDisplayValue("Saved Folk")).toBeInTheDocument();
    expect(screen.getByText("Race Points")).toBeInTheDocument();
  });
});
