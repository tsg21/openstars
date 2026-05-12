import type { CargoOrder, PlayerFleet } from "../../types";
import { cn } from "../../lib/utils";
import { AMOUNT_REQUIRED_ACTIONS } from "../../lib/waypointValidation";
import { CompactInput, CompactSelect } from "../ui/FormField";

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

const CARGO_TYPE_LABELS = {
  ironium: "Ironium",
  boranium: "Boranium",
  germanium: "Germanium",
  colonists: "Colonists",
} as const;

function getCargoTypeLabel(cargoType: CargoOrder["cargoType"]): string {
  if (!cargoType) {
    return "Select...";
  }

  return CARGO_TYPE_LABELS[cargoType];
}

function getFleetLabel(fleet: Pick<PlayerFleet, "id" | "name">): string {
  return fleet.name?.trim() || fleet.id;
}

// ---------------------------------------------------------------------------
// Shared cargo orders list
// ---------------------------------------------------------------------------

function CargoOrdersEditor({
  orders,
  onChange,
  validationErrors,
  idPrefix,
  disabled = false,
}: {
  orders: CargoOrder[];
  onChange: (orders: CargoOrder[]) => void;
  validationErrors: Record<string, string>;
  idPrefix: string;
  disabled?: boolean;
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
    onChange([...orders, { action: "load_all", cargoType: null }]);
  }

  return (
    <div className="space-y-2">
      {orders.map((order, i) => {
        const needsAmount = AMOUNT_REQUIRED_ACTIONS.has(order.action);
        const amountError = validationErrors[`${idPrefix}-order-${i}-amount`];
        const cargoTypeError = validationErrors[`${idPrefix}-order-${i}-cargoType`];
        return (
          <div key={i} className="space-y-1">
            {disabled ? (
              <div className="flex items-center gap-2 text-xs text-foreground">
                <span>{ACTION_LABELS[order.action]}</span>
                <span className="text-muted-foreground">·</span>
                <span>{getCargoTypeLabel(order.cargoType)}</span>
                {needsAmount && (
                  <>
                    <span className="text-muted-foreground">·</span>
                    <span>{order.amount ?? "Unset"}</span>
                  </>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-1.5 flex-wrap">
                <CompactSelect
                  value={order.action}
                  onChange={(e) =>
                    updateOrder(i, { action: e.target.value as CargoOrder["action"] })
                  }
                  disabled={disabled}
                >
                  {(Object.keys(ACTION_LABELS) as CargoOrder["action"][]).map(
                    (action) => (
                      <option key={action} value={action}>
                        {ACTION_LABELS[action]}
                      </option>
                    ),
                  )}
                </CompactSelect>
                <CompactSelect
                  value={order.cargoType ?? ""}
                  onChange={(e) =>
                    updateOrder(i, {
                      cargoType: e.target.value
                        ? (e.target.value as NonNullable<CargoOrder["cargoType"]>)
                        : null,
                    })
                  }
                  disabled={disabled}
                  className={cargoTypeError ? "border-red-500" : undefined}
                >
                  <option value="">Select...</option>
                  {(
                    Object.keys(CARGO_TYPE_LABELS) as Array<keyof typeof CARGO_TYPE_LABELS>
                  ).map((ct) => (
                    <option key={ct} value={ct}>
                      {CARGO_TYPE_LABELS[ct]}
                    </option>
                  ))}
                </CompactSelect>
                {needsAmount && (
                  <CompactInput
                    type="number"
                    min={1}
                    value={order.amount ?? ""}
                    onChange={(e) =>
                      updateOrder(i, {
                        amount: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                    disabled={disabled}
                    placeholder="Amount"
                    className={cn("w-20", amountError ? "border-red-500" : undefined)}
                  />
                )}
                <button
                  onClick={() => removeOrder(i)}
                  disabled={disabled}
                  className="ml-auto text-xs text-red-400 hover:text-red-300"
                  aria-label="Remove order"
                >
                  ✕
                </button>
              </div>
            )}
            {amountError && (
              <p className="text-xs text-red-400">{amountError}</p>
            )}
            {cargoTypeError && (
              <p className="text-xs text-red-400">{cargoTypeError}</p>
            )}
          </div>
        );
      })}
      {!disabled && (
        <button
          onClick={addOrder}
          disabled={disabled}
          className="text-xs text-blue-400 hover:text-blue-300"
        >
          + Add order
        </button>
      )}
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
  disabled = false,
}: {
  orders: CargoOrder[];
  onChange: (orders: CargoOrder[]) => void;
  validationErrors?: Record<string, string>;
  disabled?: boolean;
}) {
  return (
    <div>
      <CargoOrdersEditor
        orders={orders}
        onChange={onChange}
        validationErrors={validationErrors}
        idPrefix="transport"
        disabled={disabled}
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
  disabled = false,
}: {
  fleetId: string | null;
  orders: CargoOrder[];
  ownFleets: PlayerFleet[];
  onChange: (fleetId: string | null, orders: CargoOrder[]) => void;
  validationErrors?: Record<string, string>;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Target fleet
        </label>
        {disabled ? (
          <div className="text-xs text-foreground">
            {ownFleets.find((fleet) => fleet.id === fleetId)?.name?.trim() ||
              fleetId ||
              "Select fleet…"}
          </div>
        ) : (
          <CompactSelect
            value={fleetId ?? ""}
            onChange={(e) => onChange(e.target.value || null, orders)}
            disabled={disabled}
            className={cn("w-full", validationErrors["fleetId"] ? "border-red-500" : undefined)}
          >
            <option value="">Select fleet…</option>
            {ownFleets.map((f) => (
              <option key={f.id} value={f.id}>
                {getFleetLabel(f)}
              </option>
            ))}
          </CompactSelect>
        )}
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
          disabled={disabled}
        />
      </div>
    </div>
  );
}
