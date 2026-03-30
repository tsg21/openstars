import { render, screen } from "@testing-library/react";
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
      />,
    );

    expect(screen.getByText("Population:")).toBeInTheDocument();
    expect(screen.getByText("25,000")).toBeInTheDocument();
    expect(screen.getByText("Mines:")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Factories:")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
  });
});
