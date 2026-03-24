import { PanelRightClose, PanelRightOpen } from "lucide-react";

interface DetailPanelProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function DetailPanel({ collapsed, onToggle }: DetailPanelProps) {
  return (
    <div className="relative">
      {/* Toggle button — outside the aside so it's never clipped */}
      <button
        onClick={onToggle}
        className="absolute -left-7 top-2 z-10 rounded-l bg-[var(--color-panel-bg)] border border-r-0 border-[var(--color-panel-border)] p-1 text-muted-foreground hover:text-foreground"
        aria-label={collapsed ? "Open detail panel" : "Close detail panel"}
      >
        {collapsed ? (
          <PanelRightOpen className="h-4 w-4" />
        ) : (
          <PanelRightClose className="h-4 w-4" />
        )}
      </button>

      <aside
        className={`h-full border-l border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] transition-[width] duration-200 overflow-hidden ${
          collapsed ? "w-0 border-l-0" : "w-[350px]"
        }`}
      >
        {!collapsed && (
          <div className="flex h-full flex-col p-4">
            <h2 className="text-sm font-semibold text-muted-foreground">
              Nothing selected
            </h2>
            <p className="mt-2 text-xs text-muted-foreground">
              Click a planet or fleet on the map to see details.
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}
