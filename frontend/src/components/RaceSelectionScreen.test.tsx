import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  await screen.findByText("Preset");
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
    apiMocks.previewRace.mockResolvedValue(costBreakdown);
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
      ...costBreakdown,
      economy: 600,
      total: 600,
      pointsLeft: 1050,
    });

    fireEvent.change(screen.getByLabelText("Colonists per resource"), {
      target: { value: "700" },
    });

    await waitFor(() => {
      expect(screen.getAllByText("+1050").length).toBeGreaterThan(0);
    });
  });

  it("shows negative points and clears the staged command when overspent", async () => {
    const replaceCommands = vi.fn();
    apiMocks.previewRace.mockResolvedValue({
      ...costBreakdown,
      pointsLeft: -10,
    });

    renderScreen(replaceCommands);
    await finishInitialLoad();

    await waitFor(() => {
      expect(replaceCommands).toHaveBeenLastCalledWith({ kind: "race" }, []);
    });
    expect(screen.getByText("-10")).toBeInTheDocument();
    expect(screen.getByText("1 issue to fix")).toBeInTheDocument();
    expect(screen.queryByText("Ready to save")).not.toBeInTheDocument();
  });

  it("does not render preview errors as warning copy", async () => {
    apiMocks.previewRace.mockRejectedValue(new apiMocks.ApiError(400, "RACE_OVERSPENT", "Race is overspent"));
    renderScreen();
    await finishInitialLoad();

    fireEvent.change(screen.getByLabelText("Race name"), {
      target: { value: "Too Fancy" },
    });

    await waitFor(() => {
      expect(apiMocks.previewRace).toHaveBeenCalledWith(
        expect.objectContaining({ name: "Too Fancy" }),
        "alice",
      );
    });
    expect(screen.queryByText(/RACE_OVERSPENT/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Race is overspent/)).not.toBeInTheDocument();
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
    expect(screen.queryByText("Race Points")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reset" })).not.toBeInTheDocument();
  });

  it("sets PRT to HE when Hyper Expansion is clicked", async () => {
    renderScreen();
    await finishInitialLoad();
    fireEvent.click(screen.getByRole("button", { name: /Hyper Expansion/i }));
    await waitFor(() => {
      expect(apiMocks.previewRace).toHaveBeenCalledWith(
        expect.objectContaining({ prt: "HE" }),
        "alice",
      );
    });
  });

  it("labels the JOAT PRT card with its code", async () => {
    renderScreen();
    await finishInitialLoad();

    const prtSection = screen.getByText("Primary Racial Trait - choose exactly one").closest("section");
    expect(prtSection).not.toBeNull();
    const joatCard = within(prtSection!).getByRole("button", { name: /Jack of All Trades/i });
    expect(joatCard).toHaveTextContent("JOAT");
    expect(joatCard).not.toHaveTextContent("free");
  });

  it("shows doubled effective growth for HE", async () => {
    renderScreen();
    await finishInitialLoad();
    fireEvent.click(screen.getByRole("button", { name: /Hyper Expansion/i }));
    fireEvent.change(screen.getByLabelText("Max growth rate"), { target: { value: "10" } });
    expect(await screen.findByText(/20%/)).toBeInTheDocument();
  });

  it("renders IFE as an enabled checkbox outside the locked list", async () => {
    renderScreen();
    await finishInitialLoad();

    expect(screen.getByRole("checkbox", { name: "Improved Fuel Efficiency" })).toBeEnabled();
    expect(screen.getByRole("button", { name: /Total Terraforming/i })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /Improved Fuel Efficiency/i })).not.toBeInTheDocument();
  });

  it("toggles IFE in the staged race command", async () => {
    const replaceCommands = vi.fn();
    renderScreen(replaceCommands);
    await finishInitialLoad();

    const ife = screen.getByRole("checkbox", { name: "Improved Fuel Efficiency" });
    fireEvent.click(ife);

    await waitFor(() => {
      expect(replaceCommands).toHaveBeenLastCalledWith({ kind: "race" }, [
        {
          type: "select_race",
          race: expect.objectContaining({ lrts: ["IFE"] }),
        },
      ]);
    });

    fireEvent.click(ife);

    await waitFor(() => {
      expect(replaceCommands).toHaveBeenLastCalledWith({ kind: "race" }, [
        {
          type: "select_race",
          race: expect.objectContaining({ lrts: [] }),
        },
      ]);
    });
  });

  it("previews IFE when checked without adding selected effect copy", async () => {
    renderScreen();
    await finishInitialLoad();

    fireEvent.click(screen.getByRole("checkbox", { name: "Improved Fuel Efficiency" }));

    await waitFor(() => {
      expect(apiMocks.previewRace).toHaveBeenCalledWith(
        expect.objectContaining({ lrts: ["IFE"] }),
        "alice",
      );
    });
    expect(screen.queryByText("+ Fuel -15%")).not.toBeInTheDocument();
    expect(screen.queryByText("+ Fuel Mizer / Galaxy Scoop")).not.toBeInTheDocument();
    expect(screen.queryByText("+ Starting Propulsion +1")).not.toBeInTheDocument();
  });

  it("keeps the remaining LRTs locked", async () => {
    renderScreen();
    await finishInitialLoad();

    const lockedNames = [
      "Total Terraforming",
      "Advanced Remote Mining",
      "Improved Starbases",
      "Generalised Research",
      "Ultimate Recycling",
      "Mineral Alchemy",
      "No Ramscoop Engines",
      "Cheap Engines",
      "Only Basic Remote Mining",
      "No Advanced Scanners",
      "Low Starting Population",
      "Bleeding Edge Technology",
      "Regenerating Shields",
    ];

    for (const name of lockedNames) {
      expect(screen.getByRole("button", { name: new RegExp(name, "i") })).toBeDisabled();
    }
  });
});
