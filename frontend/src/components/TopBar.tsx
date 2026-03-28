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
    <header className="panel-surface flex h-12 items-center justify-between border-b border-[var(--color-panel-border)] px-4">
      <div className="flex items-center gap-4">
        <span className="text-sm font-semibold tracking-wide text-foreground">
          {gameName}
        </span>
        <span className="status-pill text-[var(--color-status-info)]">
          Command
        </span>
      </div>

      <div className="flex items-center gap-4">
        <span className="status-pill text-muted-foreground">Turn {turn}</span>
        <span className="status-pill text-muted-foreground hidden sm:inline-flex">
          {submissionStatus}
        </span>
        <button
          onClick={onSubmit}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-all duration-200 ${
            isDirty
              ? "bg-[var(--color-player-self)] text-white shadow-[0_0_0_1px_rgb(147_197_253/0.25),0_8px_20px_rgb(96_165_250/0.25)] hover:-translate-y-px hover:bg-[var(--color-player-self)]/85"
              : "bg-secondary text-muted-foreground"
          }`}
        >
          {isDirty ? "Submit Turn" : "Submitted ✓"}
        </button>
      </div>
    </header>
  );
}
