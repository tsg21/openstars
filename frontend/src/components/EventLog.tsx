import { ChevronDown, ChevronUp, Navigation, Eye, AlertTriangle } from "lucide-react";
import type { GameEvent, Galaxy } from "../types";

interface EventLogProps {
  collapsed: boolean;
  onToggle: () => void;
  events: GameEvent[];
  galaxy: Galaxy;
  onEventClick: (x: number, y: number) => void;
}

// Helper to get event icon
function getEventIcon(eventType: string) {
  switch (eventType) {
    case "fleet_arrived":
      return Navigation;
    case "planet_scanned":
      return Eye;
    case "fleet_detected":
      return AlertTriangle;
    case "production_completed":
      return AlertTriangle;
    default:
      return AlertTriangle;
  }
}

function getEventToneClass(eventType: string): string {
  switch (eventType) {
    case "fleet_arrived":
      return "text-[var(--color-status-success)] border-[var(--color-status-success)]/40";
    case "planet_scanned":
      return "text-[var(--color-status-info)] border-[var(--color-status-info)]/40";
    case "fleet_detected":
      return "text-[var(--color-status-warning)] border-[var(--color-status-warning)]/40";
    case "production_completed":
      return "text-[var(--color-player-self)] border-[var(--color-player-self)]/40";
    default:
      return "text-muted-foreground border-[var(--color-panel-border)]";
  }
}

// Helper to get event description
function getEventDescription(event: GameEvent): string {
  switch (event.type) {
    case "fleet_arrived":
      return `${event.fleetName} arrived at ${event.planetName}`;
    case "planet_scanned":
      return `Scanned ${event.planetName}${event.owner ? ` (owned by ${event.owner})` : " (uncolonised)"}`;
    case "fleet_detected":
      return `Detected ${event.owner}'s fleet${event.planetName ? ` at ${event.planetName}` : " in deep space"}`;
    case "production_completed":
      return `Completed ${event.quantity} ${event.itemType}${event.quantity === 1 ? "" : "s"} at ${event.planetName ?? event.planetId}`;
    case "colonists_died":
      return `${event.deaths.toLocaleString()} colonists died at ${event.planetName ?? event.planetId} (${event.cause.replace("_", " ")})`;
    case "planet_abandoned":
      return `${event.planetName ?? event.planetId} has been abandoned`;
  }
}

// Helper to get event position
function getEventPosition(event: GameEvent, galaxy: Galaxy): { x: number; y: number } | null {
  switch (event.type) {
    case "fleet_arrived":
    case "planet_scanned": {
      const planet = galaxy.planets.find((p) => p.id === event.planetId);
      return planet ? { x: planet.x, y: planet.y } : null;
    }
    case "fleet_detected":
      return event.position;
    case "production_completed":
    case "colonists_died":
    case "planet_abandoned": {
      const planet = galaxy.planets.find((p) => p.id === event.planetId);
      return planet ? { x: planet.x, y: planet.y } : null;
    }
  }
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
              {getEventDescription(events[events.length - 1])}
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
                const Icon = getEventIcon(event.type);
                const toneClass = getEventToneClass(event.type);
                const description = getEventDescription(event);
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
