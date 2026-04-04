import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DetailPanel } from "./DetailPanel";

vi.mock("./FleetDetail", () => ({
  FleetDetail: ({ fleet }: { fleet: { id: string; name?: string | null } }) => (
    <div>Fleet detail: {fleet.name ?? fleet.id}</div>
  ),
}));

vi.mock("./PlanetDetail", () => ({
  PlanetDetail: ({ planet }: { planet: { name: string } }) => <div>Planet detail: {planet.name}</div>,
}));

function makeProps() {
  return {
    collapsed: false,
    onToggle: vi.fn(),
    selectedPlanet: null,
    selectedFleet: null,
    currentPlayer: "tim",
    designs: [],
    knownPlanets: [],
    selectedTurn: 1,
    ownFleets: [],
    onNewCommand: vi.fn(),
    onWaypointEditorStateChange: vi.fn(),
    onSetPlanetProductionQueue: vi.fn(),
    fleetsAtSelectedPlanet: [],
    onSelectFleet: vi.fn(),
  };
}

describe("DetailPanel", () => {
  it("renders the empty state when nothing is selected", () => {
    render(<DetailPanel {...makeProps()} />);

    expect(screen.getByText("Nothing selected")).toBeInTheDocument();
    expect(
      screen.getByText("Click a planet or fleet on the map to see details."),
    ).toBeInTheDocument();
  });

  it("renders PlanetDetail when a planet is selected", () => {
    render(
      <DetailPanel
        {...makeProps()}
        selectedPlanet={{
          id: "PL000001",
          name: "Sol",
          x: 0,
          y: 0,
          owner: "tim",
          scanLevel: "basic",
          productionQueue: [],
        }}
      />,
    );

    expect(screen.getByText("Planet detail: Sol")).toBeInTheDocument();
  });

  it("renders FleetDetail when a fleet is selected", () => {
    render(
      <DetailPanel
        {...makeProps()}
        selectedFleet={{
          id: "FL001",
          name: "Fleet #1",
          owner: "tim",
          position: { x: 0, y: 0 },
          waypoints: [],
        }}
      />,
    );

    expect(screen.getByText("Fleet detail: Fleet #1")).toBeInTheDocument();
  });

  it("prefers fleet detail when both fleet and planet are present", () => {
    render(
      <DetailPanel
        {...makeProps()}
        selectedPlanet={{
          id: "PL000001",
          name: "Sol",
          x: 0,
          y: 0,
          owner: "tim",
          scanLevel: "basic",
          productionQueue: [],
        }}
        selectedFleet={{
          id: "FL001",
          name: "Fleet #1",
          owner: "tim",
          position: { x: 0, y: 0 },
          waypoints: [],
        }}
      />,
    );

    expect(screen.getByText("Fleet detail: Fleet #1")).toBeInTheDocument();
    expect(screen.queryByText("Planet detail: Sol")).not.toBeInTheDocument();
  });
});
