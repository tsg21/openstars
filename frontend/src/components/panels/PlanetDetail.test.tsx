import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PlanetDetail } from "./PlanetDetail";
import { GameCommandsContext } from "../../contexts/gameCommandsContext";
import type { GameCommandsContextValue } from "../../contexts/gameCommandsContext";
import type { PlayerPlanet } from "../../types";
import { fetchPlanetImageManifest, getPlanetImageUrl } from "../../lib/planetImages";

vi.mock("../../lib/planetImages", () => ({
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
    scanAge: 0,
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
          research: {
            levels: { energy: 1, weapons: 1, propulsion: 1, construction: 1, electronics: 1, biotechnology: 1 },
            progress: { energy: 0, weapons: 0, propulsion: 0, construction: 0, electronics: 0, biotechnology: 0 },
            currentField: "energy",
            nextField: null,
            allocationPercent: 25,
            remainingCost: { energy: 100, weapons: 100, propulsion: 100, construction: 100, electronics: 100, biotechnology: 100 },
            reservableResourcesThisTurn: 100,
          },
        },
        addCommand: vi.fn() as GameCommandsContextValue["addCommand"],
        replaceCommands: vi.fn() as GameCommandsContextValue["replaceCommands"],
        nextTmpFleetId: vi.fn(() => "tmp_1"),
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

  it("shows own scanner installation details when installed", () => {
    renderPlanetDetail({
      population: 25_000,
      scanner: {
        installed: true,
        name: "Viewer 50",
        normal: 50,
        penetrating: 0,
      },
    });

    expect(screen.getByText("Scanner:")).toBeInTheDocument();
    expect(screen.getByText("Viewer 50")).toBeInTheDocument();
  });

  it("positions the scanner row below the resource summary near the top of the planet details", () => {
    renderPlanetDetail({
      population: 25_000,
      resources: 42,
      mines: 10,
      factories: 15,
      scanner: {
        installed: true,
        name: "Viewer 50",
        normal: 50,
        penetrating: 0,
      },
    });

    const resources = screen.getByText("Resources:");
    const scanner = screen.getByText("Scanner:");
    const starbase = screen.getByText("Starbase");

    expect(resources.compareDocumentPosition(scanner) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
    expect(scanner.compareDocumentPosition(starbase) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
  });

  it("shows None installed for own planets without scanner", () => {
    renderPlanetDetail({
      population: 25_000,
      scanner: null,
    });

    expect(screen.getByText("Scanner:")).toBeInTheDocument();
    expect(screen.getByText("None installed")).toBeInTheDocument();
  });

  it("shows enemy scanner summary only for detailed scans", () => {
    const detailed = renderPlanetDetail({
      owner: "sara",
      scanLevel: "detailed",
      productionQueue: null,
      scanner: { installed: true },
    });

    expect(screen.getByText("Scanner:")).toBeInTheDocument();
    expect(screen.getByText("Installed")).toBeInTheDocument();
    detailed.unmount();

    const basic = renderPlanetDetail({
      owner: "sara",
      scanLevel: "basic",
      productionQueue: null,
      scanner: null,
    });
    expect(screen.queryByText("Scanner:")).not.toBeInTheDocument();
    basic.unmount();

    renderPlanetDetail({
      owner: "sara",
      scanLevel: "none",
      productionQueue: null,
      scanner: { installed: true },
    });
    expect(screen.queryByText("Scanner:")).not.toBeInTheDocument();
  });

  it("renders a compact header with the owner under the planet name and the image on the right", async () => {
    vi.mocked(fetchPlanetImageManifest).mockResolvedValueOnce({
      version: "v1",
      baseUrl: "https://example.com/images",
      imagesByClass: {},
    });
    vi.mocked(getPlanetImageUrl).mockReturnValueOnce("/planet.png");

    renderPlanetDetail();

    const heading = screen.getByRole("heading", { name: "Sol" });
    const owner = screen.getByText("You");
    const image = await screen.findByAltText("Sol render");
    const headingContainer = heading.parentElement;
    const imageContainer = image.parentElement;

    expect(headingContainer).not.toBeNull();
    expect(imageContainer).not.toBeNull();

    const headerRow = headingContainer?.parentElement;
    expect(headerRow).toHaveClass("flex");
    expect(owner.parentElement).toBe(headingContainer);
    expect(imageContainer).toHaveClass("h-20");
    expect(imageContainer).toHaveClass("w-20");
    expect(
      headingContainer!.compareDocumentPosition(imageContainer!) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("shows the single fleet name in orbit and selects it directly from the header", () => {
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

    fireEvent.click(screen.getByRole("button", { name: "Fleet #1 in orbit" }));
    expect(onSelectFleet).toHaveBeenCalledWith("FL001");
    expect(screen.queryByText("Fleets in Orbit")).not.toBeInTheDocument();
  });

  it("opens the fleets-in-orbit list from the header when several fleets are present", () => {
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
          {
            id: "FL002",
            owner: "tim",
            name: "Fleet #2",
            position: { x: 0, y: 0 },
            composition: [{ designId: "D1", count: 4 }],
          },
        ],
      },
    );

    fireEvent.click(screen.getByRole("button", { name: "2 fleets in orbit" }));

    expect(screen.getByText("Fleets in Orbit")).toBeInTheDocument();
    expect(screen.getByText("Fleet #1")).toBeInTheDocument();
    expect(screen.getByText("Fleet #2")).toBeInTheDocument();
    expect(screen.queryByText("Planet")).not.toBeInTheDocument();
    expect(screen.queryByText("Starbase")).not.toBeInTheDocument();
    expect(screen.queryByText("Manage →")).not.toBeInTheDocument();
  });

  it("closes the fleets-in-orbit list and returns to planet details", () => {
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
          {
            id: "FL002",
            owner: "tim",
            name: "Fleet #2",
            position: { x: 0, y: 0 },
            composition: [{ designId: "D1", count: 4 }],
          },
        ],
      },
    );

    fireEvent.click(screen.getByRole("button", { name: "2 fleets in orbit" }));
    fireEvent.click(screen.getByRole("button", { name: "Close fleets in orbit" }));

    expect(screen.queryByText("Fleets in Orbit")).not.toBeInTheDocument();
    expect(screen.getByText("Planet")).toBeInTheDocument();
    expect(screen.getByText("Starbase")).toBeInTheDocument();
    expect(screen.getByText("Production")).toBeInTheDocument();
  });

  it("shows Production section with Manage button and queue summary for owned planets", () => {
    const onOpenProduction = vi.fn();
    renderPlanetDetail(
      {
        productionQueue: [
          {
            id: "PQ1",
            itemType: "factory",
            quantity: 2,
            progress: { resourcesSpent: 0, mineralsSpent: { ironium: 0, boranium: 0, germanium: 0 } },
          },
        ],
      },
      { onOpenProduction },
    );

    expect(screen.getByText("Production")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Manage →/ })).toBeInTheDocument();
    expect(screen.getByText("Queue: 2× Factory")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Manage →/ }));
    expect(onOpenProduction).toHaveBeenCalledWith("PL000001");
  });

  it("shows empty queue summary when productionQueue is empty", () => {
    renderPlanetDetail({ productionQueue: [] });
    expect(screen.getByText("Queue: empty")).toBeInTheDocument();
  });

  it("does not show Production section on non-owned planets", () => {
    renderPlanetDetail({ name: "Rigel", owner: "sara", productionQueue: null });

    expect(screen.queryByText("Production")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Manage →/ })).not.toBeInTheDocument();
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

  it("renders stale scan banner and muted stale data", () => {
    renderPlanetDetail({
      owner: "sara",
      scanLevel: "detailed",
      scanAge: 3,
      productionQueue: null,
      population: 25_000,
      minerals: {
        ironium: 300,
        boranium: 250,
        germanium: 200,
      },
      miningRate: {
        ironium: 10,
        boranium: 9,
        germanium: 8,
      },
      habitability: { gravity: 30, temperature: 60, radiation: 40 },
    });

    expect(screen.getByText("Scan age: 3 turns")).toBeInTheDocument();
    expect(screen.getByText("Population:")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Habitability bars" })).toBeInTheDocument();
    expect(screen.queryByText("mining rate")).not.toBeInTheDocument();
    expect(screen.queryByText("Production")).not.toBeInTheDocument();
  });

  it("does not render stale scan banner for fresh planets", () => {
    renderPlanetDetail({
      scanLevel: "detailed",
      scanAge: 0,
    });

    expect(screen.queryByText(/Scan age/)).not.toBeInTheDocument();
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

  it("shows the fleets list and ship counts for multiple fleets after opening the fleets-in-orbit view", () => {
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
          {
            id: "FL002",
            owner: "sara",
            name: "Enemy Fleet",
            position: { x: 0, y: 0 },
            composition: [{ designId: "D1", count: 1 }],
          },
        ],
      },
    );

    fireEvent.click(screen.getByRole("button", { name: "2 fleets in orbit" }));

    expect(screen.getByText("Fleets in Orbit")).toBeInTheDocument();
    expect(screen.getByText("Fleet #1")).toBeInTheDocument();
    expect(screen.getByText("3 ships")).toBeInTheDocument();
    expect(screen.getByText("Fleet")).toBeInTheDocument();
  });

  it("calls onSelectFleet with the fleet id when a fleet row is clicked in the fleets-in-orbit view", () => {
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
          {
            id: "FL002",
            owner: "tim",
            name: "Fleet #2",
            position: { x: 0, y: 0 },
            composition: [{ designId: "D1", count: 1 }],
          },
        ],
        onSelectFleet,
      },
    );

    fireEvent.click(screen.getByRole("button", { name: "2 fleets in orbit" }));
    fireEvent.click(screen.getByText("Fleet #1"));
    expect(onSelectFleet).toHaveBeenCalledWith("FL001");
  });

  it("does not show Fleets in Orbit section when fleetsInOrbit is empty", () => {
    renderPlanetDetail();

    expect(screen.queryByText("Fleets in Orbit")).not.toBeInTheDocument();
  });

  it("shows Manage Fleets button whenever at least one own fleet is in orbit", () => {
    const { rerender } = renderPlanetDetail(
      {},
      {
        fleetsInOrbit: [{ id: "FL001", owner: "tim", name: "Fleet #1", position: { x: 0, y: 0 } }],
      },
    );

    expect(screen.getByRole("button", { name: "Manage Fleets" })).toBeInTheDocument();

    rerender(
      <GameCommandsContext.Provider
        value={{
          basePlayerState: {
            player: "tim",
            turn: 1,
            planets: [makePlanet()],
            designs: [],
            events: [],
            fleets: [],
          },
          addCommand: vi.fn() as GameCommandsContextValue["addCommand"],
          replaceCommands: vi.fn() as GameCommandsContextValue["replaceCommands"],
          nextTmpFleetId: vi.fn(() => "tmp_1"),
        }}
      >
        <PlanetDetail
          planet={makePlanet()}
          currentPlayer="tim"
          fleetsInOrbit={[{ id: "FL009", owner: "sara", name: "Enemy Fleet", position: { x: 0, y: 0 } }]}
          onSelectFleet={vi.fn()}
          shipDesigns={[]}
        />
      </GameCommandsContext.Provider>,
    );

    expect(screen.queryByRole("button", { name: "Manage Fleets" })).not.toBeInTheDocument();
  });

  it("opens Fleet Composer as a dialog overlay from orbit controls", () => {
    renderPlanetDetail(
      {},
      {
        fleetsInOrbit: [
          { id: "FL001", owner: "tim", name: "Fleet #1", position: { x: 0, y: 0 } },
          { id: "FL002", owner: "tim", name: "Fleet #2", position: { x: 0, y: 0 } },
        ],
      },
    );

    fireEvent.click(screen.getByRole("button", { name: "Manage Fleets" }));

    expect(screen.getByRole("dialog", { name: "Fleet Composer" })).toBeInTheDocument();
  });



  it("renders research contribution section for own detailed planet", () => {
    renderPlanetDetail({
      resources: 80,
      contributeOnlyLeftoverToResearch: false,
    });

    expect(screen.getByText("Research")).toBeInTheDocument();
    expect(screen.getByText(/Reserved this turn: ≈ 20 resources/i)).toBeInTheDocument();
  });

  it("hides research contribution for non-owner signal", () => {
    renderPlanetDetail({
      owner: "sara",
      contributeOnlyLeftoverToResearch: null,
      scanLevel: "detailed",
      scanAge: 0,
      productionQueue: null,
    }, { currentPlayer: "tim" });

    expect(screen.queryByText("Research")).not.toBeInTheDocument();
  });

  it("queues production-mode command on toggle", () => {
    const replaceCommands = vi.fn();
    const planet = makePlanet({ contributeOnlyLeftoverToResearch: false, resources: 80 });

    render(
      <GameCommandsContext.Provider
        value={{
          basePlayerState: {
            player: "tim",
            turn: 1,
            planets: [planet],
            designs: [],
            events: [],
            fleets: [],
            research: {
              levels: { energy: 1, weapons: 1, propulsion: 1, construction: 1, electronics: 1, biotechnology: 1 },
              progress: { energy: 0, weapons: 0, propulsion: 0, construction: 0, electronics: 0, biotechnology: 0 },
              currentField: "energy",
              nextField: null,
              allocationPercent: 25,
              remainingCost: { energy: 100, weapons: 100, propulsion: 100, construction: 100, electronics: 100, biotechnology: 100 },
              reservableResourcesThisTurn: 100,
            },
          },
          addCommand: vi.fn(),
          replaceCommands,
          nextTmpFleetId: vi.fn(() => "tmp_1"),
        }}
      >
        <PlanetDetail
          planet={planet}
          currentPlayer="tim"
          fleetsInOrbit={[]}
          onSelectFleet={vi.fn()}
          shipDesigns={[]}
        />
      </GameCommandsContext.Provider>,
    );

    fireEvent.click(screen.getByLabelText("Contribute only leftover resources to research"));
    expect(replaceCommands).toHaveBeenCalled();
  });

});
