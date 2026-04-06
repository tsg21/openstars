import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PlanetDetail } from "./PlanetDetail";
import { GameCommandsContext } from "../contexts/gameCommandsContext";
import type { PlayerPlanet, PlayerProductionQueueItem } from "../types";

vi.mock("../lib/planetImages", () => ({
  fetchPlanetImageManifest: vi.fn().mockResolvedValue(null),
  getPlanetImageUrl: vi.fn().mockReturnValue(null),
}));

function makePlanet(overrides: Partial<PlayerPlanet> = {}): PlayerPlanet {
  return {
    id: "PL000001",
    name: "Sol",
    x: 0,
    y: 0,
    owner: "tim",
    scanLevel: "detailed" as const,
    productionQueue: [],
    starbase: { type: "space_station", canBuildShips: true } satisfies NonNullable<PlayerPlanet["starbase"]>,
    ...overrides,
  };
}

function renderPlanetDetail(planetOverrides: Partial<PlayerPlanet> = {}, propOverrides = {}) {
  const planet = makePlanet(planetOverrides);
  return render(
    <GameCommandsContext.Provider
      value={{
        basePlayerState: {
          player: "tim",
          turn: 1,
          planets: [planet],
          designs: [],
          events: [],
          fleets: [],
        },
        addCommand: vi.fn(),
        replaceCommands: vi.fn(),
      }}
    >
      <PlanetDetail
        planet={planet}
        currentPlayer="tim"
        fleetsInOrbit={[]}
        onSelectFleet={vi.fn()}
        shipDesigns={[]}
        {...propOverrides}
      />
    </GameCommandsContext.Provider>,
  );
}

