import { useMemo, useState } from "react";
import type { Design, PlayerFleet } from "../types";
import { useGameCommands } from "../hooks/useGameCommands";
import { Button } from "./Button";

type Props = {
  fleets: PlayerFleet[];
  designs: Design[];
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

  return (
    <div className="rounded border border-white/20 p-3 space-y-3" aria-label="Fleet Composer">
      <div className="flex gap-2">
        <Button
          onClick={() => {
            const leftId = columns[0]?.fleetId;
            if (!leftId) return;
            setColumns((prev) =>
              prev.map((col, colIndex) => ({
                ...col,
                ships: Object.fromEntries(
                  rows.map((row) => [
                    row.designId,
                    colIndex === 0 ? row.total : 0,
                  ]),
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

      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left">Design</th>
            {columns.map((column, colIndex) => (
              <th key={column.fleetId}>
                <input
                  aria-label={`Fleet name ${colIndex + 1}`}
                  value={column.name}
                  onChange={(e) =>
                    setColumns((prev) =>
                      prev.map((c, i) => (i === colIndex ? { ...c, name: e.target.value } : c)),
                    )
                  }
                />
                {Object.values(column.ships).reduce((a, b) => a + b, 0) === 0 && (
                  <div className="text-xs text-muted-foreground">Will be dissolved</div>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => {
            const rowValid = rowActual(row.designId) === row.total;
            return (
              <tr key={row.designId}>
                <td>{row.name}</td>
                {columns.map((column, colIndex) => (
                  <td key={`${column.fleetId}-${row.designId}`}>
                    <input
                      aria-label={`cell-${rowIndex}-${colIndex}`}
                      type="number"
                      className={!rowValid ? "border-red-500 border" : ""}
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
                      onKeyDown={(e) => {
                        if (e.key === "Escape") {
                          onClose();
                        }
                      }}
                    />
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="flex justify-end gap-2">
        <Button onClick={onClose} variant="secondary">Cancel</Button>
        <Button onClick={apply} disabled={!validRows || !hasShips}>Apply Changes</Button>
      </div>
    </div>
  );
}
