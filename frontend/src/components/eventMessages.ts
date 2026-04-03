import type { GameEvent } from "../types";

type EventTemplate = {
  message: string;
  toneClass: string;
};

const EVENT_TEMPLATES: Record<string, EventTemplate> = {
  "movement.fleet_arrived": {
    message: "{0} arrived at {1}",
    toneClass: "text-[var(--color-status-success)] border-[var(--color-status-success)]/40",
  },
  "scanner.planet_scanned": {
    message: "Scanned {0}",
    toneClass: "text-[var(--color-status-info)] border-[var(--color-status-info)]/40",
  },
  "scanner.fleet_detected": {
    message: "Detected {0}'s fleet{1}",
    toneClass: "text-[var(--color-status-warning)] border-[var(--color-status-warning)]/40",
  },
  "mining.complete": {
    message: "{0}: mined Fe {1}, Bo {2}, Ge {3}",
    toneClass: "text-[var(--color-status-info)] border-[var(--color-status-info)]/40",
  },
  "production.completed": {
    message: "Completed {0} {1}(s) at {2}",
    toneClass: "text-[var(--color-player-self)] border-[var(--color-player-self)]/40",
  },
  "population.colonists_died": {
    message: "{0} colonists died at {2} ({1})",
    toneClass: "text-[var(--color-status-warning)] border-[var(--color-status-warning)]/40",
  },
  "population.planet_abandoned": {
    message: "{0} has been abandoned",
    toneClass: "text-[var(--color-status-warning)] border-[var(--color-status-warning)]/40",
  },
};

export function formatEventMessage(event: GameEvent): string {
  const template = EVENT_TEMPLATES[event.code];
  if (!template) {
    return `Event: ${event.code}`;
  }

  return template.message.replace(/\{(\d+)}/g, (_match, indexText) => {
    const index = Number(indexText);
    const value = event.values[index];
    return value === undefined ? `{${index}}` : String(value);
  });
}

export function getEventToneClass(code: string): string {
  return (
    EVENT_TEMPLATES[code]?.toneClass
    ?? "text-muted-foreground border-[var(--color-panel-border)]"
  );
}
