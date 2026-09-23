import { useState, useEffect, useCallback, useRef } from "react";
import {
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  type User,
} from "firebase/auth";
import { firebaseAuth, googleProvider } from "../lib/firebase";
import { postAuthSession, setAuthTokenGetter } from "../api/client";

export type AuthStatus = "loading" | "signed-out" | "signed-in" | "error";

export interface AuthUser {
  email: string;
  displayName: string | null;
}

export interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
  games: string[];
  error: Error | null;
}

export interface AuthHook extends AuthState {
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const SIGNED_OUT: AuthState = {
  status: "signed-out",
  user: null,
  games: [],
  error: null,
};

// Dismissing the Google popup is a decision, not a failure.
const CANCELLED_CODES = new Set([
  "auth/popup-closed-by-user",
  "auth/cancelled-popup-request",
]);

function isCancellation(err: unknown): boolean {
  return (
    typeof err === "object" &&
    err !== null &&
    "code" in err &&
    CANCELLED_CODES.has((err as { code: string }).code)
  );
}

function toError(err: unknown): Error {
  return err instanceof Error ? err : new Error(String(err));
}

// The API client asks for the token per request; the SDK handles expiry.
setAuthTokenGetter(async () => {
  const user = firebaseAuth.currentUser;
  return user ? await user.getIdToken() : null;
});

/**
 * Owns the whole signed-in session: Firebase user, Firestore `games` claim, and
 * the identity the rest of the app treats as the player.
 */
export function useAuth(): AuthHook {
  const [state, setState] = useState<AuthState>({
    status: "loading",
    user: null,
    games: [],
    error: null,
  });

  // Guards against a resolved promise from a session that has since ended.
  const currentUidRef = useRef<string | null>(null);

  const establishSession = useCallback(async (user: User) => {
    // Order matters: the session call writes the `games` claim, and only tokens
    // minted afterwards carry it. Refreshing first yields a stale token and
    // Firestore then denies the listener.
    const session = await postAuthSession();
    await user.getIdToken(true);

    if (currentUidRef.current !== user.uid) return;

    setState({
      status: "signed-in",
      user: { email: session.username, displayName: session.displayName },
      games: session.games,
      error: null,
    });
  }, []);

  useEffect(() => {
    return onAuthStateChanged(firebaseAuth, (user) => {
      currentUidRef.current = user?.uid ?? null;
      if (!user) {
        setState(SIGNED_OUT);
        return;
      }
      setState((prev) => ({ ...prev, status: "loading", error: null }));
      void establishSession(user).catch((err) => {
        if (currentUidRef.current !== user.uid) return;
        setState({
          status: "error",
          user: null,
          games: [],
          error: toError(err),
        });
      });
    });
  }, [establishSession]);

  const signIn = useCallback(async () => {
    setState((prev) => ({ ...prev, status: "loading", error: null }));
    try {
      // onAuthStateChanged picks it up from here and establishes the session.
      await signInWithPopup(firebaseAuth, googleProvider);
    } catch (err) {
      if (isCancellation(err)) {
        setState(SIGNED_OUT);
        return;
      }
      setState({ status: "error", user: null, games: [], error: toError(err) });
    }
  }, []);

  const signOut = useCallback(async () => {
    await firebaseSignOut(firebaseAuth);
    currentUidRef.current = null;
    setState(SIGNED_OUT);
  }, []);

  const refreshSession = useCallback(async () => {
    const user = firebaseAuth.currentUser;
    if (!user) return;
    try {
      await establishSession(user);
    } catch (err) {
      setState({ status: "error", user: null, games: [], error: toError(err) });
    }
  }, [establishSession]);

  return { ...state, signIn, signOut, refreshSession };
}
