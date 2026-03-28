import { useMemo } from "react";

/**
 * Hook to read game colors from CSS variables for canvas rendering.
 * This ensures a single source of truth for colors in index.css.
 */
export function useCanvasColors() {
  return useMemo(() => {
    const styles = getComputedStyle(document.documentElement);
    return {
      self: styles.getPropertyValue("--color-player-self").trim(),
      selfSelected: styles.getPropertyValue("--color-player-self-selected").trim(),
      enemy: styles.getPropertyValue("--color-player-enemy").trim(),
      uncolonised: styles.getPropertyValue("--color-planet-uncolonised").trim(),
    };
  }, []);
}
