import { useDraggable } from "@dnd-kit/core";
import { useMemo, useState } from "react";
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
  readOnly?: boolean;
};

export function ComponentPalette({
  components,
  slotCategoryFilter,
  selectedComponentId,
  onSelectComponent,
  readOnly = false,
}: ComponentPaletteProps) {
  const groups = useMemo(
    () =>
      ORDER.map((type) => ({
        type,
        label: formatComponentType(type),
        components: components.filter((component) => component.componentType === type),
      })).filter((group) => group.components.length > 0),
    [components],
  );
  const [activeType, setActiveType] = useState<ComponentType | null>(() => groups[0]?.type ?? null);
  const selectedType = groups.some((group) => group.type === activeType)
    ? activeType
    : (groups[0]?.type ?? null);
  const activeGroup = groups.find((group) => group.type === selectedType);

  if (!activeGroup) {
    return (
      <section
        className="rounded-md border border-[var(--color-panel-border)] p-3 text-sm text-muted-foreground"
        aria-label="Component navigation"
      >
        No components available.
      </section>
    );
  }

  return (
    <section
      className="grid h-full min-h-80 grid-cols-[7.5rem_minmax(0,1fr)] rounded-md border border-[var(--color-panel-border)]"
      aria-label="Component navigation"
    >
      <div
        role="tablist"
        aria-orientation="vertical"
        aria-label="Component types"
        className="border-r border-[var(--color-panel-border)] bg-black/20 p-1"
      >
        {groups.map((group) => (
          <button
            key={group.type}
            type="button"
            role="tab"
            aria-selected={activeGroup.type === group.type}
            aria-controls={`component-panel-${group.type}`}
            id={`component-tab-${group.type}`}
            className={[
              "flex w-full items-center justify-between gap-2 rounded px-2 py-2 text-left text-xs transition-colors",
              activeGroup.type === group.type
                ? "bg-blue-500/15 text-foreground"
                : "text-muted-foreground hover:bg-white/[0.04] hover:text-foreground",
            ].join(" ")}
            onClick={() => setActiveType(group.type)}
          >
            <span className="truncate">{group.label}</span>
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id={`component-panel-${activeGroup.type}`}
        aria-labelledby={`component-tab-${activeGroup.type}`}
        className="min-w-0 space-y-1 p-2"
      >
        <h4 className="sr-only">{activeGroup.label} components</h4>
        {activeGroup.components.map((component) => (
          <PaletteItem
            key={component.id}
            component={component}
            active={isCompatibleWithFilter(component, slotCategoryFilter)}
            selected={selectedComponentId === component.id}
            onSelectComponent={onSelectComponent}
            readOnly={readOnly}
          />
        ))}
      </div>
    </section>
  );
}

function PaletteItem({
  component,
  active,
  selected,
  onSelectComponent,
  readOnly,
}: {
  component: DesignerComponentEntry;
  active: boolean;
  selected: boolean;
  onSelectComponent?: (componentId: string) => void;
  readOnly: boolean;
}) {
  const imageUrl = getComponentImageUrl(component.id);
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `palette-${component.id}`,
    data: { kind: "palette", componentId: component.id },
    disabled: readOnly,
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
      onClick={() => {
        if (!readOnly) onSelectComponent?.(component.id);
      }}
      className={[
        "relative flex w-full items-center gap-2 rounded-md border p-2 text-left text-xs transition-colors",
        active ? "border-[var(--color-panel-border)] bg-white/[0.03]" : "opacity-40",
        selected ? "border-[var(--color-status-info)] bg-blue-500/10" : "",
        isDragging ? "z-[1000] opacity-90 shadow-xl" : "",
        readOnly ? "cursor-default" : "",
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

function formatComponentType(type: ComponentType): string {
  return COMPONENT_TYPE_LABELS[type];
}

const COMPONENT_TYPE_LABELS: Record<ComponentType, string> = {
  engine: "Engines",
  scanner: "Scanners",
  weapon: "Weapons",
  torpedo: "Torpedoes",
  shield: "Shields",
  armour: "Armour",
  electrical: "Electrical",
  mechanical: "Mechanical",
  bomb: "Bombs",
  mine_layer: "Mine Layers",
  robot_miner: "Robot Miners",
  planetary: "Planetary",
};

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
