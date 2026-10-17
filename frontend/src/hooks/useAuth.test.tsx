import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

const {
  signInWithPopupMock,
  signOutMock,
  onAuthStateChangedMock,
  getIdTokenMock,
  postAuthSessionMock,
  registeredGetters,
} = vi.hoisted(() => ({
  signInWithPopupMock: vi.fn(),
  signOutMock: vi.fn(),
  onAuthStateChangedMock: vi.fn(),
  getIdTokenMock: vi.fn(),
  postAuthSessionMock: vi.fn(),
  // A plain array, not a vi.fn: registration happens at module import time and
  // clearAllMocks() would erase the record before any test could see it.
  registeredGetters: [] as (() => Promise<string | null>)[],
}));

vi.mock("firebase/auth", () => ({
  signInWithPopup: signInWithPopupMock,
  signOut: signOutMock,
  onAuthStateChanged: onAuthStateChangedMock,
  GoogleAuthProvider: class {},
}));

vi.mock("../lib/firebase", () => ({
  firebaseAuth: { currentUser: null },
  googleProvider: {},
}));

vi.mock("../api/client", () => ({
  postAuthSession: postAuthSessionMock,
  setAuthTokenGetter: (getter: () => Promise<string | null>) => {
    registeredGetters.push(getter);
  },
}));

import { useAuth } from "./useAuth";
import { firebaseAuth } from "../lib/firebase";

/** Drives the onAuthStateChanged callback the hook registers. */
let emitAuthState: (user: unknown) => void = () => {};

function makeUser(uid = "uid-1") {
  return { uid, getIdToken: getIdTokenMock };
}

beforeEach(() => {
  vi.clearAllMocks();
  (firebaseAuth as { currentUser: unknown }).currentUser = null;
  onAuthStateChangedMock.mockImplementation((_auth, cb) => {
    emitAuthState = cb;
    return () => {};
  });
  getIdTokenMock.mockResolvedValue("fresh-token");
  postAuthSessionMock.mockResolvedValue({
    username: "alice@example.com",
    displayName: "Alice",
    games: ["g1", "g2"],
  });
});

describe("useAuth", () => {
  it("starts in loading and settles to signed-out when there is no user", async () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.status).toBe("loading");

    act(() => emitAuthState(null));

    await waitFor(() => expect(result.current.status).toBe("signed-out"));
    expect(result.current.user).toBeNull();
    expect(result.current.games).toEqual([]);
  });

  it("populates email, display name and games on a successful sign-in", async () => {
    const { result } = renderHook(() => useAuth());

    act(() => emitAuthState(makeUser()));

    await waitFor(() => expect(result.current.status).toBe("signed-in"));
    expect(result.current.user).toEqual({
      email: "alice@example.com",
      displayName: "Alice",
    });
    expect(result.current.games).toEqual(["g1", "g2"]);
  });

  it("calls the session endpoint before forcing a token refresh", async () => {
    const order: string[] = [];
    postAuthSessionMock.mockImplementation(async () => {
      order.push("session");
      return { username: "a@example.com", displayName: null, games: [] };
    });
    getIdTokenMock.mockImplementation(async () => {
      order.push("refresh");
      return "t";
    });

    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(makeUser()));
    await waitFor(() => expect(result.current.status).toBe("signed-in"));

    // Refreshing first would mint a token without the `games` claim, and the
    // Firestore listener would then be denied.
    expect(order).toEqual(["session", "refresh"]);
    expect(getIdTokenMock).toHaveBeenCalledWith(true);
  });

  it("surfaces a failing session call without a half-signed-in state", async () => {
    postAuthSessionMock.mockRejectedValue(new Error("500 server error"));

    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(makeUser()));

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error?.message).toContain("500");
    expect(result.current.user).toBeNull();
    expect(result.current.games).toEqual([]);
  });

  it("treats a dismissed popup as a return to signed-out, not an error", async () => {
    signInWithPopupMock.mockRejectedValue({ code: "auth/popup-closed-by-user" });

    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(null));
    await waitFor(() => expect(result.current.status).toBe("signed-out"));

    await act(async () => {
      await result.current.signIn();
    });

    expect(result.current.status).toBe("signed-out");
    expect(result.current.error).toBeNull();
  });

  it("treats a cancelled popup request the same way", async () => {
    signInWithPopupMock.mockRejectedValue({
      code: "auth/cancelled-popup-request",
    });

    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(null));
    await waitFor(() => expect(result.current.status).toBe("signed-out"));

    await act(async () => {
      await result.current.signIn();
    });

    expect(result.current.status).toBe("signed-out");
    expect(result.current.error).toBeNull();
  });

  it("reports a genuine sign-in failure as an error", async () => {
    signInWithPopupMock.mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(null));
    await waitFor(() => expect(result.current.status).toBe("signed-out"));

    await act(async () => {
      await result.current.signIn();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error?.message).toBe("network down");
  });

  it("signOut clears the user and games", async () => {
    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(makeUser()));
    await waitFor(() => expect(result.current.status).toBe("signed-in"));

    signOutMock.mockResolvedValue(undefined);
    await act(async () => {
      await result.current.signOut();
    });

    expect(signOutMock).toHaveBeenCalled();
    expect(result.current.status).toBe("signed-out");
    expect(result.current.user).toBeNull();
    expect(result.current.games).toEqual([]);
  });

  it("refreshSession re-issues both calls", async () => {
    const user = makeUser();
    const { result } = renderHook(() => useAuth());
    act(() => emitAuthState(user));
    await waitFor(() => expect(result.current.status).toBe("signed-in"));

    (firebaseAuth as { currentUser: unknown }).currentUser = user;
    postAuthSessionMock.mockClear();
    getIdTokenMock.mockClear();
    postAuthSessionMock.mockResolvedValue({
      username: "alice@example.com",
      displayName: "Alice",
      games: ["g1", "g2", "g3"],
    });

    await act(async () => {
      await result.current.refreshSession();
    });

    expect(postAuthSessionMock).toHaveBeenCalledTimes(1);
    expect(getIdTokenMock).toHaveBeenCalledWith(true);
    expect(result.current.games).toEqual(["g1", "g2", "g3"]);
  });

  it("registers a token getter that reads the current user's token", async () => {
    expect(registeredGetters).toHaveLength(1);
    const getter = registeredGetters[0];

    expect(await getter()).toBeNull();

    (firebaseAuth as { currentUser: unknown }).currentUser = makeUser();
    getIdTokenMock.mockResolvedValue("live-token");
    expect(await getter()).toBe("live-token");
    // Unforced: the SDK refreshes an expiring token by itself.
    expect(getIdTokenMock).toHaveBeenCalledWith();
  });
});
