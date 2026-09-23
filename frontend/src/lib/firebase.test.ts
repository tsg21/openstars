import { describe, it, expect, vi, beforeEach } from "vitest";

const mockAuth = {};
const mockDb = {};
const mockApp = {};

const connectAuthEmulatorMock = vi.fn();
const connectFirestoreEmulatorMock = vi.fn();

vi.mock("firebase/app", () => ({
  initializeApp: vi.fn(() => mockApp),
}));
vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(() => mockAuth),
  connectAuthEmulator: connectAuthEmulatorMock,
  GoogleAuthProvider: class {},
}));
vi.mock("firebase/firestore", () => ({
  getFirestore: vi.fn(() => mockDb),
  connectFirestoreEmulator: connectFirestoreEmulatorMock,
}));

describe("firebase module", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("exports firebaseAuth and firebaseDb", async () => {
    vi.stubEnv("VITE_FIREBASE_USE_EMULATORS", "false");
    const { firebaseAuth, firebaseDb } = await import("./firebase");
    expect(firebaseAuth).toBe(mockAuth);
    expect(firebaseDb).toBe(mockDb);
    vi.unstubAllEnvs();
  });

  it("does not connect emulators when flag is off", async () => {
    vi.stubEnv("VITE_FIREBASE_USE_EMULATORS", "false");
    await import("./firebase");
    expect(connectAuthEmulatorMock).not.toHaveBeenCalled();
    expect(connectFirestoreEmulatorMock).not.toHaveBeenCalled();
    vi.unstubAllEnvs();
  });

  it("connects emulators when VITE_FIREBASE_USE_EMULATORS=true", async () => {
    vi.stubEnv("VITE_FIREBASE_USE_EMULATORS", "true");
    await import("./firebase");
    expect(connectAuthEmulatorMock).toHaveBeenCalledWith(
      mockAuth,
      "http://localhost:9099",
      { disableWarnings: true },
    );
    expect(connectFirestoreEmulatorMock).toHaveBeenCalledWith(
      mockDb,
      "localhost",
      8085,
    );
    vi.unstubAllEnvs();
  });
});
