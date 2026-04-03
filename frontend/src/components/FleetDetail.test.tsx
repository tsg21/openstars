import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FleetDetail } from "./FleetDetail";

function makeFleet(overrides: Record<string, unknown> = {}) {
  return {
    id: "FL001",
    owner: "tim",
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

  it("shows repeating route indicator when fleet.repeat is true and not editing", () => {
    renderFleetDetail({ repeat: true });

    expect(screen.getByText("Repeating route")).toBeInTheDocument();
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

  it("clicking the no-task pill opens the inline editor for that waypoint", () => {
    renderFleetDetail(
      {
        waypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
      },
      {
        waypointEditMode: true,
        editedWaypoints: [{ x: 536_870_912, y: 536_870_912, task: null }],
      },
    );

    expect(screen.queryByText("Task type:")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /no task/i }));
    expect(screen.getByText("Task type:")).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole("button", { name: /transport/i }));
    fireEvent.click(screen.getByRole("button", { name: /transfer/i }));
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

    fireEvent.click(screen.getAllByRole("button", { name: /^transport$/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /^none$/i }));
    expect(onUpdateWaypointTask).toHaveBeenCalledWith(0, null);
  });

  it("shows read-only messaging for existing colonise tasks in edit mode", () => {
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

    fireEvent.click(screen.getByRole("button", { name: /colonise/i }));
    expect(screen.getByText(/Colonise tasks are resolved by the backend/i)).toBeInTheDocument();
  });
});
