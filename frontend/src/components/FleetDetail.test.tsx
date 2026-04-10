import type { ReactElement } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FleetDetail } from "./FleetDetail";
import { GameCommandsContext } from "../contexts/gameCommandsContext";
import type { WaypointEditorState } from "./FleetDetail";

function renderWithCommands(ui: ReactElement, addCommand = vi.fn()) {
  return {
    addCommand,
    ...render(
      <GameCommandsContext.Provider
        value={{
          basePlayerState: { player: "tim", turn: 1, planets: [], designs: [], events: [], fleets: [] },
          addCommand,
          replaceCommands: vi.fn(),
        }}
      >
        {ui}
      </GameCommandsContext.Provider>,
    ),
  };
}

function makeFleet(overrides: Record<string, unknown> = {}) {
  return {
    id: "FL001",
    owner: "tim",
    name: "Fleet #1",
    position: { x: 0, y: 0 },
    waypoints: [],
    ...overrides,
  };
}

function renderFleetDetail(fleetOverrides: Record<string, unknown> = {}, propOverrides = {}) {
  return renderWithCommands(
    <FleetDetail
      fleet={makeFleet(fleetOverrides)}
      currentPlayer="tim"
      designs={[]}
      knownPlanets={[]}
      onWaypointEditorStateChange={vi.fn<(state: WaypointEditorState) => void>()}
      ownFleets={[]}
      {...propOverrides}
    />,
  );
}

