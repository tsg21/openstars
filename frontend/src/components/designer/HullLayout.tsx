import type { HullDefinition, HullSlotDefinition } from "../../types";

type HullLayoutProps = {
  hull: HullDefinition;
  renderSlot?: (slot: HullSlotDefinition) => React.ReactNode;
  renderCargo?: (hull: HullDefinition) => React.ReactNode;
  renderDock?: (hull: HullDefinition) => React.ReactNode;
};

const label = (slot: HullSlotDefinition) => slot.slotCategories.join("/").replaceAll("_", " ");

export function HullLayout({ hull, renderSlot, renderCargo, renderDock }: HullLayoutProps) {
  const grid = hull.layoutGrid ?? { w: 8, h: 8 };
  return (
    <div className="grid gap-1 rounded border p-2" style={{ gridTemplateColumns: `repeat(${grid.w}, var(--designer-cell-size))`, gridTemplateRows: `repeat(${grid.h}, var(--designer-cell-size))` }}>
      {hull.cargoLayout ? <div style={{ gridColumn: `${hull.cargoLayout.x + 1} / span ${hull.cargoLayout.w}`, gridRow: `${hull.cargoLayout.y + 1} / span ${hull.cargoLayout.h}` }} className="z-0 rounded border border-emerald-500/50 bg-emerald-500/10 text-xs flex items-center justify-center">{renderCargo?.(hull) ?? `Cargo ${hull.cargoCapacity}kt`}</div> : null}
      {hull.dockLayout ? <div style={{ gridColumn: `${hull.dockLayout.x + 1} / span ${hull.dockLayout.w}`, gridRow: `${hull.dockLayout.y + 1} / span ${hull.dockLayout.h}` }} className="z-0 rounded border border-cyan-500/50 bg-cyan-500/10 text-xs flex items-center justify-center">{renderDock?.(hull) ?? `Dock ${hull.dockCapacity}kt`}</div> : null}
      {hull.slots.map((slot) => {
        const pos = slot.position ?? { x: 0, y: 0 };
        const size = slot.size ?? { w: 1, h: 1 };
        return <div key={slot.slotNumber} data-grid-pos={`${pos.x},${pos.y},${size.w},${size.h}`} style={{ gridColumn: `${pos.x + 1} / span ${size.w}`, gridRow: `${pos.y + 1} / span ${size.h}` }} className="z-10 rounded border border-slate-500/40 bg-slate-800/30 p-1 text-xs">{renderSlot?.(slot) ?? <div className="flex h-full flex-col justify-between"><span>{label(slot)}</span><span>0/{slot.capacity}</span></div>}</div>;
      })}
    </div>
  );
}
