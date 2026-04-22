import { describe, it, expect } from "vitest";
import { buildFrames, findRoundBoundaries, type InitialToken } from "./replayReducer";
import type { CombatLog, CombatEvent } from "./types";

function makeTwoTokenLog(): { log: CombatLog; initialTokens: InitialToken[] } {
  const events: CombatEvent[] = [
    { type: "round_start", roundIndex: 0 },
    { type: "tick_start", roundIndex: 0, tickIndex: 0 },
    {
      type: "token_moved",
      tokenId: "a1",
      fromPos: { x: 100, y: 500 },
      toPos: { x: 150, y: 500 },
      roundIndex: 0,
      tickIndex: 0,
    },
    { type: "tick_start", roundIndex: 0, tickIndex: 1 },
    {
      type: "token_moved",
      tokenId: "a1",
      fromPos: { x: 150, y: 500 },
      toPos: { x: 200, y: 500 },
      roundIndex: 0,
      tickIndex: 1,
    },
    { type: "shooting_phase_start", roundIndex: 0 },
    {
      type: "weapon_fired",
      attackerId: "a1",
      targetId: "b1",
      damage: 20,
      hit: true,
      roundIndex: 0,
    },
    {
      type: "damage_applied",
      targetId: "b1",
      damage: 20,
      remainingHp: 80,
      roundIndex: 0,
    },
    { type: "round_end", roundIndex: 0 },
    { type: "battle_end", reason: "max_rounds_reached" },
  ];

  const initialTokens: InitialToken[] = [
    { id: "a1", owner: "alice", x: 100, y: 500, hp: 100 },
    { id: "b1", owner: "bob", x: 900, y: 500, hp: 100 },
  ];

  const log: CombatLog = {
    schemaVersion: "altair-v1",
    config: { S: 1000, T: 20, NRounds: 16, rulesetSchemaVersion: "altair-v1" },
    events,
  };

  return { log, initialTokens };
}

describe("buildFrames", () => {
  it("produces one more frame than events (initial + per-event)", () => {
    const { log, initialTokens } = makeTwoTokenLog();
    const frames = buildFrames(log, initialTokens);
    expect(frames.length).toBe(log.events.length + 1);
  });

  it("initial frame has starting positions", () => {
    const { log, initialTokens } = makeTwoTokenLog();
    const frames = buildFrames(log, initialTokens);
    const a1 = frames[0].tokens.find((t) => t.id === "a1");
    expect(a1?.x).toBe(100);
    expect(a1?.hp).toBe(100);
    expect(a1?.alive).toBe(true);
  });

  it("applies token_moved events", () => {
    const { log, initialTokens } = makeTwoTokenLog();
    const frames = buildFrames(log, initialTokens);
    // After event index 2 (first token_moved) → frame index 3
    const a1 = frames[3].tokens.find((t) => t.id === "a1");
    expect(a1?.x).toBe(150);
  });

  it("applies damage events", () => {
    const { log, initialTokens } = makeTwoTokenLog();
    const frames = buildFrames(log, initialTokens);
    // After damage_applied event → b1 should have 80 hp
    const damageFrame = frames.find(
      (f) => f.eventIndex >= 0 && log.events[f.eventIndex].type === "damage_applied",
    );
    const b1 = damageFrame?.tokens.find((t) => t.id === "b1");
    expect(b1?.hp).toBe(80);
  });

  it("tracks weapon_fired in lastShotEvents", () => {
    const { log, initialTokens } = makeTwoTokenLog();
    const frames = buildFrames(log, initialTokens);
    const shotFrame = frames.find(
      (f) => f.eventIndex >= 0 && log.events[f.eventIndex].type === "weapon_fired",
    );
    expect(shotFrame?.lastShotEvents.length).toBe(1);
    expect(shotFrame?.lastShotEvents[0].attackerId).toBe("a1");
  });
});

describe("findRoundBoundaries", () => {
  it("returns boundaries including frame 0", () => {
    const { log } = makeTwoTokenLog();
    const boundaries = findRoundBoundaries(log);
    expect(boundaries[0]).toBe(0);
    expect(boundaries.length).toBeGreaterThanOrEqual(1);
  });
});
