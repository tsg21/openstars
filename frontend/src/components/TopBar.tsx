import { useMemo } from "react";
interface TopBarProps {
  gameName: string;
  turn: number;
  isDirty: boolean;
  onSubmit: () => void;
}

export function TopBar({
  gameName,
  turn,
  isDirty,
  onSubmit,
}: TopBarProps) {
  const submissionStatus = useMemo(() => {
    // Placeholder — in the real game this comes from the server
    return "Waiting: 1 of 2 players";
  }, []);

  return (
    <header className="flex h-10 items-center justify-between border-b border-[var(--color-panel-border)] bg-[var(--color-panel-bg)] px-4">
      <div className="flex items-center gap-4">
        <span className="text-sm font-bold text-foreground">{gameName}</span>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-xs text-muted-foreground">Turn {turn}</span>
        <span className="text-xs text-muted-foreground">
          {submissionStatus}
        </span>
        <button
          onClick={onSubmit}
          className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
            isDirty
              ? "bg-[var(--color-player-self)] text-white hover:bg-[var(--color-player-self)]/80"
              : "bg-secondary text-muted-foreground"
          }`}
        >
          {isDirty ? "Submit Turn" : "Submitted ✓"}
        </button>
      </div>
    </header>
  );
}