describe("PlanetDetail", () => {
  it("shows mine and factory counts beneath population for detailed planet scans", () => {
    renderPlanetDetail({
      population: 25_000,
      popGrowth: 320,
      resources: 42,
      mines: 10,
      factories: 15,
      minerals: {
        ironium: 300,
        boranium: 250,
        germanium: 200,
      },
      concentrations: {
        ironium: 100,
        boranium: 90,
        germanium: 80,
      },
      miningRate: {
        ironium: 10,
        boranium: 9,
        germanium: 8,
      },
    });

    expect(screen.getByText("Planet")).toBeInTheDocument();
    expect(screen.getByText("Starbase")).toBeInTheDocument();
    expect(screen.getByText("Population:")).toBeInTheDocument();
    expect(screen.getByText("25,000")).toBeInTheDocument();
    expect(screen.getByText("(+320 / turn)")).toBeInTheDocument();
    expect(screen.getByText("Resources:")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Mines:")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Factories:")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.queryByText("Owner:")).not.toBeInTheDocument();
  });

  it("renders the owned planet production queue and edit controls", () => {
    const replaceCommands = vi.fn();
    const queue: PlayerProductionQueueItem[] = [
      {
        id: "PQ1",
        itemType: "factory",
        quantity: 2,
        progress: {
          resourcesSpent: 6,
          mineralsSpent: { ironium: 0, boranium: 0, germanium: 2 },
        },
      },
      {
        id: "PQ2",
        itemType: "mine",
        quantity: 1,
        progress: {
          resourcesSpent: 0,
          mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 },
        },
      },
    ];

    render(
      <GameCommandsContext.Provider
        value={{
          basePlayerState: {
            player: "tim",
            turn: 1,
            planets: [makePlanet({ population: 25_000, productionQueue: queue })],
            designs: [],
            events: [],
            fleets: [],
          },
          addCommand: vi.fn(),
          replaceCommands,
        }}
      >
        <PlanetDetail
          planet={makePlanet({ population: 25_000, productionQueue: queue })}
          currentPlayer="tim"
          fleetsInOrbit={[]}
          onSelectFleet={vi.fn()}
          shipDesigns={[]}
        />
      </GameCommandsContext.Provider>,
    );

    expect(screen.getByText("Production Queue")).toBeInTheDocument();
    expect(screen.getAllByText("Factory").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Mine").length).toBeGreaterThan(0);
    expect(screen.getByText("2x")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Increase Factory quantity" }));
    expect(replaceCommands).toHaveBeenCalledWith({ kind: "planet", id: "PL000001" }, [
      expect.objectContaining({ type: "add_production_item", itemType: "factory", quantity: 1 }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Decrease Mine quantity" }));
    expect(replaceCommands).toHaveBeenCalledWith({ kind: "planet", id: "PL000001" }, [
      expect.objectContaining({ type: "remove_production_item", itemId: "PQ2", quantity: 1 }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Remove Factory" }));
    expect(replaceCommands).toHaveBeenCalledWith(
      { kind: "planet", id: "PL000001" },
      expect.arrayContaining([
        expect.objectContaining({ type: "remove_production_item", itemId: "PQ1", quantity: 2 }),
      ]),
    );

    fireEvent.click(screen.getByRole("button", { name: "Add production item" }));
    expect(screen.queryByRole("button", { name: /^Ship\b/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^Orbital Fort\b/ }));
    expect(replaceCommands).toHaveBeenCalledWith(
      { kind: "planet", id: "PL000001" },
      expect.arrayContaining([
        expect.objectContaining({
          type: "add_production_item",
          itemType: "starbase",
          targetType: "orbital_fort",
          quantity: 1,
        }),
      ]),
    );

    fireEvent.click(screen.getByRole("button", { name: "Add production item" }));
    fireEvent.click(screen.getByRole("button", { name: /^Factory\b/ }));
    expect(replaceCommands).toHaveBeenCalledWith(
      { kind: "planet", id: "PL000001" },
      expect.arrayContaining([
        expect.objectContaining({ type: "add_production_item", itemType: "factory", quantity: 1 }),
      ]),
    );

    fireEvent.click(screen.getByRole("button", { name: "Clear Queue" }));
    expect(replaceCommands).toHaveBeenLastCalledWith({ kind: "planet", id: "PL000001" }, [
      expect.objectContaining({ type: "clear_production_queue", planetId: "PL000001" }),
    ]);
  });

  it("opens the production picker above the trigger", () => {
    renderPlanetDetail({
      population: 25_000,
    });

    fireEvent.click(screen.getByRole("button", { name: "Add production item" }));

    const menu = screen.getByText("Add To Queue");
    const menuContainer = menu.parentElement;
    expect(menuContainer).toHaveClass("bottom-full");
    expect(menuContainer).toHaveClass("mb-2");
  });

  it("does not show editable production controls on non-owned planets", () => {
    renderPlanetDetail(
      {
        name: "Rigel",
        owner: "sara",
        productionQueue: null,
      },
      {},
    );

    expect(screen.queryByText("Production Queue")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add production item" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Clear Queue" })).not.toBeInTheDocument();
  });

  it("shows starbase details for owned and scanned planets", () => {
    renderPlanetDetail({
      starbase: { type: "orbital_fort", canBuildShips: false },
    });
    expect(screen.getByText("Starbase")).toBeInTheDocument();
    expect(screen.getByText(/orbital fort/i)).toBeInTheDocument();

    renderPlanetDetail({
      owner: "sara",
      starbase: { present: true },
      scanLevel: "basic",
      productionQueue: null,
    });
    expect(screen.getAllByText("Starbase").length).toBeGreaterThan(0);
    expect(screen.getByText("Present")).toBeInTheDocument();
  });

  it("shows habitability bars for own planet at detailed scan level", () => {
    renderPlanetDetail({
      population: 500_000,
      habitability: { gravity: 50, temperature: 50, radiation: 50 },
      maxPopulation: 1_000_000,
      popGrowth: 3_750,
    });

    expect(screen.getByRole("img", { name: "Habitability bars" })).toBeInTheDocument();
    expect(screen.getByText("(+3,750 / turn)")).toBeInTheDocument();
    expect(screen.queryByText("Growth:")).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Population details" })).not.toBeInTheDocument();

    fireEvent.mouseEnter(screen.getByLabelText("Population details"));

    expect(screen.getByRole("dialog", { name: "Population details" })).toBeInTheDocument();
    expect(screen.getByText("Max pop:")).toBeInTheDocument();
    expect(screen.getByText("1,000,000")).toBeInTheDocument();
  });

  it("shows habitability bars for a detailed scan of an enemy planet", () => {
    renderPlanetDetail({
      name: "Rigel",
      owner: "sara",
      habitability: { gravity: 30, temperature: 60, radiation: 40 },
      productionQueue: null,
    });

    expect(screen.getByRole("img", { name: "Habitability bars" })).toBeInTheDocument();
    expect(screen.queryByText("Max pop:")).not.toBeInTheDocument();
    expect(screen.queryByText("Growth:")).not.toBeInTheDocument();
  });

  it("does not show habitability bars at basic scan level", () => {
    renderPlanetDetail({
      name: "Vega",
      owner: "sara",
      scanLevel: "basic",
      productionQueue: null,
    });

    expect(screen.queryByRole("img", { name: "Habitability bars" })).not.toBeInTheDocument();
    expect(screen.queryByText("Max pop:")).not.toBeInTheDocument();
  });

  it("does not crash when detailed enemy intel includes explicit null economy fields", () => {
    renderPlanetDetail({
      name: "Rigel",
      owner: "sara",
      population: null,
      mines: null,
      factories: null,
      productionQueue: null,
    });

    expect(screen.getByText("Rigel")).toBeInTheDocument();
    expect(screen.getByText("sara")).toBeInTheDocument();
    expect(screen.queryByText("Owner:")).not.toBeInTheDocument();
    expect(screen.queryByText("Population:")).not.toBeInTheDocument();
    expect(screen.queryByText("Mines:")).not.toBeInTheDocument();
    expect(screen.queryByText("Factories:")).not.toBeInTheDocument();
  });

  it("shows Fleets in Orbit section when fleetsInOrbit is non-empty", () => {
    renderPlanetDetail(
      {},
      {
        fleetsInOrbit: [
          {
            id: "FL001",
            owner: "tim",
            name: "Fleet #1",
            position: { x: 0, y: 0 },
            composition: [{ designId: "D1", count: 3 }],
          },
        ],
      },
    );

    expect(screen.getByText("Fleets in Orbit")).toBeInTheDocument();
    expect(screen.getByText("Fleet #1")).toBeInTheDocument();
    expect(screen.getByText("3 ships")).toBeInTheDocument();
    expect(screen.queryByText(/ID: FL001/)).not.toBeInTheDocument();
  });

  it("calls onSelectFleet with the fleet id when a fleet row is clicked", () => {
    const onSelectFleet = vi.fn();

    renderPlanetDetail(
      {},
      {
        fleetsInOrbit: [
          {
            id: "FL001",
            owner: "tim",
            name: "Fleet #1",
            position: { x: 0, y: 0 },
            composition: [{ designId: "D1", count: 2 }],
          },
        ],
        onSelectFleet,
      },
    );

    fireEvent.click(screen.getByText("Fleet #1"));
    expect(onSelectFleet).toHaveBeenCalledWith("FL001");
  });

  it("does not show Fleets in Orbit section when fleetsInOrbit is empty", () => {
    renderPlanetDetail();

    expect(screen.queryByText("Fleets in Orbit")).not.toBeInTheDocument();
  });

  it("lists ship designs in the production picker and queues a ship item", () => {
    const replaceCommands = vi.fn();
    render(
      <GameCommandsContext.Provider
        value={{
          basePlayerState: {
            player: "tim",
            turn: 1,
            planets: [makePlanet({ population: 25_000, productionQueue: [] })],
            designs: [],
            events: [],
            fleets: [],
          },
          addCommand: vi.fn(),
          replaceCommands,
        }}
      >
        <PlanetDetail
          planet={makePlanet({ population: 25_000, productionQueue: [] })}
          currentPlayer="tim"
          fleetsInOrbit={[]}
          onSelectFleet={vi.fn()}
          shipDesigns={[
            {
              id: "DEship1",
              owner: "tim",
              name: "Scout",
              hull: "scout",
              cost: {
                resources: 15,
                minerals: { ironium: 5, boranium: 3, germanium: 2 },
              },
            },
          ]}
        />
      </GameCommandsContext.Provider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Add production item" }));
    fireEvent.click(screen.getByRole("button", { name: /^Scout\b/ }));
    expect(replaceCommands).toHaveBeenCalledWith(
      { kind: "planet", id: "PL000001" },
      expect.arrayContaining([
        expect.objectContaining({
          type: "add_production_item",
          itemType: "ship",
          designId: "DEship1",
          quantity: 1,
        }),
      ]),
    );
  });
});
