import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PlanetDetail } from "./PlanetDetail";

vi.mock("../lib/planetImages", () => ({
  fetchPlanetImageManifest: vi.fn().mockResolvedValue(null),
  getPlanetImageUrl: vi.fn().mockReturnValue(null),
}));

function makePlanet(overrides: Record<string, unknown> = {}) {
  return {
    id: "PL000001",
    name: "Sol",
    x: 0,
    y: 0,
    owner: "tim",
    scanLevel: "detailed" as const,
    productionQueue: [],
    ...overrides,
  };
}

function renderPlanetDetail(planetOverrides: Record<string, unknown> = {}, propOverrides = {}) {
  return render(
    <PlanetDetail
      planet={makePlanet(planetOverrides)}
      currentPlayer="tim"
      fleetsInOrbit={[]}
      onSelectFleet={vi.fn()}
      onSetProductionQueue={vi.fn()}
      {...propOverrides}
    />,
  );
}

describe("PlanetDetail", () => {
  it("shows mine and factory counts beneath population for detailed planet scans", () => {
    renderPlanetDetail({
      population: 25_000,
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

    expect(screen.getByText("Population:")).toBeInTheDocument();
    expect(screen.getByText("25,000")).toBeInTheDocument();
    expect(screen.getByText("Mines:")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Factories:")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
  });

  it("renders the owned planet production queue and edit controls", () => {
    const onSetProductionQueue = vi.fn();

    renderPlanetDetail(
      {
        population: 25_000,
        productionQueue: [
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
        ],
      },
      { onSetProductionQueue },
    );

    expect(screen.getByText("Production Queue")).toBeInTheDocument();
    expect(screen.getAllByText("Factory").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Mine").length).toBeGreaterThan(0);
    expect(screen.getByText("2x")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Increase Factory quantity" }));
    expect(onSetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ1", quantity: 3 }),
      expect.objectContaining({ id: "PQ2", quantity: 1 }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Decrease Mine quantity" }));
    expect(onSetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ1", quantity: 2 }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Remove Factory" }));
    expect(onSetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ2" }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Add production item" }));
    expect(screen.getByRole("button", { name: /^Ship\b/ })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /^Factory\b/ }));
    expect(onSetProductionQueue).toHaveBeenCalledWith(
      "PL000001",
      expect.arrayContaining([
        expect.objectContaining({ id: "PQ1" }),
        expect.objectContaining({ id: "PQ2" }),
        expect.objectContaining({ itemType: "factory", quantity: 1 }),
      ]),
    );

    fireEvent.click(screen.getByRole("button", { name: "Clear Queue" }));
    expect(onSetProductionQueue).toHaveBeenLastCalledWith("PL000001", []);
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

  it("shows habitability bars for own planet at detailed scan level", () => {
    renderPlanetDetail({
      population: 500_000,
      habitability: { gravity: 50, temperature: 50, radiation: 50 },
      maxPopulation: 1_000_000,
      popGrowth: 3_750,
    });

    expect(screen.getByRole("img", { name: "Habitability bars" })).toBeInTheDocument();
    expect(screen.getByText("Max pop:")).toBeInTheDocument();
    expect(screen.getByText("1,000,000")).toBeInTheDocument();
    expect(screen.getByText("Growth:")).toBeInTheDocument();
    expect(screen.getByText("+3,750 / turn")).toBeInTheDocument();
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

    expect(screen.getByText("Owner:")).toBeInTheDocument();
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
});
