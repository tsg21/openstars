import type { Galaxy } from "../types";
import { PARSEC } from "../types";

/**
 * Mock galaxy — a small (40-bit) galaxy with 20 planets.
 *
 * Placement region: middle 50% of the 40-bit range (274,877,906,944 to
 * 824,633,720,831). All planet coordinates are within this region.
 *
 * Distances between neighbouring planets are roughly 40-120 parsecs
 * (a parsec = 536,870,912 coordinate units).
 */

// Helpers — place planets relative to a centre point in parsec offsets
const MID = 549_755_813_888; // centre of 40-bit range

function pos(parsecX: number, parsecY: number): { x: number; y: number } {
  return {
    x: MID + parsecX * PARSEC,
    y: MID + parsecY * PARSEC,
  };
}

export const mockGalaxy: Galaxy = {
  galaxy: {
    name: "Alpha Sector",
    size: "small",
    seed: 42,
  },
  planets: [
    // --- Tim's region (south-west quadrant) ---
    { id: "PLk8m3x2", name: "Sol", ...pos(0, 0) },
    { id: "PL4fn9v6", name: "Alpha Centauri", ...pos(45, 20) },
    { id: "PLr2j5b8", name: "Proxima", ...pos(-30, 55) },
    { id: "PL7pd1w4", name: "Barnard", ...pos(80, -40) },
    { id: "PLm6a9c3", name: "Procyon", ...pos(-60, -30) },
    { id: "PLy3k7d1", name: "Luyten", ...pos(20, -70) },
    { id: "PLb9f2h5", name: "Wolf", ...pos(-80, 10) },
    { id: "PLc1n8t4", name: "Lalande", ...pos(55, 70) },

    // --- No-man's land (centre) ---
    { id: "PLd5q3v7", name: "Kapteyn", ...pos(150, 50) },
    { id: "PLe7w1m9", name: "Kruger", ...pos(120, -30) },
    { id: "PLf4x6j2", name: "Ross", ...pos(170, 100) },
    { id: "PLg8r2p6", name: "Groombridge", ...pos(200, -10) },

    // --- Sara's region (north-east quadrant) ---
    { id: "PLh2s5a8", name: "Sirius", ...pos(300, 150) },
    { id: "PLj6t9b3", name: "Vega", ...pos(340, 100) },
    { id: "PLl1u4c7", name: "Altair", ...pos(260, 200) },
    { id: "PLn3v8d2", name: "Deneb", ...pos(370, 180) },
    { id: "PLp5w2e6", name: "Rigel", ...pos(280, 80) },
    { id: "PLq9x6f1", name: "Betelgeuse", ...pos(320, 250) },
    { id: "PLs4y1g5", name: "Canopus", ...pos(250, 130) },
    { id: "PLt8z3h9", name: "Arcturus", ...pos(380, 50) },
  ],
};
