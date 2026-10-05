import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

type SnapshotCallback = (snap: object) => void;
type ErrorCallback = (err: Error) => void;

let _capturedSnapCb: SnapshotCallback | null = null;
let _capturedErrCb: ErrorCallback | null = null;

const unsubscribeMock = vi.fn();

vi.mock("firebase/firestore", () => ({
  doc: vi.fn(() => ({})),
  onSnapshot: vi.fn(
    (_docRef: object, snapCb: SnapshotCallback, errCb: ErrorCallback) => {
      _capturedSnapCb = snapCb;
      _capturedErrCb = errCb;
      return unsubscribeMock;
    },
  ),
}));

vi.mock("../lib/firebase", () => ({
  firebaseDb: {},
}));

import { useGameNotifications } from "./useGameNotifications";
import { onSnapshot } from "firebase/firestore";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fireSnap(data: object) {
  _capturedSnapCb?.({ exists: () => true, data: () => data } as never);
}

function fireError(err: Error) {
  _capturedErrCb?.(err);
}

function makeAuth(games: string[] = ["g1"]) {
  return { games, refreshSession: vi.fn() };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useGameNotifications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _capturedSnapCb = null;
    _capturedErrCb = null;
  });

  it("calls onTurnAdvanced when snapshot reports a higher turn", () => {
    const onTurnAdvanced = vi.fn();
    const onSubmissionsChanged = vi.fn();
    renderHook(() =>
      useGameNotifications({
        gameId: "g1",
        currentTurn: 1,
        onTurnAdvanced,
        onSubmissionsChanged,
        auth: makeAuth(),
      }),
    );

    act(() => fireSnap({ current_turn: 2, players_submitted: [] }));
    expect(onTurnAdvanced).toHaveBeenCalledOnce();
    expect(onTurnAdvanced).toHaveBeenCalledWith(2);
  });

  it("does not call onTurnAdvanced for same turn", () => {
    const onTurnAdvanced = vi.fn();
    renderHook(() =>
      useGameNotifications({
        gameId: "g1",
        currentTurn: 1,
        onTurnAdvanced,
        onSubmissionsChanged: vi.fn(),
        auth: makeAuth(),
      }),
    );

    act(() => fireSnap({ current_turn: 1, players_submitted: [] }));
    expect(onTurnAdvanced).not.toHaveBeenCalled();
  });

  it("calls onSubmissionsChanged when players_submitted changes, including shrink to []", () => {
    const onSubmissionsChanged = vi.fn();
    renderHook(() =>
      useGameNotifications({
        gameId: "g1",
        currentTurn: 1,
        onTurnAdvanced: vi.fn(),
        onSubmissionsChanged,
        auth: makeAuth(),
      }),
    );

    act(() => fireSnap({ current_turn: 1, players_submitted: ["tim"] }));
    expect(onSubmissionsChanged).toHaveBeenCalledWith(["tim"]);

    act(() => fireSnap({ current_turn: 2, players_submitted: [] }));
    expect(onSubmissionsChanged).toHaveBeenCalledWith([]);
  });

  it("exposes error when listener errors", () => {
    const { result } = renderHook(() =>
      useGameNotifications({
        gameId: "g1",
        currentTurn: 1,
        onTurnAdvanced: vi.fn(),
        onSubmissionsChanged: vi.fn(),
        auth: makeAuth(),
      }),
    );

    act(() => fireError(new Error("permission-denied")));
    expect(result.current.error?.message).toBe("permission-denied");
  });

  it("calls auth.refreshSession when gameId is not in claims", () => {
    const auth = makeAuth(["other-game"]);
    renderHook(() =>
      useGameNotifications({
        gameId: "g1",
        currentTurn: 1,
        onTurnAdvanced: vi.fn(),
        onSubmissionsChanged: vi.fn(),
        auth,
      }),
    );
    expect(auth.refreshSession).toHaveBeenCalledOnce();
  });

  it("re-attaches listener when gameId changes", () => {
    const { rerender } = renderHook(
      ({ gameId }) =>
        useGameNotifications({
          gameId,
          currentTurn: 1,
          onTurnAdvanced: vi.fn(),
          onSubmissionsChanged: vi.fn(),
          auth: makeAuth(["g1", "g2"]),
        }),
      { initialProps: { gameId: "g1" } },
    );

    const callsBefore = (onSnapshot as ReturnType<typeof vi.fn>).mock.calls.length;
    rerender({ gameId: "g2" });
    expect((onSnapshot as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(callsBefore);
  });
});
