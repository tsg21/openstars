import type { CargoOrder } from "../types";

export const AMOUNT_REQUIRED_ACTIONS = new Set<CargoOrder["action"]>([
  "load_amount",
  "load_up_to",
  "unload_amount",
  "unload_but",
]);

export function validateTransportOrders(
  orders: CargoOrder[],
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (let i = 0; i < orders.length; i++) {
    const order = orders[i];
    if (AMOUNT_REQUIRED_ACTIONS.has(order.action)) {
      if (order.amount == null || order.amount <= 0) {
        errors[`order-${i}-amount`] = "Amount must be a positive number";
      }
    }
  }
  return errors;
}

export function validateTransferTask(
  fleetId: string | null,
  orders: CargoOrder[],
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!fleetId) {
    errors["fleetId"] = "Target fleet is required";
  }
  Object.assign(errors, validateTransportOrders(orders));
  return errors;
}
