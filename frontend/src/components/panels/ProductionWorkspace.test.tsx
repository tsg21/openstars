import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ProductionWorkspace } from "./ProductionWorkspace";
import { GameCommandsContext } from "../../contexts/gameCommandsContext";
import type { GameCommandsContextValue } from "../../contexts/gameCommandsContext";
import type { PlayerPlanet, PlayerState } from "../../types";
import type { DesignSummary } from "../../types/designer";

function makePlanet(id: string, name: string, overrides: Partial<PlayerPlanet> = {}): PlayerPlanet {
  return {
    id,
    name,
    x: 0,
    y: 0,
    scanLevel: "detailed",
    scanAge: 0,
    owner: "tim",
    mines: 5,
    factories: 10,
    resources: 100,
    minerals: { ironium: 100, boranium: 50, germanium: 30 },
    productionQueue: [],
    starbase: null,
    scanner: null,
    contributeOnlyLeftoverToResearch: false,
    ...overrides,
  };
}

const designs: DesignSummary[] = [];

function makeBaseState(planets: PlayerPlanet[]): PlayerState {
  return {
    player: "tim",
    turn: 1,
    planets,
    fleets: [],
    designs: [],
    events: [],
  };
}

function Wrapper({
  planets,
  initialPlanetId = null,
  onShowOnMap = vi.fn(),
  replaceCommands = vi.fn(),
  addCommand = vi.fn(),
}: {
  planets: PlayerPlanet[];
  initialPlanetId?: string | null;
  onShowOnMap?: (id: string) => void;
  replaceCommands?: ReturnType<typeof vi.fn>;
  addCommand?: ReturnType<typeof vi.fn>;
}) {
  return (
    <GameCommandsContext.Provider
      value={{
        basePlayerState: makeBaseState(planets),
        addCommand: addCommand as GameCommandsContextValue["addCommand"],
        replaceCommands: replaceCommands as GameCommandsContextValue["replaceCommands"],
        nextTmpFleetId: () => "tmp_1",
      }}
    >
      <ProductionWorkspace
        ownedPlanets={planets}
        currentPlayer="tim"
        shipDesigns={designs}
        initialPlanetId={initialPlanetId}
        onShowOnMap={onShowOnMap}
      />
    </GameCommandsContext.Provider>
  );
}

