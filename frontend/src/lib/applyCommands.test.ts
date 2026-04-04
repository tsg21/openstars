import { describe, it, expect } from "vitest";
import { applyCommandsToPlayerState } from "./applyCommands";
import type { PlayerState } from "../types";

const baseState: PlayerState = {
  player: "alice",
  turn: 1,
  planets: [],
  designs: [],
  events: [],
  fleets: [
    {
      id: "FL000001",
      owner: "alice",
      name: "Fleet #1",
      position: { x: 100, y: 200 },
      composition: [],
      waypoints: [],
      repeat: false,
    },
  ],
};

describe("applyCommandsToPlayerState — set_waypoints", () => {
  it("sets repeat to true when command has repeat: true", () => {
    const result = applyCommandsToPlayerState(baseState, [
      {
        type: "set_waypoints",
        fleetId: "FL000001",
        waypoints: [],
        repeat: true,
      },
    ]);
    expect(result.fleets[0].repeat).toBe(true);
  });

  it("leaves existing repeat unchanged when command omits repeat", () => {
    const stateWithRepeat: PlayerState = {
      ...baseState,
      fleets: [{ ...baseState.fleets[0], repeat: true }],
    };
    const result = applyCommandsToPlayerState(stateWithRepeat, [
      {
        type: "set_waypoints",
        fleetId: "FL000001",
        waypoints: [],
      },
    ]);
    expect(result.fleets[0].repeat).toBe(true);
  });

  it("preserves waypoint task through apply", () => {
    const result = applyCommandsToPlayerState(baseState, [
      {
        type: "set_waypoints",
        fleetId: "FL000001",
        waypoints: [
          {
            x: 300,
            y: 400,
            task: {
              type: "transport",
              orders: [{ action: "load_all", cargoType: "ironium" }],
            },
          },
        ],
      },
    ]);
    expect(result.fleets[0].waypoints?.[0].task?.type).toBe("transport");
    expect(result.fleets[0].waypoints?.[0].task?.orders[0].cargoType).toBe(
      "ironium",
    );
  });
});

describe("applyCommandsToPlayerState — rename_fleet", () => {
  it("updates fleet.name in the working state", () => {
    const result = applyCommandsToPlayerState(baseState, [
      {
        type: "rename_fleet",
        fleetId: "FL000001",
        name: "Vanguard",
      },
    ]);

    expect(result.fleets[0].name).toBe("Vanguard");
  });

  it("ignores unknown fleets without affecting other fleets", () => {
    const result = applyCommandsToPlayerState(baseState, [
      {
        type: "rename_fleet",
        fleetId: "FL999999",
        name: "Phantom",
      },
    ]);

    expect(result.fleets).toEqual(baseState.fleets);
  });
});
