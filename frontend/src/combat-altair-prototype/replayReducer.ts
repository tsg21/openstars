/**
 * Pure reducer: builds frame state by applying combat events sequentially.
 *
 * The initial token positions/hp come from the first events in the log
 * (we extract them from token_moved and damage_applied events).
 */

import type {
  CombatEvent,
  CombatLog,
  FrameState,
  TokenFrame,
  WeaponFiredEvent,
} from "./types";

export interface InitialToken {
  id: string;
  owner: string;
  x: number;
  y: number;
  hp: number;
}

/** Build all frames by replaying every event. Frame 0 is the initial state. */
export function buildFrames(
  log: CombatLog,
  initialTokens: InitialToken[],
): FrameState[] {
  const tokens: Map<string, TokenFrame> = new Map();
  for (const t of initialTokens) {
    tokens.set(t.id, { id: t.id, owner: t.owner, x: t.x, y: t.y, hp: t.hp, alive: true });
  }

  const snapshot = (): TokenFrame[] =>
    Array.from(tokens.values()).map((t) => ({ ...t }));

  const frames: FrameState[] = [
    {
      eventIndex: -1,
      roundIndex: 0,
      tickIndex: 0,
      tokens: snapshot(),
      lastShotEvents: [],
    },
  ];

  let roundIndex = 0;
  let tickIndex = 0;
  let lastShotEvents: WeaponFiredEvent[] = [];

  for (let i = 0; i < log.events.length; i++) {
    const evt = log.events[i];
    applyEvent(tokens, evt);

    if (evt.type === "round_start") {
      roundIndex = evt.roundIndex;
      lastShotEvents = [];
    }
    if (evt.type === "tick_start") {
      tickIndex = evt.tickIndex;
    }
    if (evt.type === "weapon_fired") {
      lastShotEvents.push(evt);
    }
    if (evt.type === "shooting_phase_start") {
      lastShotEvents = [];
    }

    frames.push({
      eventIndex: i,
      roundIndex,
      tickIndex,
      tokens: snapshot(),
      lastShotEvents: [...lastShotEvents],
    });
  }

  return frames;
}

function applyEvent(tokens: Map<string, TokenFrame>, evt: CombatEvent): void {
  switch (evt.type) {
    case "token_moved": {
      const t = tokens.get(evt.tokenId);
      if (t) {
        t.x = evt.toPos.x;
        t.y = evt.toPos.y;
      }
      break;
    }
    case "damage_applied": {
      const t = tokens.get(evt.targetId);
      if (t) {
        t.hp = evt.remainingHp;
      }
      break;
    }
    case "token_destroyed": {
      const t = tokens.get(evt.tokenId);
      if (t) {
        t.alive = false;
        t.hp = 0;
      }
      break;
    }
    default:
      break;
  }
}

/** Find tick_start boundaries for "jump to next/prev round". */
export function findRoundBoundaries(log: CombatLog): number[] {
  const boundaries: number[] = [0];
  for (let i = 0; i < log.events.length; i++) {
    if (log.events[i].type === "round_start") {
      boundaries.push(i + 1);
    }
  }
  return boundaries;
}
