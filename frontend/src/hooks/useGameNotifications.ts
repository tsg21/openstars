import { useState, useEffect, useLayoutEffect, useRef } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { firebaseDb } from "../lib/firebase";
import type { FirebaseAuthHook } from "./useFirebaseAuth";

export interface UseGameNotificationsOptions {
  gameId: string | null;
  currentTurn: number | null;
  onTurnAdvanced: (newTurn: number) => void;
  onSubmissionsChanged: (playersSubmitted: string[]) => void;
  auth: FirebaseAuthHook;
}

export interface GameNotificationsHook {
  error: Error | null;
}

export function useGameNotifications({
  gameId,
  currentTurn,
  onTurnAdvanced,
  onSubmissionsChanged,
  auth,
}: UseGameNotificationsOptions): GameNotificationsHook {
  const [error, setError] = useState<Error | null>(null);

  // Stable refs so snapshot callback never closes over stale values
  const currentTurnRef = useRef(currentTurn);
  const onTurnAdvancedRef = useRef(onTurnAdvanced);
  const onSubmissionsChangedRef = useRef(onSubmissionsChanged);

  useLayoutEffect(() => {
    currentTurnRef.current = currentTurn;
    onTurnAdvancedRef.current = onTurnAdvanced;
    onSubmissionsChangedRef.current = onSubmissionsChanged;
  });

  // Destructure stable primitives: `claims` is React state (same reference between
  // renders unless auth actually changes) and `refresh` is a useCallback. Depending
  // on the whole `auth` object would re-subscribe on every unrelated render because
  // useFirebaseAuth returns a fresh object reference each time.
  const { claims, refresh } = auth;

  useEffect(() => {
    if (!gameId) return;

    // If this game is not in our token claims, refresh the token first
    if (claims && !claims.games.includes(gameId)) {
      refresh();
    }

    const gameDoc = doc(firebaseDb, "games", gameId);
    const unsubscribe = onSnapshot(
      gameDoc,
      (snapshot) => {
        if (!snapshot.exists()) return;
        const data = snapshot.data();
        const snapshotTurn: number = data.current_turn ?? 0;
        const playersSubmitted: string[] = data.players_submitted ?? [];

        if (
          currentTurnRef.current !== null &&
          snapshotTurn > currentTurnRef.current
        ) {
          onTurnAdvancedRef.current(snapshotTurn);
        }

        onSubmissionsChangedRef.current(playersSubmitted);
      },
      (err) => {
        setError(err instanceof Error ? err : new Error(String(err)));
      },
    );

    return unsubscribe;
  }, [gameId, claims, refresh]);

  return { error };
}
