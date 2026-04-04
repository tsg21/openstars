import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FleetDetail } from "./FleetDetail";
import type { PlayerCommand } from "../types";

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
  return render(
    <FleetDetail
      fleet={makeFleet(fleetOverrides)}
      currentPlayer="tim"
      designs={[]}
      knownPlanets={[]}
      waypointEditMode={false}
      editedWaypoints={null}
      editRepeat={false}
      onEnterWaypointMode={vi.fn()}
      onExitWaypointMode={vi.fn()}
      onNewCommand={vi.fn<(command: PlayerCommand) => void>()}
      onRemoveWaypoint={vi.fn()}
      onClearAllWaypoints={vi.fn()}
      onToggleRepeat={vi.fn()}
      onUpdateWaypointTask={vi.fn()}
      waypointValidationErrors={{}}
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
    const onNewCommand = vi.fn();

    renderFleetDetail({}, { onNewCommand });

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    fireEvent.change(screen.getByRole("textbox", { name: /fleet name/i }), {
      target: { value: "   " },
    });

    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
    fireEvent.keyDown(screen.getByRole("textbox", { name: /fleet name/i }), {
      key: "Enter",
    });
    expect(onNewCommand).not.toHaveBeenCalled();
  });

  it("supports Enter to save and Escape to cancel fleet rename", () => {
    const onNewCommand = vi.fn();

    renderFleetDetail({}, { onNewCommand });

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    fireEvent.change(screen.getByRole("textbox", { name: /fleet name/i }), {
      target: { value: "Vanguard" },
    });

    fireEvent.keyDown(screen.getByRole("textbox", { name: /fleet name/i }), {
      key: "Enter",
    });

    expect(onNewCommand).toHaveBeenCalledWith({
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
    const { rerender } = render(
      <FleetDetail
        key="FL001"
        fleet={makeFleet()}
        currentPlayer="tim"
        designs={[]}
        knownPlanets={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        editRepeat={false}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onNewCommand={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onToggleRepeat={vi.fn()}
        onUpdateWaypointTask={vi.fn()}
        waypointValidationErrors={{}}
        ownFleets={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /rename/i }));
    expect(screen.getByRole("textbox", { name: /fleet name/i })).toBeInTheDocument();

    rerender(
      <FleetDetail
        key="FL002"
        fleet={makeFleet({ id: "FL002", name: "Fleet #2" })}
        currentPlayer="tim"
        designs={[]}
        knownPlanets={[]}
        waypointEditMode={false}
        editedWaypoints={null}
        editRepeat={false}
        onEnterWaypointMode={vi.fn()}
        onExitWaypointMode={vi.fn()}
        onNewCommand={vi.fn()}
        onRemoveWaypoint={vi.fn()}
        onClearAllWaypoints={vi.fn()}
        onToggleRepeat={vi.fn()}
        onUpdateWaypointTask={vi.fn()}
        waypointValidationErrors={{}}
        ownFleets={[]}
      />,
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
          task: { type: "colonise", orders: [] },
        },
      ],
    });

    expect(screen.getByText("Colonise")).toBeInTheDocument();
  });

  it("shows the planet name for waypoint destinations that match a planet", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
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
      { waypointEditMode: true, editedWaypoints: [] },
    );

    expect(screen.getByLabelText(/repeat route/i)).toBeInTheDocument();
  });

  it("disables Done when waypoint orders are incomplete", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
      },
      {
        waypointEditMode: true,
        editedWaypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
        waypointValidationErrors: { "waypoint-0-transport-order-0-cargoType": "Required" },
      },
    );

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
        waypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
      },
      {
        waypointEditMode: true,
        editedWaypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
      },
    );

    expect(screen.queryByRole("dialog", { name: /waypoint task type/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /no task/i }));
    expect(screen.getByRole("dialog", { name: /waypoint task type/i })).toBeInTheDocument();
  });

  it("switching from Transport to Transfer resets the task payload", () => {
    const onUpdateWaypointTask = vi.fn();

    renderFleetDetail(
      {
        waypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            task: { type: "transport", orders: [{ action: "load_all", cargoType: "ironium" }] },
          },
        ],
      },
      {
        waypointEditMode: true,
        editedWaypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            task: { type: "transport", orders: [{ action: "load_all", cargoType: "ironium" }] },
          },
        ],
        onUpdateWaypointTask,
      },
    );

    fireEvent.click(screen.getByRole("button", { name: /^transport$/i }));
    fireEvent.click(screen.getAllByRole("button", { name: /^transfer$/i })[0]);
    expect(onUpdateWaypointTask).toHaveBeenCalledWith(0, {
      type: "transfer",
      orders: [],
    });
  });

  it("switching task type to None clears the task", () => {
    const onUpdateWaypointTask = vi.fn();

    renderFleetDetail(
      {
        waypoints: [
          {
            x: 536_870_912,
            y: 536_870_912,
            task: { type: "transport", orders: [] },
          },
        ],
      },
      {
        waypointEditMode: true,
        editedWaypoints: [
          { x: 536_870_912, y: 536_870_912, task: { type: "transport", orders: [] } },
        ],
        onUpdateWaypointTask,
      },
    );

    fireEvent.click(screen.getByRole("button", { name: /^transport$/i }));
    fireEvent.click(screen.getAllByRole("button", { name: /^none$/i })[0]);
    expect(onUpdateWaypointTask).toHaveBeenCalledWith(0, null);
  });

  it("does not open a lower editor panel for colonise tasks", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, task: { type: "colonise", orders: [] } }],
      },
      {
        waypointEditMode: true,
        editedWaypoints: [
          { x: 536_870_912, y: 536_870_912, task: { type: "colonise", orders: [] } },
        ],
      },
    );

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
});
