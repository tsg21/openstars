import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { signInMock, getIdTokenResultMock, fetchFirebaseTokenMock } =
  vi.hoisted(() => ({
    signInMock: vi.fn(),
    getIdTokenResultMock: vi.fn(),
    fetchFirebaseTokenMock: vi.fn(),
  }));

vi.mock("../lib/firebase", () => ({
  firebaseAuth: {
    get currentUser() {
      return { getIdTokenResult: getIdTokenResultMock };
    },
  },
}));

vi.mock("firebase/auth", () => ({
  signInWithCustomToken: signInMock,
}));

vi.mock("../api/client", () => ({
  fetchFirebaseToken: fetchFirebaseTokenMock,
}));

// ---------------------------------------------------------------------------
// Import under test (after mocks are declared)
// ---------------------------------------------------------------------------

import { useFirebaseAuth } from "./useFirebaseAuth";

const ONE_HOUR_FROM_NOW = () =>
  new Date(Date.now() + 3600 * 1000).toISOString();

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useFirebaseAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    signInMock.mockResolvedValue(undefined);
    getIdTokenResultMock.mockResolvedValue({ claims: { games: ["g1"] } });
    fetchFirebaseTokenMock.mockResolvedValue({
      token: "tok",
      expiresAt: ONE_HOUR_FROM_NOW(),
    });
  });

  it("fetches a token and calls signInWithCustomToken on mount", async () => {
    const { result } = renderHook(() => useFirebaseAuth("tim"));
    await waitFor(() => expect(result.current.status).toBe("signed-in"));
    expect(fetchFirebaseTokenMock).toHaveBeenCalledWith("tim");
    expect(signInMock).toHaveBeenCalledWith(expect.anything(), "tok");
  });

  it("exposes status: signed-in and claims.games after auth", async () => {
    const { result } = renderHook(() => useFirebaseAuth("tim"));
    await waitFor(() => expect(result.current.status).toBe("signed-in"));
    expect(result.current.claims?.games).toEqual(["g1"]);
    expect(result.current.error).toBeNull();
  });

  it("exposes status: error when token endpoint fails", async () => {
    fetchFirebaseTokenMock.mockRejectedValue(new Error("500 server error"));
    const { result } = renderHook(() => useFirebaseAuth("tim"));
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error?.message).toBe("500 server error");
  });

  it("exposes status: error when sign-in fails", async () => {
    signInMock.mockRejectedValue(new Error("auth failed"));
    const { result } = renderHook(() => useFirebaseAuth("tim"));
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error?.message).toBe("auth failed");
  });

  it("re-authenticates when player changes", async () => {
    const { result, rerender } = renderHook(
      ({ player }) => useFirebaseAuth(player),
      { initialProps: { player: "tim" } },
    );
    await waitFor(() => expect(result.current.status).toBe("signed-in"));

    fetchFirebaseTokenMock.mockClear();
    rerender({ player: "matt" });
    await waitFor(() =>
      expect(fetchFirebaseTokenMock).toHaveBeenCalledWith("matt"),
    );
  });

  it("calling refresh re-authenticates", async () => {
    const { result } = renderHook(() => useFirebaseAuth("tim"));
    await waitFor(() => expect(result.current.status).toBe("signed-in"));

    fetchFirebaseTokenMock.mockClear();
    await act(() => result.current.refresh());
    expect(fetchFirebaseTokenMock).toHaveBeenCalledTimes(1);
  });
});
