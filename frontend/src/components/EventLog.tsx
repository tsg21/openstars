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
    default:
      return AlertTriangle;
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
  }
}

export function EventLog({ collapsed, onToggle, events, galaxy, onEventClick }: EventLogProps) {
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
        {events.length > 0 && (
          <span className="ml-auto text-muted-foreground">
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
                    className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Icon className="h-3 w-3 shrink-0 text-muted-foreground" />
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
