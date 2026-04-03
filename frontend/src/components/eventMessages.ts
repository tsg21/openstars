import type { GameEvent } from "../types";

type EventTemplate = {
  message: string;
};

const EVENT_TEMPLATES: Record<string, EventTemplate> = {
  "movement.fleet_arrived": {
    message: "{0} arrived at {1}",
  },
  "scanner.planet_scanned": {
    message: "Scanned {0}",
  },
  "scanner.fleet_detected": {
    message: "Detected {0}'s fleet{1}",
  },
  "mining.complete": {
    message: "{0}: mined Fe {1}, Bo {2}, Ge {3}",
  },
  "production.completed": {
    message: "Completed {0} {1}(s) at {2}",
  },
  "population.colonists_died": {
    message: "{0} colonists died at {2} ({1})",
  },
  "population.planet_abandoned": {
    message: "{0} has been abandoned",
  },
  "colonisation.colonised": {
    message: "{0} colonised {1} with {2} colonists",
  },
  "colonisation.failed": {
    message: "{0} could not colonise {1} ({2})",
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
