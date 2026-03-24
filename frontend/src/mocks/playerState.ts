import type { PlayerState, Design } from "../types";
import { mockGalaxy } from "./galaxy";

/**
 * Mock player state for Tim at turn 3.
 *
 * Tim owns Sol, Alpha Centauri, and Proxima. He has two fleets:
 * - Scout Alpha: at Alpha Centauri, heading toward Kapteyn (exploring)
 * - Scout Beta: stationary at Sol
 *
 * Tim can see some of Sara's stuff near scanner range.
 */

// Grab planet positions from the galaxy for convenience
function planetPos(id: string) {
  const p = mockGalaxy.planets.find((pl) => pl.id === id);
  if (!p) throw new Error(`Planet ${id} not found in mock galaxy`);
  return { x: p.x, y: p.y };
}

// Designs visible to Tim
const timScout: Design = {
  id: "DEa3f0p5",
  owner: "tim",
  name: "Long Range Scout",
  hull: "scout",
  speed: 6,
  scannerRange: 150,
};

export const mockPlayerState: PlayerState = {
  player: "tim",
  turn: 3,

  designs: [timScout],

  planets: [
    // --- Tim's planets (full detail) ---
    {
      id: "PLk8m3x2",
      name: "Sol",
      ...planetPos("PLk8m3x2"),
      owner: "tim",
      population: 28000,
    },
    {
      id: "PL4fn9v6",
      name: "Alpha Centauri",
      ...planetPos("PL4fn9v6"),
      owner: "tim",
      population: 10000,
    },
    {
      id: "PLr2j5b8",
      name: "Proxima",
      ...planetPos("PLr2j5b8"),
      owner: "tim",
      population: 5000,
    },

    // --- Uncolonised planets in scanner range ---
    {
      id: "PL7pd1w4",
      name: "Barnard",
      ...planetPos("PL7pd1w4"),
      owner: null,
      population: 0,
    },
    {
      id: "PLm6a9c3",
      name: "Procyon",
      ...planetPos("PLm6a9c3"),
      owner: null,
      population: 0,
    },
    {
      id: "PLy3k7d1",
      name: "Luyten",
      ...planetPos("PLy3k7d1"),
      owner: null,
      population: 0,
    },
    {
      id: "PLb9f2h5",
      name: "Wolf",
      ...planetPos("PLb9f2h5"),
      owner: null,
      population: 0,
    },
    {
      id: "PLc1n8t4",
      name: "Lalande",
      ...planetPos("PLc1n8t4"),
      owner: null,
      population: 0,
    },

    // --- Planets visible via Scout Alpha's scanner (explored area) ---
    {
      id: "PLd5q3v7",
      name: "Kapteyn",
      ...planetPos("PLd5q3v7"),
      owner: null,
      population: 0,
    },
    {
      id: "PLe7w1m9",
      name: "Kruger",
      ...planetPos("PLe7w1m9"),
      owner: null,
      population: 0,
    },

    // --- Sara's planet barely in scanner range (limited info) ---
    {
      id: "PLp5w2e6",
      name: "Rigel",
      ...planetPos("PLp5w2e6"),
      owner: "sara",
    },
  ],

  fleets: [
    // --- Tim's fleets (full detail) ---
    {
      id: "FL9qb7w1",
      owner: "tim",
      position: planetPos("PL4fn9v6"), // at Alpha Centauri
      composition: [{ designId: "DEa3f0p5", count: 1 }],
      waypoints: [
        planetPos("PLd5q3v7"), // heading to Kapteyn
        planetPos("PLf4x6j2"), // then Ross
      ],
    },
    {
      id: "FLp4h8e2",
      owner: "tim",
      position: planetPos("PLk8m3x2"), // at Sol
      composition: [{ designId: "DEa3f0p5", count: 1 }],
      waypoints: [], // stationary
    },

    // --- Sara's fleet detected near Rigel (limited info) ---
    {
      id: "FLx7c3k9",
      owner: "sara",
      position: planetPos("PLp5w2e6"), // at Rigel
      // No composition or waypoints — enemy fleet, limited visibility
    },
  ],

  events: [
    {
      type: "fleet_arrived",
      fleetId: "FL9qb7w1",
      fleetName: "Scout Alpha",
      planetId: "PL4fn9v6",
      planetName: "Alpha Centauri",
      turn: 3,
    },
    {
      type: "planet_scanned",
      planetId: "PLe7w1m9",
      planetName: "Kruger",
      owner: null,
      population: 0,
      turn: 3,
    },
    {
      type: "fleet_detected",
      owner: "sara",
      planetId: "PLp5w2e6",
      planetName: "Rigel",
      position: planetPos("PLp5w2e6"),
      turn: 3,
    },
  ],
};
