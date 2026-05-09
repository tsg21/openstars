import type { CSSProperties, ReactNode } from "react";
import type { GridRect, HullDefinition, HullSlotDefinition } from "../../types";

type HullLayoutProps = {
  hull: HullDefinition;
  renderSlot?: (slot: HullSlotDefinition) => ReactNode;
  renderCargo?: (hull: HullDefinition) => ReactNode;
  renderDock?: (hull: HullDefinition) => ReactNode;
};

const abbreviationByCategory = new Map<string, string>([
  ["engine", "Eng"],
  ["scanner", "Scn"],
  ["weapon", "Wpn"],
  ["torpedo", "Torp"],
  ["shield", "Shd"],
  ["armour", "Arm"],
  ["electrical", "Elec"],
  ["mechanical", "Mech"],
  ["bomb", "Bomb"],
  ["mine_layer", "Mine"],
  ["robot_miner", "Miner"],
  ["planetary", "Orb"],
  ["general_purpose", "GP"],
  ["orbital", "Orb"],
]);

function slotLabel(slot: HullSlotDefinition) {
  return slot.slotCategories
    .map((category) => abbreviationByCategory.get(category) ?? category)
    .join("/");
}

function placementStyle(rect: GridRect): CSSProperties {
  return {
    gridColumn: `${rect.x + 1} / span ${rect.w}`,
    gridRow: `${rect.y + 1} / span ${rect.h}`,
  };
}

export function HullLayout({ hull, renderSlot, renderCargo, renderDock }: HullLayoutProps) {
  const grid = hull.layoutGrid ?? inferGridSize(hull);
  return (
    <div
      className="inline-grid gap-1 rounded-md border border-[var(--color-panel-border)] bg-black/20 p-2"
      style={{
        gridTemplateColumns: `repeat(${grid.w}, var(--designer-cell-size))`,
        gridTemplateRows: `repeat(${grid.h}, var(--designer-cell-size))`,
      }}
    >
      {Array.from({ length: grid.w * grid.h }, (_, index) => (
        <div
          key={`empty-${index}`}
          aria-hidden="true"
          className="rounded-sm border border-dashed border-white/10"
          style={{
            gridColumn: (index % grid.w) + 1,
            gridRow: Math.floor(index / grid.w) + 1,
          }}
        />
      ))}
      {hull.cargoLayout ? (
        <div
          data-testid="hull-cargo-layout"
          style={placementStyle(hull.cargoLayout)}
          className="z-0 flex items-center justify-center rounded border border-emerald-500/50 bg-emerald-500/10 px-1 text-center text-xs text-emerald-100"
        >
          {renderCargo?.(hull) ?? `Cargo ${hull.cargoCapacity} kt`}
        </div>
      ) : null}
      {hull.dockLayout ? (
        <div
          data-testid="hull-dock-layout"
          style={placementStyle(hull.dockLayout)}
          className="z-0 flex items-center justify-center rounded border border-cyan-500/50 bg-cyan-500/10 px-1 text-center text-xs text-cyan-100"
        >
          {renderDock?.(hull) ?? `Dock ${hull.dockCapacity} kt`}
        </div>
      ) : null}
      {hull.slots.map((slot) => {
        const pos = slot.position ?? { x: 0, y: 0 };
        const size = slot.size ?? { w: 1, h: 1 };
        return (
          <div
            key={slot.slotNumber}
            data-testid={`hull-slot-${slot.slotNumber}`}
            data-grid-pos={`${pos.x},${pos.y},${size.w},${size.h}`}
            style={placementStyle({ ...pos, ...size })}
            className="z-10 rounded border border-slate-400/40 bg-slate-900/80 p-1 text-xs shadow-sm"
          >
            {renderSlot?.(slot) ?? (
              <div className="flex h-full flex-col justify-between">
                <span className="font-medium text-foreground">{slotLabel(slot)}</span>
                <span className="self-end rounded bg-black/40 px-1 text-[0.65rem] text-muted-foreground">
                  0/{slot.capacity}
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function inferGridSize(hull: HullDefinition) {
  let w = 1;
  let h = 1;
  for (const slot of hull.slots) {
    const position = slot.position ?? { x: 0, y: 0 };
    const size = slot.size ?? { w: 1, h: 1 };
    w = Math.max(w, position.x + size.w);
    h = Math.max(h, position.y + size.h);
  }
  if (hull.cargoLayout) {
    w = Math.max(w, hull.cargoLayout.x + hull.cargoLayout.w);
    h = Math.max(h, hull.cargoLayout.y + hull.cargoLayout.h);
  }
  if (hull.dockLayout) {
    w = Math.max(w, hull.dockLayout.x + hull.dockLayout.w);
    h = Math.max(h, hull.dockLayout.y + hull.dockLayout.h);
  }
  return { w, h };
}
