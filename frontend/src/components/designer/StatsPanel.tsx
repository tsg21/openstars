import type { DerivedDesignerStats } from "../../lib/designerStats";

export function StatsPanel({ stats }: { stats: DerivedDesignerStats }) {
  return (
    <div className="rounded-md border border-[var(--color-panel-border)] p-3 text-sm">
      <div className="font-semibold text-foreground">Derived stats</div>
      <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-muted-foreground">
        <dt>Mass</dt>
        <dd className="text-right text-foreground">{stats.mass} kt</dd>
        <dt>Fuel</dt>
        <dd className="text-right text-foreground">{stats.fuelCapacity} mg</dd>
        <dt>Cargo</dt>
        <dd className="text-right text-foreground">{stats.cargoCapacity} kt</dd>
        <dt>Armour</dt>
        <dd className="text-right text-foreground">{stats.armour}</dd>
        <dt>Scanner</dt>
        <dd className="text-right text-foreground">
          {stats.scanner ? `${stats.scanner.normal}/${stats.scanner.penetrating}` : "0/0"}
        </dd>
      </dl>
      <div className="mt-2 text-xs text-muted-foreground">
        Cost: {stats.cost.resources} resources,{" "}
        <span className="text-[var(--color-ironium-bright)]">{stats.cost.ironium} ironium</span>,{" "}
        <span className="text-[var(--color-boranium-bright)]">{stats.cost.boranium} boranium</span>,{" "}
        <span className="text-[var(--color-germanium-bright)]">
          {stats.cost.germanium} germanium
        </span>
      </div>
    </div>
  );
}
