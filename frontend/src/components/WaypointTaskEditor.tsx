import type { CargoOrder, PlayerFleet } from "../types";
import { cn } from "../lib/utils";
import { AMOUNT_REQUIRED_ACTIONS } from "../lib/waypointValidation";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ACTION_LABELS: Record<CargoOrder["action"], string> = {
  load_all: "Load all",
  load_amount: "Load amount",
  load_up_to: "Load up to",
  unload_all: "Unload all",
  unload_amount: "Unload amount",
  unload_but: "Unload, keep",
};

const CARGO_TYPE_LABELS: Record<CargoOrder["cargoType"], string> = {
  ironium: "Ironium",
  boranium: "Boranium",
  germanium: "Germanium",
  colonists: "Colonists",
};

// ---------------------------------------------------------------------------
// Shared cargo orders list
// ---------------------------------------------------------------------------

function CargoOrdersEditor({
  orders,
  onChange,
  validationErrors,
  idPrefix,
}: {
  orders: CargoOrder[];
  onChange: (orders: CargoOrder[]) => void;
  validationErrors: Record<string, string>;
  idPrefix: string;
}) {
  function updateOrder(index: number, patch: Partial<CargoOrder>) {
    onChange(
      orders.map((o, i) =>
        i === index ? ({ ...o, ...patch } as CargoOrder) : o,
      ),
    );
  }

  function removeOrder(index: number) {
    onChange(orders.filter((_, i) => i !== index));
  }

  function addOrder() {
    onChange([...orders, { action: "load_all", cargoType: "ironium" }]);
  }

  return (
    <div className="space-y-2">
      {orders.map((order, i) => {
        const needsAmount = AMOUNT_REQUIRED_ACTIONS.has(order.action);
        const amountError = validationErrors[`${idPrefix}-order-${i}-amount`];
        return (
          <div key={i} className="space-y-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <select
                value={order.action}
                onChange={(e) =>
                  updateOrder(i, { action: e.target.value as CargoOrder["action"] })
                }
                className="rounded border border-[var(--color-panel-border)] bg-black/30 px-1.5 py-0.5 text-xs text-foreground"
              >
                {(Object.keys(ACTION_LABELS) as CargoOrder["action"][]).map(
                  (action) => (
                    <option key={action} value={action}>
                      {ACTION_LABELS[action]}
                    </option>
                  ),
                )}
              </select>
              <select
                value={order.cargoType}
                onChange={(e) =>
                  updateOrder(i, {
                    cargoType: e.target.value as CargoOrder["cargoType"],
                  })
                }
                className="rounded border border-[var(--color-panel-border)] bg-black/30 px-1.5 py-0.5 text-xs text-foreground"
              >
                {(
                  Object.keys(CARGO_TYPE_LABELS) as CargoOrder["cargoType"][]
                ).map((ct) => (
                  <option key={ct} value={ct}>
                    {CARGO_TYPE_LABELS[ct]}
                  </option>
                ))}
              </select>
              {needsAmount && (
                <input
                  type="number"
                  min={1}
                  value={order.amount ?? ""}
                  onChange={(e) =>
                    updateOrder(i, {
                      amount: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  placeholder="Amount"
                  className={cn(
                    "w-20 rounded border bg-black/30 px-1.5 py-0.5 text-xs text-foreground",
                    amountError
                      ? "border-red-500"
                      : "border-[var(--color-panel-border)]",
                  )}
                />
              )}
              <button
                onClick={() => removeOrder(i)}
                className="ml-auto text-xs text-red-400 hover:text-red-300"
                aria-label="Remove order"
              >
                ✕
              </button>
            </div>
            {amountError && (
              <p className="text-xs text-red-400">{amountError}</p>
            )}
          </div>
        );
      })}
      <button
        onClick={addOrder}
        className="text-xs text-blue-400 hover:text-blue-300"
      >
        + Add order
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TransportTaskEditor
// ---------------------------------------------------------------------------

export function TransportTaskEditor({
  orders,
  onChange,
  validationErrors = {},
}: {
  orders: CargoOrder[];
  onChange: (orders: CargoOrder[]) => void;
  validationErrors?: Record<string, string>;
}) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">Cargo orders</p>
      <CargoOrdersEditor
        orders={orders}
        onChange={onChange}
        validationErrors={validationErrors}
        idPrefix="transport"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// TransferTaskEditor
// ---------------------------------------------------------------------------

export function TransferTaskEditor({
  fleetId,
  orders,
  ownFleets,
  onChange,
  validationErrors = {},
}: {
  fleetId: string | null;
  orders: CargoOrder[];
  ownFleets: PlayerFleet[];
  onChange: (fleetId: string | null, orders: CargoOrder[]) => void;
  validationErrors?: Record<string, string>;
}) {
  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Target fleet
        </label>
        <select
          value={fleetId ?? ""}
          onChange={(e) => onChange(e.target.value || null, orders)}
          className={cn(
            "w-full rounded border bg-black/30 px-1.5 py-0.5 text-xs text-foreground",
            validationErrors["fleetId"]
              ? "border-red-500"
              : "border-[var(--color-panel-border)]",
          )}
        >
          <option value="">Select fleet…</option>
          {ownFleets.map((f) => (
            <option key={f.id} value={f.id}>
              {f.id}
            </option>
          ))}
        </select>
        {validationErrors["fleetId"] && (
          <p className="text-xs text-red-400">{validationErrors["fleetId"]}</p>
        )}
        <p className="text-xs text-muted-foreground/70">
          Target fleet must be at this location at resolution time — if absent,
          task is skipped
        </p>
      </div>
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">
          Transfer orders
        </p>
        <CargoOrdersEditor
          orders={orders}
          onChange={(newOrders) => onChange(fleetId, newOrders)}
          validationErrors={validationErrors}
          idPrefix="transfer"
        />
      </div>
    </div>
  );
}
