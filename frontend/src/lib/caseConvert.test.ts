import { describe, it, expect } from "vitest";
import {
  snakeToCamel,
  camelToSnake,
  keysToCamel,
  keysToSnake,
} from "./caseConvert";

describe("snakeToCamel", () => {
  it("converts simple snake_case", () => {
    expect(snakeToCamel("game_id")).toBe("gameId");
  });

  it("converts multiple underscores", () => {
    expect(snakeToCamel("all_turns_submitted")).toBe("allTurnsSubmitted");
  });

  it("leaves already camelCase unchanged", () => {
    expect(snakeToCamel("gameId")).toBe("gameId");
  });

  it("leaves single words unchanged", () => {
    expect(snakeToCamel("name")).toBe("name");
  });

  it("handles trailing underscore-digit", () => {
    expect(snakeToCamel("player_1")).toBe("player1");
  });

  it("handles empty string", () => {
    expect(snakeToCamel("")).toBe("");
  });
});

describe("camelToSnake", () => {
  it("converts simple camelCase", () => {
    expect(camelToSnake("gameId")).toBe("game_id");
  });

  it("converts multiple capitals", () => {
    expect(camelToSnake("allTurnsSubmitted")).toBe("all_turns_submitted");
  });

  it("leaves already snake_case unchanged", () => {
    expect(camelToSnake("game_id")).toBe("game_id");
  });

  it("leaves single words unchanged", () => {
    expect(camelToSnake("name")).toBe("name");
  });

  it("handles empty string", () => {
    expect(camelToSnake("")).toBe("");
  });
});

describe("keysToCamel", () => {
  it("converts flat object keys", () => {
    expect(keysToCamel({ game_id: "abc", galaxy_size: "small" })).toEqual({
      gameId: "abc",
      galaxySize: "small",
    });
  });

  it("converts nested object keys", () => {
    expect(
      keysToCamel({
        fleet_id: "FL001",
        fleet_position: { coord_x: 1, coord_y: 2 },
      }),
    ).toEqual({
      fleetId: "FL001",
      fleetPosition: { coordX: 1, coordY: 2 },
    });
  });

  it("converts keys inside arrays", () => {
    expect(
      keysToCamel({
        fleet_list: [
          { fleet_id: "FL001", design_id: "DE001" },
          { fleet_id: "FL002", design_id: "DE002" },
        ],
      }),
    ).toEqual({
      fleetList: [
        { fleetId: "FL001", designId: "DE001" },
        { fleetId: "FL002", designId: "DE002" },
      ],
    });
  });

  it("handles top-level arrays", () => {
    expect(keysToCamel([{ game_id: "a" }, { game_id: "b" }])).toEqual([
      { gameId: "a" },
      { gameId: "b" },
    ]);
  });

  it("preserves primitive values", () => {
    expect(keysToCamel(42)).toBe(42);
    expect(keysToCamel("hello")).toBe("hello");
    expect(keysToCamel(null)).toBe(null);
    expect(keysToCamel(true)).toBe(true);
  });

  it("handles null values inside objects", () => {
    expect(keysToCamel({ owner_name: null })).toEqual({ ownerName: null });
  });

  it("handles deeply nested structures", () => {
    expect(
      keysToCamel({
        outer_key: {
          middle_key: {
            inner_key: "value",
          },
        },
      }),
    ).toEqual({
      outerKey: {
        middleKey: {
          innerKey: "value",
        },
      },
    });
  });
});

describe("keysToSnake", () => {
  it("converts flat object keys", () => {
    expect(keysToSnake({ gameId: "abc", galaxySize: "small" })).toEqual({
      game_id: "abc",
      galaxy_size: "small",
    });
  });

  it("converts nested object keys", () => {
    expect(
      keysToSnake({
        fleetId: "FL001",
        fleetPosition: { coordX: 1, coordY: 2 },
      }),
    ).toEqual({
      fleet_id: "FL001",
      fleet_position: { coord_x: 1, coord_y: 2 },
    });
  });

  it("converts keys inside arrays", () => {
    expect(
      keysToSnake({
        commands: [
          { fleetId: "FL001", waypoints: [{ x: 1, y: 2 }] },
        ],
      }),
    ).toEqual({
      commands: [
        { fleet_id: "FL001", waypoints: [{ x: 1, y: 2 }] },
      ],
    });
  });

  it("preserves primitive values", () => {
    expect(keysToSnake(42)).toBe(42);
    expect(keysToSnake("hello")).toBe("hello");
    expect(keysToSnake(null)).toBe(null);
  });
});

describe("round-trip", () => {
  it("snake → camel → snake preserves keys", () => {
    const original = {
      game_id: "abc",
      galaxy_size: "small",
      all_turns_submitted: true,
      players: [{ scanner_range: 150 }],
    };
    expect(keysToSnake(keysToCamel(original))).toEqual(original);
  });

  it("camel → snake → camel preserves keys", () => {
    const original = {
      gameId: "abc",
      galaxySize: "small",
      allTurnsSubmitted: true,
      players: [{ scannerRange: 150 }],
    };
    expect(keysToCamel(keysToSnake(original))).toEqual(original);
  });
});
