import { useState } from "react";
import type { ReactNode } from "react";
import type { PlayerPlanet } from "../../types";

export interface PlanetListColumn {
  id: string;
  header: string;
  align?: "left" | "right";
  width?: string;
  sortable?: boolean;
  sortValue?: (planet: PlayerPlanet) => number | string | null;
  render: (planet: PlayerPlanet) => ReactNode;
}

export interface PlanetListFilterToggle {
  id: string;
  label: string;
  active: boolean;
}

export interface PlanetListFilter {
  search: string;
  toggles: PlanetListFilterToggle[];
  onChange: (next: PlanetListFilter) => void;
}

export interface PlanetListProps {
  planets: PlayerPlanet[];
  selectedPlanetId: string | null;
  onSelectPlanet: (planetId: string) => void;
  columns: PlanetListColumn[];
  filter?: PlanetListFilter;
  emptyState?: ReactNode;
}

type SortDir = "asc" | "desc";

function sortPlanets(
  planets: PlayerPlanet[],
  col: PlanetListColumn | undefined,
  dir: SortDir,
): PlayerPlanet[] {
  if (!col?.sortValue) return planets;
  return [...planets].sort((a, b) => {
    const va = col.sortValue!(a);
    const vb = col.sortValue!(b);
    if (va === null && vb === null) return 0;
    if (va === null) return 1;
    if (vb === null) return -1;
    let cmp = 0;
    if (typeof va === "number" && typeof vb === "number") {
      cmp = va - vb;
    } else {
      cmp = String(va).localeCompare(String(vb));
    }
    return dir === "asc" ? cmp : -cmp;
  });
}

export function PlanetList({
  planets,
  selectedPlanetId,
  onSelectPlanet,
  columns,
  filter,
  emptyState,
}: PlanetListProps) {
  const [sortColId, setSortColId] = useState<string | null>(
    () => columns.find((c) => c.sortable)?.id ?? null,
  );
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [clickCount, setClickCount] = useState<Record<string, number>>({});

  const handleHeaderClick = (col: PlanetListColumn) => {
    if (!col.sortable) return;
    const prev = clickCount[col.id] ?? 0;
    const next = prev + 1;
    setClickCount((c) => ({ ...c, [col.id]: next }));
    if (next % 3 === 1) {
      setSortColId(col.id);
      setSortDir("asc");
    } else if (next % 3 === 2) {
      setSortColId(col.id);
      setSortDir("desc");
    } else {
      setSortColId(null);
    }
  };

  const searchStr = filter?.search.toLowerCase() ?? "";
  const filtered = searchStr
    ? planets.filter((p) => p.name.toLowerCase().includes(searchStr))
    : planets;

  const activeCol = columns.find((c) => c.id === sortColId);
  const sorted = activeCol ? sortPlanets(filtered, activeCol, sortDir) : filtered;

  const clearFilter = () => {
    if (!filter) return;
    filter.onChange({
      ...filter,
      search: "",
      toggles: filter.toggles.map((t) => ({ ...t, active: false })),
    });
  };

  if (planets.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-sm text-muted-foreground">
        {emptyState ?? "No planets to show."}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {filter && (
        <div className="flex flex-wrap items-center gap-2 border-b border-[var(--color-panel-border)] p-2 text-xs">
          <input
            aria-label="Search planets"
            type="text"
            value={filter.search}
            onChange={(e) =>
              filter.onChange({ ...filter, search: e.target.value })
            }
            placeholder="Search…"
            className="rounded border border-[var(--color-panel-border)] bg-black/30 px-2 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-[var(--color-player-self)]"
          />
          {filter.toggles.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() =>
                filter.onChange({
                  ...filter,
                  toggles: filter.toggles.map((tog) =>
                    tog.id === t.id ? { ...tog, active: !tog.active } : tog,
                  ),
                })
              }
              className={`rounded-full border px-2 py-0.5 text-xs transition-colors ${
                t.active
                  ? "border-[var(--color-player-self)] bg-[var(--color-player-self)]/20 text-foreground"
                  : "border-[var(--color-panel-border)] text-muted-foreground hover:border-foreground/40"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-auto">
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-4 text-sm text-muted-foreground">
            <span>No planets match the current filter.</span>
            <button
              type="button"
              onClick={clearFilter}
              className="text-xs underline hover:text-foreground"
            >
              Clear filter
            </button>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-[var(--color-panel-bg,#0a0a0a)]">
              <tr className="border-b border-[var(--color-panel-border)]">
                {columns.map((col) => {
                  const isActive = col.id === sortColId;
                  const arrow = isActive ? (sortDir === "asc" ? " ↑" : " ↓") : "";
                  return (
                    <th
                      key={col.id}
                      style={col.width ? { width: col.width } : undefined}
                      className={`px-2 py-1.5 text-left font-medium text-muted-foreground ${
                        col.sortable !== false ? "cursor-pointer select-none hover:text-foreground" : ""
                      } ${col.align === "right" ? "text-right" : "text-left"}`}
                      aria-sort={
                        isActive ? (sortDir === "asc" ? "ascending" : "descending") : "none"
                      }
                      onClick={() => handleHeaderClick(col)}
                    >
                      {col.header}
                      {arrow}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {sorted.map((planet) => {
                const isSelected = planet.id === selectedPlanetId;
                return (
                  <tr
                    key={planet.id}
                    aria-selected={isSelected}
                    onClick={() => onSelectPlanet(planet.id)}
                    className={`cursor-pointer border-b border-[var(--color-panel-border)] transition-colors hover:bg-white/5 ${
                      isSelected
                        ? "border-l-2 border-l-[var(--color-player-self)] bg-[var(--color-player-self)]/10"
                        : ""
                    }`}
                  >
                    {columns.map((col) => (
                      <td
                        key={col.id}
                        className={`px-2 py-1.5 ${col.align === "right" ? "text-right" : "text-left"}`}
                      >
                        {col.render(planet)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
