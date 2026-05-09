import { DndContext } from "@dnd-kit/core";
import { HullLayout } from "./HullLayout";
import { ComponentPalette } from "./ComponentPalette";
import type { DesignerComponentEntry, HullDefinition } from "../../types";

export type FitState = Map<number, { componentId: string; componentCount: number }>;

export function DragAndDropFitter({ hull, components, value, onChange }: { hull: HullDefinition; components: DesignerComponentEntry[]; value: FitState; onChange: (v: FitState) => void }) {
  return <DndContext><div className="grid grid-cols-1 gap-3 lg:grid-cols-2"><HullLayout hull={hull} renderSlot={(slot) => {
    const item = value.get(slot.slotNumber);
    const name = item ? components.find((c) => c.id === item.componentId)?.name ?? item.componentId : "Empty";
    return <div><div className="font-medium">Slot {slot.slotNumber}</div><div>{name}</div><div>{item?.componentCount ?? 0}/{slot.capacity}</div><button type="button" onClick={() => {
      const component = components.find((c) => slot.slotCategories.includes(c.componentType));
      if (!component) return;
      const current = value.get(slot.slotNumber);
      const next = new Map(value);
      if (!current) next.set(slot.slotNumber, { componentId: component.id, componentCount: 1 });
      else next.set(slot.slotNumber, { componentId: current.componentId, componentCount: Math.min(slot.capacity, current.componentCount + 1) });
      onChange(next);
    }}>+</button></div>;
  }} /><ComponentPalette components={components} /></div></DndContext>;
}
