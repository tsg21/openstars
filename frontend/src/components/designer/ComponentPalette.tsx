import { useDraggable } from "@dnd-kit/core";
import type { ComponentType, DesignerComponentEntry, SlotCategory } from "../../types";
import { getComponentImageUrl } from "../../lib/componentImages";

const ORDER: ComponentType[] = [
  "engine",
  "scanner",
  "weapon",
  "torpedo",
  "shield",
  "armour",
  "electrical",
  "mechanical",
  "bomb",
  "mine_layer",
  "robot_miner",
  "planetary",
];

type ComponentPaletteProps = {
  components: DesignerComponentEntry[];
  slotCategoryFilter?: SlotCategory;
  selectedComponentId?: string | null;
  onSelectComponent?: (componentId: string) => void;
};

export function ComponentPalette({
  components,
  slotCategoryFilter,
  selectedComponentId,
  onSelectComponent,
}: ComponentPaletteProps) {
  return (
    <div className="space-y-3" aria-label="Component palette">
      {ORDER.map((type) => {
        const group = components.filter((component) => component.componentType === type);
        if (!group.length) return null;
        return (
          <section key={type} aria-label={`${type.replaceAll("_", " ")} components`}>
            <h4 className="text-sm font-semibold capitalize text-foreground">
              {type.replaceAll("_", " ")}
            </h4>
            <div className="mt-1 space-y-1">
              {group.map((component) => (
                <PaletteItem
                  key={component.id}
                  component={component}
                  active={isCompatibleWithFilter(component, slotCategoryFilter)}
                  selected={selectedComponentId === component.id}
                  onSelectComponent={onSelectComponent}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function PaletteItem({
  component,
  active,
  selected,
  onSelectComponent,
}: {
  component: DesignerComponentEntry;
  active: boolean;
  selected: boolean;
  onSelectComponent?: (componentId: string) => void;
}) {
  const imageUrl = getComponentImageUrl(component.id);
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `palette-${component.id}`,
    data: { kind: "palette", componentId: component.id },
  });
  return (
    <button
      ref={setNodeRef}
      type="button"
      data-component-id={component.id}
      {...attributes}
      {...listeners}
      aria-disabled={!active}
      aria-pressed={selected}
      onClick={() => onSelectComponent?.(component.id)}
      className={[
        "flex w-full items-center gap-2 rounded-md border p-2 text-left text-xs transition-colors",
        active ? "border-[var(--color-panel-border)] bg-white/[0.03]" : "opacity-40",
        selected ? "border-[var(--color-status-info)] bg-blue-500/10" : "",
        isDragging ? "opacity-70" : "",
      ].join(" ")}
      style={
        transform
          ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, touchAction: "none" }
          : { touchAction: "none" }
      }
    >
      {imageUrl ? (
        <img
          src={imageUrl}
          alt=""
          aria-hidden="true"
          className="h-16 w-16 flex-none object-contain [image-rendering:pixelated]"
          draggable={false}
        />
      ) : (
        <div className="flex h-16 w-16 flex-none items-center justify-center rounded border border-white/10 text-[0.65rem] text-muted-foreground">
          {component.componentType.slice(0, 3).toUpperCase()}
        </div>
      )}
      <div className="min-w-0">
        <div className="truncate font-medium text-foreground">{component.name}</div>
        <div className="text-muted-foreground">Mass {component.mass} kt</div>
        {primaryStat(component) ? (
          <div className="truncate text-muted-foreground">{primaryStat(component)}</div>
        ) : null}
      </div>
    </button>
  );
}

function isCompatibleWithFilter(
  component: DesignerComponentEntry,
  slotCategoryFilter?: SlotCategory,
) {
  if (!slotCategoryFilter) return true;
  if (slotCategoryFilter === "general_purpose") {
    return ["scanner", "weapon", "torpedo", "shield", "armour", "electrical", "mechanical"].includes(
      component.componentType,
    );
  }
  if (slotCategoryFilter === "weapon" && component.componentType === "torpedo") {
    return true;
  }
  return slotCategoryFilter === component.componentType;
}

function primaryStat(component: DesignerComponentEntry): string | null {
  if (component.engine) {
    return component.engine.isRamscoop
      ? "Ramscoop engine"
      : `Fuel ${component.engine.fuelUsage.join("/")}`;
  }
  if (component.scanner) {
    return `Scanner ${component.scanner.normal}/${component.scanner.penetrating}`;
  }
  if (component.weapon) {
    return `Range ${component.weapon.range}, damage ${component.weapon.damage}`;
  }
  if (component.torpedo) {
    return `Range ${component.torpedo.range}, damage ${component.torpedo.damage}`;
  }
  if (component.shield) {
    return `${component.shield.shieldPoints} shield points`;
  }
  if (component.armour) {
    return `${component.armour.armourPoints} armour points`;
  }
  if (component.electrical) {
    return `Ability ${component.electrical.ability}`;
  }
  if (component.mechanical) {
    return `Ability ${component.mechanical.ability}`;
  }
  if (component.planetary) {
    return `Ability ${component.planetary.ability}`;
  }
  return null;
}