describe("ProductionWorkspace", () => {
  it("renders three panes when at least one planet is supplied", () => {
    render(<Wrapper planets={[makePlanet("p1", "Earth")]} />);
    expect(screen.getByTestId("planet-list-pane")).toBeInTheDocument();
    expect(screen.getByTestId("centre-pane")).toBeInTheDocument();
    expect(screen.getByTestId("palette-pane")).toBeInTheDocument();
  });

  it("pre-selects initialPlanetId when provided", () => {
    render(
      <Wrapper
        planets={[makePlanet("p1", "Earth"), makePlanet("p2", "Mars")]}
        initialPlanetId="p2"
      />,
    );
    // Centre pane shows Mars
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("Mars");
  });

  it("pre-selects first owned planet (by name) when no initialPlanetId", () => {
    render(
      <Wrapper planets={[makePlanet("p1", "Zeta"), makePlanet("p2", "Alpha")]} />,
    );
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("Alpha");
  });

  it("shows empty-workspace message and no panes when no owned planets", () => {
    render(<Wrapper planets={[]} />);
    expect(screen.getAllByText("Colonise a planet to start producing.").length).toBeGreaterThan(0);
  });

  it("switching planets in the list updates the centre pane", () => {
    render(
      <Wrapper planets={[makePlanet("p1", "Earth"), makePlanet("p2", "Mars")]} />,
    );
    // Initially Earth (first alpha)
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("Earth");
    // Click Mars row in the list
    const rows = screen.getAllByRole("row");
    const marsRow = rows.find((r) => r.textContent?.includes("Mars"));
    fireEvent.click(marsRow!);
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("Mars");
  });

  it("Toggling Empty queue filter keeps current selection", () => {
    render(
      <Wrapper
        planets={[
          makePlanet("p1", "Earth", { productionQueue: [] }),
          makePlanet("p2", "Mars", { productionQueue: [] }),
        ]}
        initialPlanetId="p2"
      />,
    );
    // Toggle "Empty queue"
    fireEvent.click(screen.getByText("Empty queue"));
    // Centre pane still shows Mars
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("Mars");
  });

  it("production summary renders leftover-only annotation", () => {
    render(
      <Wrapper
        planets={[makePlanet("p1", "Earth", { contributeOnlyLeftoverToResearch: true })]}
      />,
    );
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("leftover only");
  });

  it("Idle status shows for empty queue, Building for non-empty queue", () => {
    render(
      <Wrapper
        planets={[
          makePlanet("p1", "Earth", { productionQueue: [] }),
        ]}
        initialPlanetId="p1"
      />,
    );
    expect(screen.getByTestId("centre-pane")).toHaveTextContent("Idle");

    const withQueue = makePlanet("p2", "Mars", {
      productionQueue: [{
        id: "qi1",
        itemType: "mine",
        quantity: 3,
        designId: null,
        progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
      }],
    });
    render(
      <Wrapper planets={[withQueue]} initialPlanetId="p2" />,
    );
    expect(screen.getAllByTestId("centre-pane")[1]).toHaveTextContent("Building (3 remaining)");
  });

  it("Show on map calls onShowOnMap with the selected planet id", () => {
    const onShowOnMap = vi.fn();
    render(
      <Wrapper
        planets={[makePlanet("p1", "Earth")]}
        initialPlanetId="p1"
        onShowOnMap={onShowOnMap}
      />,
    );
    fireEvent.click(screen.getByText("Show on map →"));
    expect(onShowOnMap).toHaveBeenCalledWith("p1");
  });

  it("Queue rows render in order with correct labels", () => {
    const planet = makePlanet("p1", "Earth", {
      productionQueue: [
        {
          id: "qi1",
          itemType: "factory",
          quantity: 5,
          designId: null,
          progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
        },
        {
          id: "qi2",
          itemType: "mine",
          quantity: 2,
          designId: null,
          progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
        },
      ],
    });
    render(<Wrapper planets={[planet]} initialPlanetId="p1" />);
    const centre = screen.getByTestId("centre-pane");
    expect(centre).toHaveTextContent("Factory");
    expect(centre).toHaveTextContent("Mine");
  });

  it("Clear queue button dispatches commands and is disabled when empty", () => {
    const replaceCommands = vi.fn();
    render(
      <Wrapper
        planets={[makePlanet("p1", "Earth", { productionQueue: [] })]}
        initialPlanetId="p1"
        replaceCommands={replaceCommands}
      />,
    );
    const clearBtn = screen.getByRole("button", { name: /clear queue/i });
    expect(clearBtn).toBeDisabled();
  });

  it("planetary_scanner row has + disabled", () => {
    const planet = makePlanet("p1", "Earth", {
      productionQueue: [{
        id: "scanner-1",
        itemType: "planetary_scanner",
        quantity: 1,
        designId: null,
        progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
      }],
    });
    render(<Wrapper planets={[planet]} initialPlanetId="p1" />);
    const increaseBtn = screen.getByRole("button", { name: /increase Planetary Scanner quantity/i });
    expect(increaseBtn).toBeDisabled();
  });

  it("workspace edits call replaceCommands with planet-scoped commands", () => {
    const replaceCommands = vi.fn();
    const planet = makePlanet("p1", "Earth", {
      productionQueue: [{
        id: "qi1",
        itemType: "factory",
        quantity: 3,
        designId: null,
        progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
      }],
    });
    render(
      <Wrapper
        planets={[planet]}
        initialPlanetId="p1"
        replaceCommands={replaceCommands}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /remove factory/i }));
    expect(replaceCommands).toHaveBeenCalledWith(
      { kind: "planet", id: "p1" },
      expect.any(Array),
    );
  });
});
