import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BuildPalette } from "./BuildPalette";
import type { PlayerPlanet } from "../../types";
import type { DesignSummary } from "../../types/designer";

function makePlanet(overrides: Partial<PlayerPlanet> = {}): PlayerPlanet {
  return {
    id: "p1",
    name: "Earth",
    x: 0,
    y: 0,
    scanLevel: "detailed",
    scanAge: 0,
    owner: "tim",
    mines: 10,
    factories: 20,
    resources: 200,
    minerals: { ironium: 500, boranium: 300, germanium: 200 },
    productionQueue: [],
    starbase: { type: "space_station", canBuildShips: true },
    scanner: { installed: false, name: "", normal: 0, penetrating: 0 },
    ...overrides,
  };
}

const designs: DesignSummary[] = [
  {
    id: "d1",
    name: "Scout",
    hull: "scout",
    fuelCapacity: 100,
    cost: { resources: 40, minerals: { ironium: 0, boranium: 0, germanium: 0 } },
  },
];

describe("BuildPalette", () => {
  it("renders all three categories with expected entries", () => {
    render(
      <BuildPalette
        planet={makePlanet()}
        queue={[]}
        shipDesigns={designs}
        onAdd={vi.fn()}
      />,
    );
    expect(screen.getByText("Infrastructure")).toBeInTheDocument();
    expect(screen.getByText("Mine")).toBeInTheDocument();
    expect(screen.getByText("Factory")).toBeInTheDocument();
    expect(screen.getByText("Planetary Scanner")).toBeInTheDocument();
    expect(screen.getByText("Ships")).toBeInTheDocument();
    expect(screen.getByText("Scout")).toBeInTheDocument();
    expect(screen.getByText("Starbases")).toBeInTheDocument();
  });

  it("click on Mine calls onAdd with itemType 'mine' and quantity 1", () => {
    const onAdd = vi.fn();
    render(
      <BuildPalette
        planet={makePlanet()}
        queue={[]}
        shipDesigns={designs}
        onAdd={onAdd}
      />,
    );
    fireEvent.click(screen.getByText("Mine"));
    expect(onAdd).toHaveBeenCalledWith("mine", undefined, undefined, 1);
  });

  it("Shift+click on Factory calls onAdd with quantity 5", () => {
    const onAdd = vi.fn();
    render(
      <BuildPalette
        planet={makePlanet()}
        queue={[]}
        shipDesigns={designs}
        onAdd={onAdd}
      />,
    );
    fireEvent.click(screen.getByText("Factory"), { shiftKey: true });
    expect(onAdd).toHaveBeenCalledWith("factory", undefined, undefined, 5);
  });

  it("Planetary Scanner shows 'Already installed' when has scanner", () => {
    render(
      <BuildPalette
        planet={makePlanet({ scanner: { installed: true, name: "Scoper", normal: 200, penetrating: 0 } })}
        queue={[]}
        shipDesigns={[]}
        onAdd={vi.fn()}
      />,
    );
    expect(screen.getByText("Already installed")).toBeInTheDocument();
    expect(screen.getByText("Planetary Scanner").closest("button")).toBeDisabled();
  });

  it("Planetary Scanner shows 'Already queued' when already in queue", () => {
    const queue = [{
      id: "qi1",
      itemType: "planetary_scanner" as const,
      quantity: 1,
      designId: null,
      progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
    }];
    render(
      <BuildPalette
        planet={makePlanet()}
        queue={queue}
        shipDesigns={[]}
        onAdd={vi.fn()}
      />,
    );
    expect(screen.getByText("Already queued")).toBeInTheDocument();
  });

  it("Ship rows show 'Needs starbase' when planet cannot build ships", () => {
    render(
      <BuildPalette
        planet={makePlanet({ starbase: { type: "orbital_fort", canBuildShips: false } })}
        queue={[]}
        shipDesigns={designs}
        onAdd={vi.fn()}
      />,
    );
    expect(screen.getByText("Needs starbase")).toBeInTheDocument();
    expect(screen.getByText("Scout").closest("button")).toBeDisabled();
  });

  it("Ships section renders 'No designs' when no ship designs supplied", () => {
    render(
      <BuildPalette
        planet={makePlanet()}
        queue={[]}
        shipDesigns={[]}
        onAdd={vi.fn()}
      />,
    );
    expect(screen.getByText("No designs")).toBeInTheDocument();
  });
});
