import { useMemo, useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Minus, Plus, X, ChevronUp, ChevronDown } from "lucide-react";
import type { PlayerPlanet, PlayerProductionQueueItem, ProductionItemType, StarbaseType } from "../../types";
import type { DesignSummary } from "../../types/designer";
import { useGameCommands } from "../../hooks/useGameCommands";
import { buildPlanetScopeCommands } from "../../lib/productionQueueCommands";
import { createDraftProductionQueueItem, describeQueueItem } from "../../lib/productionSummary";
import { Button } from "../ui/Button";
import { MutedText } from "../ui/MutedText";
import { SectionLabel } from "../ui/SectionLabel";
import { PlanetList } from "./PlanetList";
import { BuildPalette } from "./BuildPalette";
import {
  nameColumn,
  populationColumn,
  resourcesColumn,
  minesColumn,
  factoriesColumn,
  queueHeadColumn,
  queueLengthColumn,
} from "./planetListColumns";
import type { PlanetListFilter } from "./PlanetList";

// ---------------------------------------------------------------------------
// Sortable queue row
// ---------------------------------------------------------------------------

interface QueueRowProps {
  item: PlayerProductionQueueItem;
  shipDesigns: DesignSummary[];
  onIncrease: () => void;
  onDecrease: () => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  isFirst: boolean;
  isLast: boolean;
}