describe("FleetDetail", () => {
  it("shows the fleet name as the primary heading for owned fleets", () => {
    renderFleetDetail();

    const heading = screen.getByRole("heading", { name: "Fleet #1" });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveAttribute("title", "Fleet ID: FL001");
  });

  it("does not show a rename button for enemy fleets", () => {
    renderFleetDetail({ owner: "sara", name: null });

    expect(screen.getByRole("heading", { name: "Enemy Fleet" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /rename/i })).not.toBeInTheDocument();
  });

  it("shows a prefilled input when fleet rename mode is active", () => {
    renderFleetDetail();

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));

    expect(screen.getByRole("textbox", { name: /fleet name/i })).toHaveValue("Fleet #1");
  });

  it("keeps fleet id in the heading tooltip instead of visible metadata", () => {
    renderFleetDetail();

    expect(screen.getByRole("heading", { name: "Fleet #1" })).toHaveAttribute(
      "title",
      "Fleet ID: FL001",
    );
    expect(screen.queryByText("FL001")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "FL001" })).not.toBeInTheDocument();
  });

  it("blocks saving an empty fleet rename", () => {
    const { addCommand } = renderFleetDetail();

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    fireEvent.change(screen.getByRole("textbox", { name: /fleet name/i }), {
      target: { value: "   " },
    });

    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
    fireEvent.keyDown(screen.getByRole("textbox", { name: /fleet name/i }), {
      key: "Enter",
    });
    expect(addCommand).not.toHaveBeenCalled();
  });

  it("supports Enter to save and Escape to cancel fleet rename", () => {
    const { addCommand } = renderFleetDetail();

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    fireEvent.change(screen.getByRole("textbox", { name: /fleet name/i }), {
      target: { value: "Vanguard" },
    });

    fireEvent.keyDown(screen.getByRole("textbox", { name: /fleet name/i }), {
      key: "Enter",
    });

    expect(addCommand).toHaveBeenCalledWith({
      type: "rename_fleet",
      fleetId: "FL001",
      name: "Vanguard",
    });
  });

  it("cancels fleet rename locally on Escape", () => {
    renderFleetDetail();

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    fireEvent.keyDown(screen.getByRole("textbox", { name: /fleet name/i }), {
      key: "Escape",
    });

    expect(screen.queryByRole("textbox", { name: /fleet name/i })).not.toBeInTheDocument();
  });

  it("resets local rename state when the selected fleet changes", () => {
    const { rerender } = renderWithCommands(
      <FleetDetail
        key="FL001"
        fleet={makeFleet()}
        currentPlayer="tim"
        designs={[]}
        knownPlanets={[]}
        onWaypointEditorStateChange={vi.fn()}
        ownFleets={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    expect(screen.getByRole("textbox", { name: /fleet name/i })).toBeInTheDocument();

    rerender(
      <GameCommandsContext.Provider
        value={{
          basePlayerState: { player: "tim", turn: 1, planets: [], designs: [], events: [], fleets: [] },
          addCommand: vi.fn(),
          replaceCommands: vi.fn(),
        }}
      >
        <FleetDetail
          key="FL002"
          fleet={makeFleet({ id: "FL002", name: "Fleet #2" })}
          currentPlayer="tim"
          designs={[]}
          knownPlanets={[]}
          onWaypointEditorStateChange={vi.fn()}
          ownFleets={[]}
        />
      </GameCommandsContext.Provider>,
    );

    expect(screen.queryByRole("textbox", { name: /fleet name/i })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Fleet #2" })).toBeInTheDocument();
  });

  it("renders task chip for waypoint with transport task", () => {
    renderFleetDetail({
      waypoints: [
        {
          x: 536_870_912,
          y: 536_870_912,
          warp: 5,
          task: { type: "transport", orders: [{ action: "load_all", cargoType: "ironium" }] },
        },
      ],
    });

    expect(screen.getByText("Transport")).toBeInTheDocument();
  });

  it("renders task chip for waypoint with transfer task", () => {
    renderFleetDetail({
      waypoints: [
        {
          x: 536_870_912,
          y: 536_870_912,
          warp: 5,
          task: { type: "transfer", orders: [], fleetId: "FL002" },
        },
      ],
    });

    expect(screen.getByText("Transfer")).toBeInTheDocument();
  });

  it("renders task chip for waypoint with colonise task", () => {
    renderFleetDetail({
      waypoints: [
        {
          x: 536_870_912,
          y: 536_870_912,
          warp: 5,
          task: { type: "colonise", orders: [] },
        },
      ],
    });

    expect(screen.getByText("Colonise")).toBeInTheDocument();
  });

  it("shows the planet name for waypoint destinations that match a planet", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 5, task: null }],
      },
      {
        knownPlanets: [
          { id: "PL001", name: "New London", x: 536_870_912, y: 536_870_912 },
        ],
      },
    );

    expect(screen.getByText(/New London/)).toBeInTheDocument();
    expect(screen.queryByText(/\(1,\s*1\)/)).not.toBeInTheDocument();
  });

  it("shows repeat toggle in waypoint edit mode", () => {
    renderFleetDetail(
      { waypoints: [] },
      {},
    );

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));

    expect(screen.getByLabelText(/repeat route/i)).toBeInTheDocument();
  });

  it("disables Done when waypoint orders are incomplete", () => {
    renderFleetDetail({
      waypoints: [
        {
          x: 536_870_912,
          y: 536_870_912,
          warp: 5,
          task: {
            type: "transport",
            orders: [{ action: "load_amount", cargoType: null, amount: null }],
          },
        },
      ],
    });

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));

    expect(screen.getByRole("button", { name: /fix errors to save/i })).toBeDisabled();
  });

  it("shows repeating route indicator when fleet.repeat is true and not editing", () => {
    renderFleetDetail({ repeat: true });

    expect(screen.getByLabelText(/repeat route/i)).toBeChecked();
    expect(screen.getByLabelText(/repeat route/i)).toBeDisabled();
  });

  it("shows cargo contents for owned fleets with cargo capacity", () => {
    renderFleetDetail({
      cargoCapacity: 100,
      cargo: {
        ironium: 12,
        boranium: 7,
        germanium: 3,
        colonists: 20,
      },
    });

    expect(screen.getByText("Cargo:")).toBeInTheDocument();
    expect(screen.getByText("42 / 100 used")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Resource bars" })).toBeInTheDocument();
  });

  it("does not show cargo card when fleet has no cargo capacity", () => {
    renderFleetDetail({
      cargoCapacity: 0,
      cargo: {
        ironium: 12,
        boranium: 7,
        germanium: 3,
        colonists: 20,
      },
    });

    expect(screen.queryByText("Cargo:")).not.toBeInTheDocument();
  });

  it("clicking the no-task pill opens the task type popover for that waypoint", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 5, task: null }],
      },
      {
        onWaypointEditorStateChange: vi.fn(),
      },
    );

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));
    expect(screen.queryByRole("dialog", { name: /waypoint task type/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /no task/i }));
    expect(screen.getByRole("dialog", { name: /waypoint task type/i })).toBeInTheDocument();
  });

  it("switching from Transport to Transfer resets the task payload", () => {
    renderFleetDetail(
      {
        waypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            warp: 5,
            task: { type: "transport", orders: [{ action: "load_all", cargoType: "ironium" }] },
          },
        ],
      },
      {},
    );

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));
    fireEvent.click(screen.getByRole("button", { name: /^transport$/i }));
    fireEvent.click(screen.getAllByRole("button", { name: /^transfer$/i })[0]);
    expect(screen.getByText("Transfer")).toBeInTheDocument();
  });

  it("switching task type to None clears the task", () => {
    renderFleetDetail(
      {
        waypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            warp: 5,
            task: { type: "transport", orders: [] },
          },
        ],
      },
      {},
    );

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));
    fireEvent.click(screen.getByRole("button", { name: /^transport$/i }));
    fireEvent.click(screen.getAllByRole("button", { name: /^none$/i })[0]);
    expect(screen.getByText("No task")).toBeInTheDocument();
  });

  it("does not open a lower editor panel for colonise tasks", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 5, task: { type: "colonise", orders: [] } }],
      },
      {
        onWaypointEditorStateChange: vi.fn(),
      },
    );

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));
    fireEvent.click(screen.getByRole("button", { name: /^colonise$/i }));
    fireEvent.click(screen.getAllByRole("button", { name: /^colonise$/i })[1]);
    expect(screen.queryByRole("button", { name: /close/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/Colonise tasks are resolved by the backend/i)).not.toBeInTheDocument();
  });

  it("shows transport orders even outside edit mode", () => {
    renderFleetDetail({
      waypoints: [
        {
          x: 536_870_912,
          y: 536_870_912,
          warp: 5,
          task: { type: "transport", orders: [{ action: "load_all", cargoType: "ironium" }] },
        },
      ],
    });

    expect(screen.getByText("Load all")).toBeInTheDocument();
    expect(screen.getByText("Ironium")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /\+ add order/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /close/i })).not.toBeInTheDocument();
  });

  it("shows transfer orders even outside edit mode", () => {
    renderFleetDetail(
      {
        waypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            warp: 5,
            task: { type: "transfer", orders: [], fleetId: "FL002" },
          },
        ],
      },
      {
        ownFleets: [{ id: "FL002", owner: "tim", position: { x: 0, y: 0 } }],
      },
    );

    expect(screen.getByText("FL002")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /\+ add order/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /close/i })).not.toBeInTheDocument();
  });

  it("shows fleet names for transfer task targets when available", () => {
    renderFleetDetail(
      {
        waypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            warp: 5,
            task: { type: "transfer", orders: [], fleetId: "FL002" },
          },
        ],
      },
      {
        ownFleets: [{ id: "FL002", owner: "tim", name: "Vanguard", position: { x: 0, y: 0 } }],
      },
    );

    expect(screen.getByText("Vanguard")).toBeInTheDocument();
  });

  it("shows fuel bar for own fleets with fuel capacity", () => {
    renderFleetDetail({ fuel: 450, fuelCapacity: 600 });

    expect(screen.getByRole("img", { name: "Fuel bar" })).toBeInTheDocument();
  });

  it("does not show fuel bar for enemy fleets", () => {
    renderFleetDetail({ owner: "sara", fuel: 450, fuelCapacity: 600 });

    expect(screen.queryByRole("img", { name: "Fuel bar" })).not.toBeInTheDocument();
  });

  it("does not show fuel bar when fuelCapacity is 0", () => {
    renderFleetDetail({ fuel: 0, fuelCapacity: 0 });

    expect(screen.queryByRole("img", { name: "Fuel bar" })).not.toBeInTheDocument();
  });

  it("adding a waypoint sets warp 5 by default", async () => {
    const onWaypointEditorStateChange = vi.fn<(state: WaypointEditorState) => void>();
    renderFleetDetail({ waypoints: [] }, { onWaypointEditorStateChange });

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));

    const stateInEditMode = onWaypointEditorStateChange.mock.calls.at(-1)?.[0];
    await act(async () => {
      stateInEditMode?.onAddWaypoint?.({ x: 536_870_912, y: 536_870_912 });
    });

    const callAfterAdd = onWaypointEditorStateChange.mock.calls.at(-1)?.[0];
    expect(callAfterAdd?.editedWaypoints?.[0]).toMatchObject({ warp: 5 });
  });

  it("shows warp value in read mode", () => {
    renderFleetDetail({
      waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 7, task: null }],
    });

    expect(screen.getByText("W7")).toBeInTheDocument();
  });

  it("shows warp input in edit mode", () => {
    renderFleetDetail({
      waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 6, task: null }],
    });

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));

    expect(screen.getByRole("spinbutton", { name: /warp for waypoint 1/i })).toHaveValue(6);
  });

  it("changing warp in edit mode updates editedWaypoints", () => {
    const onWaypointEditorStateChange = vi.fn<(state: WaypointEditorState) => void>();
    renderFleetDetail(
      { waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 5, task: null }] },
      { onWaypointEditorStateChange },
    );

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));
    fireEvent.change(screen.getByRole("spinbutton", { name: /warp for waypoint 1/i }), {
      target: { value: "8" },
    });

    const lastCall = onWaypointEditorStateChange.mock.calls.at(-1)?.[0];
    expect(lastCall?.editedWaypoints?.[0]).toMatchObject({ warp: 8 });
  });

  it("saved command payload includes warp on each waypoint", () => {
    const { addCommand } = renderFleetDetail({
      waypoints: [{ x: 536_870_912, y: 536_870_912, warp: 5, task: null }],
    });

    fireEvent.click(screen.getByRole("button", { name: /edit waypoints/i }));
    fireEvent.change(screen.getByRole("spinbutton", { name: /warp for waypoint 1/i }), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /done/i }));

    expect(addCommand).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "set_waypoints",
        waypoints: expect.arrayContaining([
          expect.objectContaining({ warp: 9 }),
        ]),
      }),
    );
  });

  it("uses warp squared formula for estimated turns", () => {
    // At warp 4, budget = 16 parsecs/turn. Distance = 16 parsecs → 1 turn.
    renderFleetDetail({
      position: { x: 0, y: 0 },
      waypoints: [{ x: 16 * 536_870_912, y: 0, warp: 4, task: null }],
    });

    expect(screen.getByText(/~1 turn/)).toBeInTheDocument();
  });
});
