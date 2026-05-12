import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  TransportTaskEditor,
  TransferTaskEditor,
} from "./WaypointTaskEditor";
import type { CargoOrder } from "../../types";
import { validateTransportOrders, validateTransferTask } from "../../lib/waypointValidation";

// ---------------------------------------------------------------------------
// TransportTaskEditor
// ---------------------------------------------------------------------------

describe("TransportTaskEditor", () => {
  it("renders all action types in the action dropdown", () => {
    render(<TransportTaskEditor orders={[{ action: "load_all", cargoType: "ironium" }]} onChange={vi.fn()} />);
    const select = screen.getByDisplayValue("Load all");
    expect(select).toBeInTheDocument();
    fireEvent.change(select, { target: { value: "unload_amount" } });
  });

  it("shows amount input only for actions that require it", () => {
    const orders: CargoOrder[] = [{ action: "load_all", cargoType: "ironium" }];
    const { rerender } = render(
      <TransportTaskEditor orders={orders} onChange={vi.fn()} />,
    );
    expect(screen.queryByPlaceholderText("Amount")).not.toBeInTheDocument();

    rerender(
      <TransportTaskEditor
        orders={[{ action: "load_amount", cargoType: "ironium", amount: 10 }]}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("Amount")).toBeInTheDocument();
  });

  it("does not show amount input for load_up_to action (renders it)", () => {
    render(
      <TransportTaskEditor
        orders={[{ action: "load_up_to", cargoType: "germanium", amount: 5 }]}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("Amount")).toBeInTheDocument();
  });

  it("add order appends a default load_all / ironium order", () => {
    const onChange = vi.fn();
    render(<TransportTaskEditor orders={[]} onChange={onChange} />);
    fireEvent.click(screen.getByText("+ Add order"));
    expect(onChange).toHaveBeenCalledWith([
      { action: "load_all", cargoType: null },
    ]);
  });

  it("shows an unset cargo placeholder when cargo type is not chosen yet", () => {
    render(
      <TransportTaskEditor
        orders={[{ action: "load_all", cargoType: null }]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByDisplayValue("Select...")).toBeInTheDocument();
  });

  it("renders read-only text instead of controls when disabled", () => {
    render(
      <TransportTaskEditor
        orders={[{ action: "load_amount", cargoType: "ironium", amount: 25 }]}
        onChange={vi.fn()}
        disabled
      />,
    );

    expect(screen.getByText("Load amount")).toBeInTheDocument();
    expect(screen.getByText("Ironium")).toBeInTheDocument();
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /\+ add order/i })).not.toBeInTheDocument();
  });

  it("remove order removes at the correct index", () => {
    const onChange = vi.fn();
    const orders: CargoOrder[] = [
      { action: "load_all", cargoType: "ironium" },
      { action: "unload_all", cargoType: "germanium" },
    ];
    render(<TransportTaskEditor orders={orders} onChange={onChange} />);
    const removeButtons = screen.getAllByRole("button", { name: "Remove order" });
    fireEvent.click(removeButtons[0]);
    expect(onChange).toHaveBeenCalledWith([
      { action: "unload_all", cargoType: "germanium" },
    ]);
  });
});

// ---------------------------------------------------------------------------
// validateTransportOrders
// ---------------------------------------------------------------------------

describe("validateTransportOrders", () => {
  it("returns no errors for load_all (no amount required)", () => {
    const errors = validateTransportOrders([
      { action: "load_all", cargoType: "ironium" },
    ]);
    expect(Object.keys(errors)).toHaveLength(0);
  });

  it("returns error when load_amount is missing amount", () => {
    const errors = validateTransportOrders([
      { action: "load_amount", cargoType: "germanium" },
    ]);
    expect(errors["order-0-amount"]).toBeDefined();
  });

  it("returns error when amount is 0", () => {
    const errors = validateTransportOrders([
      { action: "unload_amount", cargoType: "boranium", amount: 0 },
    ]);
    expect(errors["order-0-amount"]).toBeDefined();
  });

  it("returns no errors when amount-requiring action has valid amount", () => {
    const errors = validateTransportOrders([
      { action: "load_up_to", cargoType: "germanium", amount: 50 },
    ]);
    expect(Object.keys(errors)).toHaveLength(0);
  });

  it("returns error when cargo type is missing", () => {
    const errors = validateTransportOrders([
      { action: "load_all", cargoType: null },
    ]);
    expect(errors["order-0-cargoType"]).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// TransferTaskEditor
// ---------------------------------------------------------------------------

describe("TransferTaskEditor", () => {
  it("shows fleet dropdown populated with own fleets", () => {
    render(
      <TransferTaskEditor
        fleetId={null}
        orders={[]}
        ownFleets={[
          { id: "FL001", owner: "alice", name: "Fleet #1", position: { x: 0, y: 0 } },
          { id: "FL002", owner: "alice", name: "Vanguard", position: { x: 0, y: 0 } },
        ]}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByDisplayValue("Select fleet…")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Fleet #1" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Vanguard" })).toBeInTheDocument();
  });

  it("calls onChange with selected fleet id", () => {
    const onChange = vi.fn();
    render(
      <TransferTaskEditor
        fleetId={null}
        orders={[]}
        ownFleets={[{ id: "FL001", owner: "alice", name: "Fleet #1", position: { x: 0, y: 0 } }]}
        onChange={onChange}
      />,
    );
    fireEvent.change(screen.getByDisplayValue("Select fleet…"), {
      target: { value: "FL001" },
    });
    expect(onChange).toHaveBeenCalledWith("FL001", []);
  });

  it("renders selected fleet as read-only text when disabled", () => {
    render(
      <TransferTaskEditor
        fleetId="FL001"
        orders={[]}
        ownFleets={[{ id: "FL001", owner: "alice", name: "Fleet #1", position: { x: 0, y: 0 } }]}
        onChange={vi.fn()}
        disabled
      />,
    );

    expect(screen.getByText("Fleet #1")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// validateTransferTask
// ---------------------------------------------------------------------------

describe("validateTransferTask", () => {
  it("returns error when fleetId is null", () => {
    const errors = validateTransferTask(null, []);
    expect(errors["fleetId"]).toBeDefined();
  });

  it("returns no fleetId error when fleetId is set", () => {
    const errors = validateTransferTask("FL001", []);
    expect(errors["fleetId"]).toBeUndefined();
  });

  it("also validates orders within the transfer task", () => {
    const errors = validateTransferTask("FL001", [
      { action: "load_amount", cargoType: "ironium" },
    ]);
    expect(errors["order-0-amount"]).toBeDefined();
  });
});
