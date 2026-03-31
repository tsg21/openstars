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
    expect(screen.getByText("Current unit: 6/10 resources")).toBeInTheDocument();
    expect(
      screen.getByText(/Blocked-state reason is not exposed by the current player state yet/),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Move Mine up" }));
    expect(onSetPlanetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ2" }),
      expect.objectContaining({ id: "PQ1" }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Remove Factory" }));
    expect(onSetPlanetProductionQueue).toHaveBeenCalledWith("PL000001", [
      expect.objectContaining({ id: "PQ2" }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Factory" }));
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
    expect(screen.queryByRole("button", { name: "Clear Queue" })).not.toBeInTheDocument();
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
