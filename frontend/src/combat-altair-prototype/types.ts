/** Altair combat log types (camelCase mirrors of the backend snake_case schema). */

export interface Position {
  x: number;
  y: number;
}

export interface AltairCombatConfig {
  // These stay uppercase — keysToCamel doesn't touch single-letter keys
  S: number;
  T: number;
  // N_rounds → NRounds (capital N preserved, _r → R)
  NRounds: number;
  rulesetSchemaVersion: string;
}

export type CombatEventType =
  | "round_start"
  | "tick_start"
  | "token_moved"
  | "shooting_phase_start"
  | "weapon_fired"
  | "damage_applied"
  | "token_destroyed"
  | "round_end"
  | "battle_end";

export interface RoundStartEvent {
  type: "round_start";
  roundIndex: number;
}

export interface TickStartEvent {
  type: "tick_start";
  roundIndex: number;
  tickIndex: number;
}

export interface TokenMovedEvent {
  type: "token_moved";
  tokenId: string;
  fromPos: Position;
  toPos: Position;
  roundIndex: number;
  tickIndex: number;
}

export interface ShootingPhaseStartEvent {
  type: "shooting_phase_start";
  roundIndex: number;
}

export interface WeaponFiredEvent {
  type: "weapon_fired";
  attackerId: string;
  targetId: string;
  damage: number;
  hit: boolean;
  roundIndex: number;
}

export interface DamageAppliedEvent {
  type: "damage_applied";
  targetId: string;
  damage: number;
  remainingHp: number;
  roundIndex: number;
}

export interface TokenDestroyedEvent {
  type: "token_destroyed";
  tokenId: string;
  roundIndex: number;
}

export interface RoundEndEvent {
  type: "round_end";
  roundIndex: number;
}

export interface BattleEndEvent {
  type: "battle_end";
  reason: string;
}

export type CombatEvent =
  | RoundStartEvent
  | TickStartEvent
  | TokenMovedEvent
  | ShootingPhaseStartEvent
  | WeaponFiredEvent
  | DamageAppliedEvent
  | TokenDestroyedEvent
  | RoundEndEvent
  | BattleEndEvent;

export interface CombatLog {
  schemaVersion: string;
  config: AltairCombatConfig;
  events: CombatEvent[];
}

/** Snapshot of one token's visible state at a point in the replay. */
export interface TokenFrame {
  id: string;
  owner: string;
  x: number;
  y: number;
  hp: number;
  alive: boolean;
}

/** Full frame state at a given event index. */
export interface FrameState {
  eventIndex: number;
  roundIndex: number;
  tickIndex: number;
  tokens: TokenFrame[];
  lastShotEvents: WeaponFiredEvent[];
}
