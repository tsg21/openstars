import { ChevronDown, ChevronUp } from "lucide-react";

interface EventLogProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function EventLog({ collapsed, onToggle }: EventLogProps) {
  return (
    <footer
      className={`border-t border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] transition-[height] duration-200 ${
        collapsed ? "h-8" : "h-40"
      }`}
    >
      {/* Header strip — always visible */}
      <button
        onClick={onToggle}
        className="flex h-8 w-full items-center gap-2 px-4 text-xs text-muted-foreground hover:text-foreground"
      >
        {collapsed ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        <span className="font-medium">Events</span>
      </button>

      {/* Event list — visible when expanded */}
      {!collapsed && (
        <div className="h-[calc(100%-2rem)] overflow-y-auto px-4 pb-2">
          <p className="text-xs text-muted-foreground">
            No events yet.
          </p>
        </div>
      )}
    </footer>
  );
}
