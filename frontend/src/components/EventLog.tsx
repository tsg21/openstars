import { ChevronDown, ChevronUp, Navigation, Eye, AlertTriangle } from "lucide-react";
import type { GameEvent, Galaxy } from "../types";
import { formatEventMessage, getEventToneClass } from "./eventMessages";

interface EventLogProps {
  collapsed: boolean;
  onToggle: () => void;
  events: GameEvent[];
  galaxy: Galaxy;
  onEventClick: (x: number, y: number) => void;
}

// Helper to get event icon
function getEventIcon(eventCode: string) {
  switch (eventCode) {
    case "movement.fleet_arrived":
      return Navigation;
    case "scanner.planet_scanned":
      return Eye;
    case "scanner.fleet_detected":
      return AlertTriangle;
    default:
      return AlertTriangle;
  }
}

// Helper to get event position
function getEventPosition(event: GameEvent, galaxy: Galaxy): { x: number; y: number } | null {
  if (!event.sourceId) {
    return null;
  }

  const planet = galaxy.planets.find((p) => p.id === event.sourceId);
  return planet ? { x: planet.x, y: planet.y } : null;
}

export function EventLog({ collapsed, onToggle, events, galaxy, onEventClick }: EventLogProps) {
  const unreadCount = events.length > 0 ? Math.min(events.length, 9) : 0;

  return (
    <footer
      className={`panel-surface border-t border-[var(--color-panel-border)] transition-[height] duration-300 ${
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
        {unreadCount > 0 && (
          <span className="inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--color-status-info)]/20 px-1 text-[10px] text-[var(--color-status-info)]">
            {unreadCount}
          </span>
        )}
        {events.length > 0 && collapsed && (
          <>
            <span className="mx-1 text-muted-foreground">·</span>
            <span className="truncate text-foreground">
              {formatEventMessage(events[events.length - 1])}
            </span>
          </>
        )}
        {events.length > 0 && (
          <span className={`text-muted-foreground ${collapsed ? "shrink-0" : "ml-auto"}`}>
            {events.length}
          </span>
        )}
      </button>

      {/* Event list — visible when expanded */}
      {!collapsed && (
        <div className="h-[calc(100%-2rem)] overflow-y-auto px-4 pb-2">
          {events.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No events yet.
            </p>
          ) : (
            <div className="space-y-1">
              {events.map((event, index) => {
                const Icon = getEventIcon(event.code);
                const toneClass = getEventToneClass(event.code);
                const description = formatEventMessage(event);
                const position = getEventPosition(event, galaxy);

                return (
                  <button
                    key={index}
                    onClick={() => {
                      if (position) {
                        onEventClick(position.x, position.y);
                      }
                    }}
                    disabled={!position}
                    className="group flex w-full items-center gap-2 rounded border border-transparent px-2 py-1.5 text-left text-xs transition-all duration-200 hover:bg-muted/40 hover:border-[var(--color-panel-border)] hover:translate-x-0.5 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <span className={`rounded-sm border p-0.5 ${toneClass}`}>
                      <Icon className="h-3 w-3 shrink-0" />
                    </span>
                    <span className="flex-1 text-foreground">{description}</span>
                    <span className="shrink-0 text-muted-foreground">
                      Turn {event.turn}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </footer>
  );
}
