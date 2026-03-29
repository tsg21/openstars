/**
 * snake_case ↔ camelCase conversion utilities.
 *
 * Used by the API client to convert between the Python backend's snake_case
 * and the TypeScript frontend's camelCase conventions.
 */

/** Convert a snake_case string to camelCase. */
export function snakeToCamel(s: string): string {
  return s.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
}

/** Convert a camelCase string to snake_case. */
export function camelToSnake(s: string): string {
  return s.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

/** Recursively convert all keys in a value from snake_case to camelCase. */
export function keysToCamel(val: unknown): unknown {
  if (Array.isArray(val)) return val.map(keysToCamel);
  if (val !== null && typeof val === "object") {
    const obj = val as Record<string, unknown>;
    const result: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj)) {
      result[snakeToCamel(k)] = keysToCamel(v);
    }
    return result;
  }
  return val;
}

/** Recursively convert all keys in a value from camelCase to snake_case. */
export function keysToSnake(val: unknown): unknown {
  if (Array.isArray(val)) return val.map(keysToSnake);
  if (val !== null && typeof val === "object") {
    const obj = val as Record<string, unknown>;
    const result: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj)) {
      result[camelToSnake(k)] = keysToSnake(v);
    }
    return result;
  }
  return val;
}
