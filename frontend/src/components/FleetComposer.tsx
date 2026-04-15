import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import type { Design, DesignSummary, PlayerFleet } from "../types";
import { useGameCommands } from "../hooks/useGameCommands";
import { Button } from "./Button";

type FleetComposerDesign = Pick<Design, "id" | "name"> | Pick<DesignSummary, "id" | "name">;

type Props = {
  fleets: PlayerFleet[];
  designs: FleetComposerDesign[];
  onClose: () => void;
};

export function FleetComposer({ fleets, designs, onClose }: Props) {
  const { addCommand, nextTmpFleetId } = useGameCommands();
  const rows = useMemo(() => {
    const totals = new Map<string, number>();
    for (const fleet of fleets) {
      for (const ship of fleet.composition ?? []) {
        totals.set(ship.designId, (totals.get(ship.designId) ?? 0) + ship.count);
      }
    }
    return Array.from(totals.entries()).map(([designId, total]) => ({
      designId,
      name: designs.find((d) => d.id === designId)?.name ?? designId,
      total,
    }));
  }, [designs, fleets]);

  const [columns, setColumns] = useState(() =>
    fleets.map((fleet) => ({
      fleetId: fleet.id,
      name: fleet.name ?? fleet.id,
      ships: Object.fromEntries((fleet.composition ?? []).map((c) => [c.designId, c.count])),
      isExisting: true,
    })),
  );

  const rowActual = (designId: string) =>
    columns.reduce((sum, column) => sum + (column.ships[designId] ?? 0), 0);

  const validRows = rows.every((row) => rowActual(row.designId) === row.total);
  const hasShips = columns.some((c) => Object.values(c.ships).some((v) => v > 0));
  const locationLabel =
    fleets[0] != null
      ? `${fleets[0].position.x.toLocaleString()}, ${fleets[0].position.y.toLocaleString()}`
      : "this position";

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  const apply = () => {
    const command = {
      type: "merge_split_fleets" as const,
      fleets: columns
        .filter((column) => column.isExisting || Object.values(column.ships).some((v) => v > 0))
        .map((column) => ({
          fleetId: column.fleetId,
          name: column.name,
          ships: rows
            .map((row) => ({ designId: row.designId, count: column.ships[row.designId] ?? 0 }))
            .filter((ship) => ship.count > 0),
        })),
    };
    addCommand(command);
    onClose();
  };

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Fleet Composer"
        className="flex max-h-[88vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="border-b border-[var(--color-panel-border)] px-5 py-4">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-foreground">Manage Fleets</h2>
              <p className="text-sm text-muted-foreground">
                Redistribute ships between all fleets at {locationLabel}.
              </p>
            </div>
            <Button variant="ghost" aria-label="Close Fleet Composer" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 border-b border-[var(--color-panel-border)] px-5 py-3">
          <Button
            onClick={() => {
              const leftId = columns[0]?.fleetId;
              if (!leftId) return;
              setColumns((prev) =>
                prev.map((col, colIndex) => ({
                  ...col,
                  ships: Object.fromEntries(
                    rows.map((row) => [row.designId, colIndex === 0 ? row.total : 0]),
                  ),
                })),
              );
            }}
            variant="secondary"
          >
            Merge All
          </Button>
          <Button
            onClick={() => {
              setColumns((prev) =>
                prev.map((col, colIndex) => ({
                  ...col,
                  ships: Object.fromEntries(
                    rows.map((row) => {
                      const base = Math.floor(row.total / prev.length);
                      const remainder = row.total % prev.length;
                      return [row.designId, base + (colIndex === 0 ? remainder : 0)];
                    }),
                  ),
                })),
              );
            }}
            variant="secondary"
          >
            Split Evenly
          </Button>
          <Button
            onClick={() =>
              setColumns((prev) => [
                ...prev,
                { fleetId: nextTmpFleetId(), name: "New Fleet", ships: {}, isExisting: false },
              ])
            }
            variant="secondary"
          >
            + New Fleet
          </Button>
        </div>

        <div className="overflow-auto px-5 py-4">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-panel-border)]">
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Design</th>
                {columns.map((column, colIndex) => (
                  <th key={column.fleetId} className="min-w-36 px-3 py-2 align-top">
                    <input
                      aria-label={`Fleet name ${colIndex + 1}`}
                      value={column.name}
                      className="w-full rounded-md border border-[var(--color-panel-border)] bg-transparent px-2 py-1 text-sm"
                      onChange={(e) =>
                        setColumns((prev) =>
                          prev.map((c, i) => (i === colIndex ? { ...c, name: e.target.value } : c)),
                        )
                      }
                    />
                    {Object.values(column.ships).reduce((a, b) => a + b, 0) === 0 && (
                      <div className="pt-1 text-xs text-muted-foreground">Will be dissolved</div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => {
                const rowValid = rowActual(row.designId) === row.total;
                return (
                  <tr key={row.designId} className="border-b border-[var(--color-panel-border)]/60">
                    <td className="px-3 py-3">
                      <div className="font-medium text-foreground">{row.name}</div>
                      <div className="text-xs text-muted-foreground">Total: {row.total}</div>
                    </td>
                    {columns.map((column, colIndex) => (
                      <td key={`${column.fleetId}-${row.designId}`} className="px-3 py-3">
                        <input
                          aria-label={`cell-${rowIndex}-${colIndex}`}
                          type="number"
                          className={`w-full rounded-md border bg-transparent px-2 py-1 ${
                            rowValid
                              ? "border-[var(--color-panel-border)]"
                              : "border-red-500 bg-red-950/20"
                          }`}
                          value={column.ships[row.designId] ?? 0}
                          onChange={(e) => {
                            const value = Math.max(0, Number(e.target.value || 0));
                            setColumns((prev) =>
                              prev.map((c, i) =>
                                i === colIndex
                                  ? {
                                      ...c,
                                      ships: {
                                        ...c.ships,
                                        [row.designId]: value,
                                      },
                                    }
                                  : c,
                              ),
                            );
                          }}
                        />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end gap-2 border-t border-[var(--color-panel-border)] px-5 py-4">
          <Button onClick={onClose} variant="secondary">
            Cancel
          </Button>
          <Button onClick={apply} disabled={!validRows || !hasShips}>
            Apply Changes
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
