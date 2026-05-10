import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useMemo, useState, type ReactNode } from "react";
import type {
  DesignerComponentEntry,
  HullDefinition,
  HullSlotDefinition,
} from "../../types";
import {
  applyComponentToFitState,
  decrementSlot,
  type FitState,
} from "../../lib/designerFit";
import { getComponentImageUrl } from "../../lib/componentImages";
import { computeDerivedStats } from "../../lib/designerStats";
import { ComponentPalette } from "./ComponentPalette";
import { HullLayout } from "./HullLayout";
import { StatsPanel } from "./StatsPanel";

type DragAndDropFitterProps = {
  hull: HullDefinition;
  components: DesignerComponentEntry[];
  value: FitState;
  onChange: (value: FitState) => void;
  controls?: ReactNode;
  actions?: ReactNode;
};

export function DragAndDropFitter({
  hull,
  components,
  value,
  onChange,
  controls,
  actions,
}: DragAndDropFitterProps) {
  const sensors = useSensors(useSensor(PointerSensor), useSensor(KeyboardSensor));
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(null);
  const [rejectedSlotNumber, setRejectedSlotNumber] = useState<number | null>(null);
  const componentById = useMemo(
    () => new Map(components.map((component) => [component.id, component])),
    [components],
  );
  const stats = computeDerivedStats(hull, components, value);

  function commitFit(next: FitState, rejectedSlot?: number) {
    if (rejectedSlot !== undefined) {
      setRejectedSlotNumber(rejectedSlot);
      window.setTimeout(() => setRejectedSlotNumber(null), 250);
      return;
    }
    onChange(next);
  }

  function addComponentToSlot(slotNumber: number, componentId: string) {
    const result = applyComponentToFitState({
      hull,
      components,
      fitState: value,
      slotNumber,
      componentId,
      confirmReplace: (message) => window.confirm(message),
    });
    commitFit(result.fitState, result.rejected ? slotNumber : undefined);
  }

  function handleDragEnd(event: DragEndEvent) {
    const componentId = event.active.data.current?.componentId;
    const slotNumber = event.over?.data.current?.slotNumber;
    if (typeof componentId !== "string" || typeof slotNumber !== "number") return;
    addComponentToSlot(slotNumber, componentId);
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="grid min-h-0 min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
        <div className="min-w-0 space-y-4">
          {controls}
          <div className="min-w-0 overflow-x-auto pb-2">
            <HullLayout
              hull={hull}
              renderSlot={(slot) => {
                const fit = value.get(slot.slotNumber);
                return (
                  <DroppableSlot
                    slot={slot}
                    fit={fit}
                    component={fit ? componentById.get(fit.componentId) : undefined}
                    rejected={rejectedSlotNumber === slot.slotNumber}
                    onAddSelected={() => {
                      if (selectedComponentId) addComponentToSlot(slot.slotNumber, selectedComponentId);
                    }}
                    onIncrement={() => {
                      if (fit) addComponentToSlot(slot.slotNumber, fit.componentId);
                    }}
                    onDecrement={() => onChange(decrementSlot(value, slot.slotNumber))}
                  />
                );
              }}
            />
          </div>
          <StatsPanel stats={stats} />
          {actions}
        </div>
        <div className="min-h-0">
          <ComponentPalette
            components={components}
            selectedComponentId={selectedComponentId}
            onSelectComponent={setSelectedComponentId}
          />
        </div>
      </div>
    </DndContext>
  );
}

function DroppableSlot({
  slot,
  fit,
  component,
  rejected,
  onAddSelected,
  onIncrement,
  onDecrement,
}: {
  slot: HullSlotDefinition;
  fit?: { componentId: string; componentCount: number };
  component?: DesignerComponentEntry;
  rejected: boolean;
  onAddSelected: () => void;
  onIncrement: () => void;
  onDecrement: () => void;
}) {
  const componentImageUrl = fit ? getComponentImageUrl(fit.componentId) : null;
  const { isOver, setNodeRef } = useDroppable({
    id: `slot-${slot.slotNumber}`,
    data: { kind: "slot", slotNumber: slot.slotNumber, slotCategories: slot.slotCategories },
  });
  return (
    <div
      ref={setNodeRef}
      role="button"
      tabIndex={0}
      aria-label={
        component
          ? `${formatSlotCategories(slot)} fitting cell, fitted with ${component.name}`
          : `${formatSlotCategories(slot)} fitting cell`
      }
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onAddSelected();
        }
      }}
      className={[
        "flex h-full flex-col justify-between rounded p-1 outline-none",
        isOver ? "bg-blue-500/15" : "",
        rejected ? "animate-pulse bg-red-500/20" : "",
      ].join(" ")}
    >
      <div>
        <div className="text-[0.65rem] capitalize text-muted-foreground">
          {slot.slotCategories.join("/").replaceAll("_", " ")}
        </div>
      </div>
      <div className="flex min-h-16 items-center justify-center">
        {componentImageUrl ? (
          <img
            src={componentImageUrl}
            alt=""
            aria-hidden="true"
            className="h-16 w-16 object-contain [image-rendering:pixelated]"
            draggable={false}
          />
        ) : null}
      </div>
      <div className="flex items-center justify-between gap-1">
        <button
          type="button"
          aria-label={`Remove from slot ${slot.slotNumber}`}
          className="rounded border border-[var(--color-panel-border)] px-1 text-xs disabled:opacity-40"
          disabled={!fit}
          onClick={(event) => {
            event.stopPropagation();
            onDecrement();
          }}
        >
          -
        </button>
        <span className="rounded bg-black/40 px-1 text-[0.65rem] text-muted-foreground">
          {fit?.componentCount ?? 0}/{slot.capacity}
        </span>
        <button
          type="button"
          aria-label={`Add to slot ${slot.slotNumber}`}
          className="rounded border border-[var(--color-panel-border)] px-1 text-xs disabled:opacity-40"
          disabled={!fit || fit.componentCount >= slot.capacity}
          onClick={(event) => {
            event.stopPropagation();
            onIncrement();
          }}
        >
          +
        </button>
      </div>
    </div>
  );
}

function formatSlotCategories(slot: HullSlotDefinition) {
  return slot.slotCategories
    .map((category) =>
      category
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" "),
    )
    .join("/");
}
