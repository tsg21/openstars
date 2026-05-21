import type { PlayerPlanet, PlayerProductionQueueItem, ProductionItemType, StarbaseType } from "../../types";
import type { DesignSummary } from "../../types/designer";

interface PaletteRow {
  label: string;
  cost: string;
  available: boolean;
  unavailableReason?: string;
  itemType: ProductionItemType;
  targetType?: StarbaseType;
  designId?: string;
}

function buildRows(
  planet: PlayerPlanet,
  queue: PlayerProductionQueueItem[],
  shipDesigns: DesignSummary[],
): { infrastructure: PaletteRow[]; ships: PaletteRow[]; starbases: PaletteRow[] } {
  const hasScanner = planet.scanner?.installed === true;
  const hasQueuedScanner = queue.some((i) => i.itemType === "planetary_scanner");
  const hasQueuedStarbase = queue.some((i) => i.itemType === "starbase");
  const canBuildShips = planet.starbase != null && "canBuildShips" in planet.starbase
    ? (planet.starbase as { canBuildShips: boolean }).canBuildShips
    : false;
  const currentStarbaseType = planet.starbase && "type" in planet.starbase
    ? (planet.starbase as { type: StarbaseType }).type
    : null;

  const infrastructure: PaletteRow[] = [
    { label: "Mine", cost: "5r", available: true, itemType: "mine" },
    { label: "Factory", cost: "10r 4g", available: true, itemType: "factory" },
    {
      label: "Planetary Scanner",
      cost: "100r 10i 10b 70g",
      available: !hasScanner && !hasQueuedScanner,
      unavailableReason: hasScanner ? "Already installed" : hasQueuedScanner ? "Already queued" : undefined,
      itemType: "planetary_scanner",
    },
  ];

  const ships: PaletteRow[] = shipDesigns.map((d) => ({
    label: d.name,
    cost: formatDesignCost(d),
    available: canBuildShips,
    unavailableReason: !canBuildShips ? "Needs starbase" : undefined,
    itemType: "ship" as const,
    designId: d.id,
  }));

  const starbaseOptions: Array<{ label: string; targetType: StarbaseType; cost: string }> = [
    { label: "Orbital Fort", targetType: "orbital_fort", cost: "(see PRD 17)" },
    { label: "Space Station", targetType: "space_station", cost: "(see PRD 17)" },
  ];

  const starbases: PaletteRow[] = starbaseOptions.map((opt) => {
    const isDuplicate = hasQueuedStarbase;
    const isSameType = currentStarbaseType === opt.targetType;
    return {
      label: opt.label,
      cost: opt.cost,
      available: !isDuplicate && !isSameType,
      unavailableReason: isDuplicate ? "Already queued" : isSameType ? "Already this type" : undefined,
      itemType: "starbase" as const,
      targetType: opt.targetType,
    };
  });

  return { infrastructure, ships, starbases };
}

function formatDesignCost(d: DesignSummary): string {
  const parts: string[] = [`${d.cost.resources}r`];
  if (d.cost.minerals.ironium) parts.push(`${d.cost.minerals.ironium}i`);
  if (d.cost.minerals.boranium) parts.push(`${d.cost.minerals.boranium}b`);
  if (d.cost.minerals.germanium) parts.push(`${d.cost.minerals.germanium}g`);
  return parts.join(" ");
}

interface BuildPaletteProps {
  planet: PlayerPlanet;
  queue: PlayerProductionQueueItem[];
  shipDesigns: DesignSummary[];
  onAdd: (itemType: ProductionItemType, designId?: string, targetType?: StarbaseType, quantity?: number) => void;
}

function PaletteSection({ title, rows, onAdd }: {
  title: string;
  rows: PaletteRow[];
  onAdd: BuildPaletteProps["onAdd"];
}) {
  return (
    <div>
      <div className="px-2 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
        {title}
      </div>
      {rows.length === 0 && (
        <div className="px-2 py-1.5 text-xs italic text-muted-foreground">No designs</div>
      )}
      {rows.map((row) => (
        <button
          key={`${row.itemType}-${row.targetType ?? ""}-${row.designId ?? ""}`}
          type="button"
          disabled={!row.available}
          onClick={(e) => {
            if (!row.available) return;
            const isSingle = row.itemType === "planetary_scanner";
            const qty = !isSingle && e.shiftKey ? 5 : 1;
            onAdd(row.itemType, row.designId, row.targetType, qty);
          }}
          className={`w-full px-2 py-1.5 text-left transition-colors ${
            row.available
              ? "hover:bg-white/8 cursor-pointer"
              : "cursor-not-allowed opacity-45"
          }`}
        >
          <div className="text-sm text-foreground">{row.label}</div>
          <div className="flex gap-2 text-[11px] text-muted-foreground">
            <span>{row.cost}</span>
            {row.unavailableReason && <span className="italic">{row.unavailableReason}</span>}
          </div>
        </button>
      ))}
    </div>
  );
}

export function BuildPalette({ planet, queue, shipDesigns, onAdd }: BuildPaletteProps) {
  const { infrastructure, ships, starbases } = buildRows(planet, queue, shipDesigns);

  return (
    <div className="h-full overflow-y-auto space-y-2 py-2">
      <PaletteSection title="Infrastructure" rows={infrastructure} onAdd={onAdd} />
      <PaletteSection title="Ships" rows={ships} onAdd={onAdd} />
      <PaletteSection title="Starbases" rows={starbases} onAdd={onAdd} />
    </div>
  );
}
