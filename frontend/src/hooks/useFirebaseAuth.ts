import { useState, useEffect, useLayoutEffect, useCallback, useRef } from "react";
import { signInWithCustomToken } from "firebase/auth";
import { firebaseAuth } from "../lib/firebase";
import { fetchFirebaseToken } from "../api/client";

export type FirebaseAuthStatus = "idle" | "signed-in" | "error";

export interface FirebaseAuthClaims {
  games: string[];
}

export interface FirebaseAuthHook {
  status: FirebaseAuthStatus;
  claims: FirebaseAuthClaims | null;
  error: Error | null;
  refresh: () => Promise<void>;
}

interface AuthState {
  status: FirebaseAuthStatus;
  claims: FirebaseAuthClaims | null;
  error: Error | null;
}

const IDLE_STATE: AuthState = { status: "idle", claims: null, error: null };
const REFRESH_BEFORE_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes

export function useFirebaseAuth(player: string | null): FirebaseAuthHook {
  const [{ status, claims, error }, setAuthState] = useState<AuthState>(IDLE_STATE);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activePlayerRef = useRef(player);
  // Ref to call authenticate recursively from the timer (avoids TDZ lint error)
  const authenticateRef = useRef<((player: string) => Promise<void>) | null>(null);

  useLayoutEffect(() => {
    activePlayerRef.current = player;
  });

  const authenticate = useCallback(async (currentPlayer: string) => {
    try {
      const { token, expiresAt } = await fetchFirebaseToken(currentPlayer);
      if (activePlayerRef.current !== currentPlayer) return;

      await signInWithCustomToken(firebaseAuth, token);
      if (activePlayerRef.current !== currentPlayer) return;

      const idTokenResult = await firebaseAuth.currentUser?.getIdTokenResult();
      const gameClaims = (idTokenResult?.claims?.games as string[]) ?? [];

      setAuthState({ status: "signed-in", claims: { games: gameClaims }, error: null });

      // Schedule proactive refresh before expiry
      const expiryMs = new Date(expiresAt).getTime();
      const refreshInMs = Math.max(0, expiryMs - Date.now() - REFRESH_BEFORE_EXPIRY_MS);
      if (refreshTimerRef.current !== null) clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(() => {
        if (activePlayerRef.current === currentPlayer) {
          void authenticateRef.current?.(currentPlayer);
        }
      }, refreshInMs);
    } catch (err) {
      if (activePlayerRef.current !== currentPlayer) return;
      setAuthState({
        status: "error",
        claims: null,
        error: err instanceof Error ? err : new Error(String(err)),
      });
    }
  }, []);

  // Keep the ref current so the timer callback always calls the latest version
  useLayoutEffect(() => {
    authenticateRef.current = authenticate;
  });

  const refresh = useCallback(async () => {
    if (!activePlayerRef.current) return;
    await authenticate(activePlayerRef.current);
  }, [authenticate]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!player) { setAuthState(IDLE_STATE); return; }
    setAuthState(IDLE_STATE);
    void authenticate(player);

    return () => {
      if (refreshTimerRef.current !== null) clearTimeout(refreshTimerRef.current);
    };
  }, [player, authenticate]);

  return { status, claims, error, refresh };
}
