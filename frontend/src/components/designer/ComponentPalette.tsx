import type { ComponentType, DesignerComponentEntry, SlotCategory } from "../../types";

const ORDER: ComponentType[] = ["engine", "scanner", "weapon", "torpedo", "shield", "armour", "electrical", "mechanical", "bomb", "mine_layer", "robot_miner", "planetary"];

export function ComponentPalette({ components, slotCategoryFilter }: { components: DesignerComponentEntry[]; slotCategoryFilter?: SlotCategory }) {
  return <div className="space-y-3">{ORDER.map((type) => {
    const group = components.filter((c) => c.componentType === type);
    if (!group.length) return null;
    return <section key={type}><h4 className="text-sm font-semibold capitalize">{type.replaceAll("_", " ")}</h4><div className="space-y-1">{group.map((c) => {
      const active = !slotCategoryFilter || slotCategoryFilter === c.componentType || slotCategoryFilter === "general_purpose";
      return <div key={c.id} data-component-id={c.id} aria-disabled={!active} className={`rounded border p-2 text-xs ${active ? "" : "opacity-40"}`}><div className="font-medium">{c.name}</div><div>Mass {c.mass}</div></div>;
    })}</div></section>;
  })}</div>;
}
