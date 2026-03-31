import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DetailPanel } from "./DetailPanel";

vi.mock("../lib/planetImages", () => ({
  fetchPlanetImageManifest: vi.fn().mockResolvedValue(null),
  getPlanetImageUrl: vi.fn().mockReturnValue(null),
}));

describe("DetailPanel", () => {
  it("shows mine and factory counts beneath population for detailed planet scans", () => {
    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000001",
          name: "Sol",
          x: 500_000_000_000,
          y: 500_000_000_000,
          owner: "tim",
          population: 25_000,
          mines: 10,
          factories: 15,
          scanLevel: "detailed",
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
          productionQueue: [],
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={vi.fn()}
      />,
    );

    expect(screen.getByText("Population:")).toBeInTheDocument();
    expect(screen.getByText("25,000")).toBeInTheDocument();
    expect(screen.getByText("Mines:")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Factories:")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
  });

  it("renders the owned planet production queue and edit controls", () => {
    const onSetPlanetProductionQueue = vi.fn();

    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000001",
          name: "Sol",
          x: 500_000_000_000,
          y: 500_000_000_000,
          owner: "tim",
          population: 25_000,
          scanLevel: "detailed",
          productionQueue: [
            {
              id: "PQ1",
              itemType: "factory",
              quantity: 2,
              progress: {
                resourcesSpent: 6,
                mineralsSpent: {
                  ironium: 0,
                  boranium: 0,
                  germanium: 2,
                },
              },
            },
            {
              id: "PQ2",
              itemType: "mine",
              quantity: 1,
              progress: {
                resourcesSpent: 0,
                mineralsSpent: {
                  ironium: 0,
                  boranium: 0,
                  germanium: 0,
                },
              },
            },
          ],
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={onSetPlanetProductionQueue}
      />,
    );

    expect(screen.getByText("Production Queue")).toBeInTheDocument();
    expect(screen.getAllByText("Factory").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Mine").length).toBeGreaterThan(0);
    expect(screen.getByText("2x")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Increase Factory quantity" }));
    expect(onSetPlanetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ1", quantity: 3 }),
      expect.objectContaining({ id: "PQ2", quantity: 1 }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Decrease Mine quantity" }));
    expect(onSetPlanetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ1", quantity: 2 }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Remove Factory" }));
    expect(onSetPlanetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ2" }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Add production item" }));
    expect(screen.getByRole("button", { name: /^Ship\b/ })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /^Factory\b/ }));
    expect(onSetPlanetProductionQueue).toHaveBeenCalledWith(
      "PL000001",
      expect.arrayContaining([
        expect.objectContaining({ id: "PQ1" }),
        expect.objectContaining({ id: "PQ2" }),
        expect.objectContaining({ itemType: "factory", quantity: 1 }),
      ]),
    );

    fireEvent.click(screen.getByRole("button", { name: "Clear Queue" }));
    expect(onSetPlanetProductionQueue).toHaveBeenLastCalledWith("PL000001", []);
  });

  it("does not show editable production controls on non-owned planets", () => {
    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000001",
          name: "Rigel",
          x: 0,
          y: 0,
          owner: "sara",
          scanLevel: "detailed",
          productionQueue: null,
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={vi.fn()}
      />,
    );

    expect(screen.queryByText("Production Queue")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add production item" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Clear Queue" })).not.toBeInTheDocument();
  });

  it("shows habitability bars for own planet at detailed scan level", () => {
    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000001",
          name: "Sol",
          x: 0,
          y: 0,
          owner: "tim",
          population: 500_000,
          scanLevel: "detailed",
          habitability: { gravity: 50, temperature: 50, radiation: 50 },
          maxPopulation: 1_000_000,
          popGrowth: 3_750,
          productionQueue: [],
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={vi.fn()}
      />,
    );

    expect(screen.getByRole("img", { name: "Habitability bars" })).toBeInTheDocument();
    expect(screen.getByText("Max pop:")).toBeInTheDocument();
    expect(screen.getByText("1,000,000")).toBeInTheDocument();
    expect(screen.getByText("Growth:")).toBeInTheDocument();
    expect(screen.getByText("+3,750 / turn")).toBeInTheDocument();
  });

  it("shows habitability bars for a detailed scan of an enemy planet", () => {
    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000002",
          name: "Rigel",
          x: 0,
          y: 0,
          owner: "sara",
          scanLevel: "detailed",
          habitability: { gravity: 30, temperature: 60, radiation: 40 },
          productionQueue: null,
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={vi.fn()}
      />,
    );

    expect(screen.getByRole("img", { name: "Habitability bars" })).toBeInTheDocument();
    // max_population and pop_growth are owner-only
    expect(screen.queryByText("Max pop:")).not.toBeInTheDocument();
    expect(screen.queryByText("Growth:")).not.toBeInTheDocument();
  });

  it("does not show habitability bars at basic scan level", () => {
    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000003",
          name: "Vega",
          x: 0,
          y: 0,
          owner: "sara",
          scanLevel: "basic",
          productionQueue: null,
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={vi.fn()}
      />,
    );

    expect(screen.queryByRole("img", { name: "Habitability bars" })).not.toBeInTheDocument();
    expect(screen.queryByText("Max pop:")).not.toBeInTheDocument();
  });

  it("does not crash when detailed enemy intel includes explicit null economy fields", () => {
    render(
      <DetailPanel
        collapsed={false}
        onToggle={vi.fn()}
        selectedPlanet={{
          id: "PL000001",
          name: "Rigel",
          x: 0,
          y: 0,
          owner: "sara",
          population: null,
          mines: null,
          factories: null,
          scanLevel: "detailed",
          productionQueue: null,
        }}
        selectedFleet={null}
        currentPlayer="tim"
        designs={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onSetPlanetProductionQueue={vi.fn()}
      />,
    );

    expect(screen.getByText("Owner:")).toBeInTheDocument();
    expect(screen.queryByText("Population:")).not.toBeInTheDocument();
    expect(screen.queryByText("Mines:")).not.toBeInTheDocument();
    expect(screen.queryByText("Factories:")).not.toBeInTheDocument();
  });
});