function SortableQueueRow({
  item,
  shipDesigns,
  onIncrease,
  onDecrease,
  onRemove,
  onMoveUp,
  onMoveDown,
  isFirst,
  isLast,
}: QueueRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const label = describeQueueItem(item, shipDesigns);
  const isSingle = item.itemType === "planetary_scanner";

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-1.5 rounded-md border border-[var(--color-panel-border)] bg-black/10 px-2 py-1.5 text-sm"
    >
      {/* drag handle */}
      <button
        type="button"
        className="cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing"
        aria-label={`Drag to reorder ${label}`}
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-3.5 w-3.5" />
      </button>

      {/* label + progress */}
      <div className="min-w-0">
        <div className="truncate font-medium text-foreground">{label}</div>
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <span>{item.quantity}×</span>
          {item.progress.resourcesSpent > 0 && (
            <span>res {item.progress.resourcesSpent}/{/* cost not known client-side */}…</span>
          )}
        </div>
      </div>

      {/* controls */}
      <div className="flex items-center gap-0.5">
        <Button
          size="icon"
          variant="ghost"
          aria-label={`Move ${label} up`}
          disabled={isFirst}
          onClick={onMoveUp}
        >
          <ChevronUp className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          aria-label={`Move ${label} down`}
          disabled={isLast}
          onClick={onMoveDown}
        >
          <ChevronDown className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          aria-label={`Increase ${label} quantity`}
          disabled={isSingle}
          onClick={onIncrease}
        >
          <Plus className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          aria-label={`Decrease ${label} quantity`}
          onClick={onDecrease}
        >
          <Minus className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant="dangerGhost"
          aria-label={`Remove ${label}`}
          onClick={onRemove}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Starbase label helper (used in summary)
// ---------------------------------------------------------------------------

function starbaseLabel(planet: PlayerPlanet): string {
  if (!planet.starbase) return "None";
  const sb = planet.starbase as { type?: string; canBuildShips?: boolean };
  if (sb.canBuildShips) return "Dock (+ships)";
  return "Dock";
}

// ---------------------------------------------------------------------------
// Centre pane
// ---------------------------------------------------------------------------

interface CentrePaneProps {
  planet: PlayerPlanet;
  queue: PlayerProductionQueueItem[];
  baseQueue: PlayerProductionQueueItem[];
  baseContributeOnly: boolean | null | undefined;
  shipDesigns: DesignSummary[];
  onShowOnMap: () => void;
}

function CentrePane({
  planet,
  queue,
  baseQueue,
  baseContributeOnly,
  shipDesigns,
  onShowOnMap,
}: CentrePaneProps) {
  const { replaceCommands } = useGameCommands();

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const commit = (nextQueue: PlayerProductionQueueItem[]) => {
    replaceCommands(
      { kind: "planet", id: planet.id },
      buildPlanetScopeCommands(
        planet.id,
        baseQueue,
        nextQueue,
        baseContributeOnly,
        planet.contributeOnlyLeftoverToResearch,
      ),
    );
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIdx = queue.findIndex((i) => i.id === active.id);
    const newIdx = queue.findIndex((i) => i.id === over.id);
    if (oldIdx === -1 || newIdx === -1) return;
    commit(arrayMove(queue, oldIdx, newIdx));
  };

  const handleMove = (idx: number, delta: -1 | 1) => {
    const targetIdx = idx + delta;
    if (targetIdx < 0 || targetIdx >= queue.length) return;
    commit(arrayMove(queue, idx, targetIdx));
  };

  const handleAdjust = (idx: number, delta: -1 | 1) => {
    const item = queue[idx];
    const qty = item.quantity + delta;
    if (qty <= 0) {
      commit(queue.filter((_, i) => i !== idx));
    } else {
      commit(queue.map((i, n) => (n === idx ? { ...i, quantity: qty } : i)));
    }
  };

  const handleRemove = (idx: number) => {
    commit(queue.filter((_, i) => i !== idx));
  };

  const handleClearQueue = () => {
    commit([]);
  };

  const minerals = planet.minerals;
  const queueStatus =
    queue.length === 0
      ? "Idle"
      : `Building (${queue[0].quantity} remaining)`;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* header */}
      <div className="flex items-center justify-between border-b border-[var(--color-panel-border)] px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">{planet.name}</span>
          <span className="rounded border border-[var(--color-panel-border)] px-1.5 py-0.5 text-[10px] uppercase tracking-widest text-muted-foreground">
            detailed
          </span>
        </div>
        <button
          type="button"
          onClick={onShowOnMap}
          className="text-xs text-[var(--color-player-self)] hover:underline"
        >
          Show on map →
        </button>
      </div>

      {/* summary */}
      <div className="border-b border-[var(--color-panel-border)] px-3 py-2 text-xs space-y-0.5">
        <div>
          <MutedText>Res/turn:</MutedText>{" "}
          <span className="text-foreground">
            {planet.resources ?? "—"}
            {planet.contributeOnlyLeftoverToResearch ? " (leftover only)" : ""}
          </span>
        </div>
        <div>
          <MutedText>Mines / Factories:</MutedText>{" "}
          <span className="text-foreground">
            {planet.mines ?? "—"} / {planet.factories ?? "—"}
          </span>
        </div>
        <div>
          <MutedText>Starbase:</MutedText>{" "}
          <span className="text-foreground">{starbaseLabel(planet)}</span>
        </div>
        {minerals && (
          <div>
            <MutedText>Minerals:</MutedText>{" "}
            <span className="text-foreground">
              {minerals.ironium} / {minerals.boranium} / {minerals.germanium}
            </span>
          </div>
        )}
        <div>
          <MutedText>Status:</MutedText>{" "}
          <span className="text-foreground">{queueStatus}</span>
        </div>
      </div>

      {/* queue editor */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        <div className="flex items-center justify-between">
          <SectionLabel>Production Queue</SectionLabel>
          <Button
            size="icon"
            variant="dangerGhost"
            aria-label="Clear queue"
            disabled={queue.length === 0}
            onClick={handleClearQueue}
          >
            <X className="h-3 w-3" />
          </Button>
        </div>

        {queue.length === 0 ? (
          <div className="rounded-md border border-dashed border-[var(--color-panel-border)] px-3 py-4 text-center text-xs text-muted-foreground">
            Queue empty. Add items from the palette →
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext items={queue.map((i) => i.id)} strategy={verticalListSortingStrategy}>
              <div className="space-y-1.5">
                {queue.map((item, idx) => (
                  <SortableQueueRow
                    key={item.id}
                    item={item}
                    shipDesigns={shipDesigns}
                    isFirst={idx === 0}
                    isLast={idx === queue.length - 1}
                    onMoveUp={() => handleMove(idx, -1)}
                    onMoveDown={() => handleMove(idx, 1)}
                    onIncrease={() => handleAdjust(idx, 1)}
                    onDecrease={() => handleAdjust(idx, -1)}
                    onRemove={() => handleRemove(idx)}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProductionWorkspace
// ---------------------------------------------------------------------------

export interface ProductionWorkspaceProps {
  ownedPlanets: PlayerPlanet[];
  currentPlayer: string;
  shipDesigns: DesignSummary[];
  initialPlanetId: string | null;
  onShowOnMap: (planetId: string) => void;
}

const INITIAL_FILTER: PlanetListFilter = {
  search: "",
  toggles: [
    { id: "empty_queue", label: "Empty queue", active: false },
    { id: "has_starbase", label: "Has starbase", active: false },
    { id: "can_build_ships", label: "Can build ships", active: false },
  ],
  onChange: () => undefined,
};

export function ProductionWorkspace({
  ownedPlanets,
  shipDesigns,
  initialPlanetId,
  onShowOnMap,
}: ProductionWorkspaceProps) {
  const { basePlayerState, replaceCommands } = useGameCommands();

  const sortedOwnedPlanets = useMemo(
    () => [...ownedPlanets].sort((a, b) => a.name.localeCompare(b.name)),
    [ownedPlanets],
  );

  const [selectedPlanetId, setSelectedPlanetId] = useState<string | null>(
    () => initialPlanetId ?? sortedOwnedPlanets[0]?.id ?? null,
  );

  const [filter, setFilter] = useState<PlanetListFilter>({
    ...INITIAL_FILTER,
    onChange: (next) => setFilter((prev) => ({ ...next, onChange: prev.onChange })),
  });

  // Apply toggle predicates upstream
  const filteredPlanets = useMemo(() => {
    const emptyQueue = filter.toggles.find((t) => t.id === "empty_queue")?.active ?? false;
    const hasStarbase = filter.toggles.find((t) => t.id === "has_starbase")?.active ?? false;
    const canBuildShips = filter.toggles.find((t) => t.id === "can_build_ships")?.active ?? false;
    return sortedOwnedPlanets.filter((p) => {
      if (emptyQueue && (p.productionQueue?.length ?? 0) > 0) return false;
      if (hasStarbase && !p.starbase) return false;
      if (canBuildShips) {
        const sb = p.starbase as { canBuildShips?: boolean } | null | undefined;
        if (!sb?.canBuildShips) return false;
      }
      return true;
    });
  }, [sortedOwnedPlanets, filter.toggles]);

  const selectedPlanet = useMemo(
    () => ownedPlanets.find((p) => p.id === selectedPlanetId) ?? null,
    [ownedPlanets, selectedPlanetId],
  );

  const baseQueue = useMemo(
    () =>
      basePlayerState?.planets.find((p) => p.id === selectedPlanetId)?.productionQueue ?? [],
    [basePlayerState, selectedPlanetId],
  );

  const baseContributeOnly = useMemo(
    () =>
      basePlayerState?.planets.find((p) => p.id === selectedPlanetId)
        ?.contributeOnlyLeftoverToResearch ?? null,
    [basePlayerState, selectedPlanetId],
  );

  const queue = selectedPlanet?.productionQueue ?? [];

  const columns = useMemo(
    () => [
      nameColumn,
      populationColumn,
      resourcesColumn,
      minesColumn,
      factoriesColumn,
      queueHeadColumn(shipDesigns),
      queueLengthColumn,
    ],
    [shipDesigns],
  );

  const handleAddToQueue = (
    itemType: ProductionItemType,
    designId?: string,
    targetType?: StarbaseType,
    quantity = 1,
  ) => {
    if (!selectedPlanet) return;
    const newItems = Array.from({ length: quantity }, () =>
      createDraftProductionQueueItem(itemType, targetType ?? null, designId ?? null),
    );
    // Collapse multiple identical new items into one with summed quantity
    const merged = newItems[0] ? { ...newItems[0], quantity } : null;
    if (!merged) return;
    const nextQueue = [...queue, merged];
    replaceCommands(
      { kind: "planet", id: selectedPlanet.id },
      buildPlanetScopeCommands(
        selectedPlanet.id,
        baseQueue,
        nextQueue,
        baseContributeOnly,
        selectedPlanet.contributeOnlyLeftoverToResearch,
      ),
    );
  };

  const emptyMessage = (
    <div className="text-xs text-muted-foreground">Colonise a planet to start producing.</div>
  );

  return (
    <div
      className="flex h-full overflow-hidden"
      style={{ display: "grid", gridTemplateColumns: "22% 1fr 30%" }}
    >
      {/* Left: planet list */}
      <div className="overflow-hidden border-r border-[var(--color-panel-border)]" data-testid="planet-list-pane">
        {ownedPlanets.length === 0 ? (
          <div className="flex h-full items-center justify-center p-4">{emptyMessage}</div>
        ) : (
          <PlanetList
            planets={filteredPlanets}
            selectedPlanetId={selectedPlanetId}
            onSelectPlanet={setSelectedPlanetId}
            columns={columns}
            filter={filter}
          />
        )}
      </div>

      {/* Centre: planet detail + queue */}
      <div className="overflow-hidden border-r border-[var(--color-panel-border)]" data-testid="centre-pane">
        {selectedPlanet == null ? (
          <div className="flex h-full items-center justify-center p-4">{emptyMessage}</div>
        ) : (
          <CentrePane
            planet={selectedPlanet}
            queue={queue}
            baseQueue={baseQueue}
            baseContributeOnly={baseContributeOnly}
            shipDesigns={shipDesigns}
            onShowOnMap={() => onShowOnMap(selectedPlanet.id)}
          />
        )}
      </div>

      {/* Right: build palette */}
      <div className="overflow-hidden" data-testid="palette-pane">
        {selectedPlanet == null ? (
          <div className="flex h-full items-center justify-center p-4">{emptyMessage}</div>
        ) : (
          <BuildPalette
            planet={selectedPlanet}
            queue={queue}
            shipDesigns={shipDesigns}
            onAdd={handleAddToQueue}
          />
        )}
      </div>
    </div>
  );
}
