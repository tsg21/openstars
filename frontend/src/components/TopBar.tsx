interface TopBarProps {
  gameName: string;
  turn: number;
  isDirty: boolean;
  submitted: boolean;
  onSubmit: () => void;
  submissionStatus: string;
  allSubmitted: boolean;
  onResolve: () => void;
  onLeave: () => void;
  playerName: string;
  error: string | null;
}

export function TopBar({
  gameName,
  turn,
  isDirty,
  submitted,
  onSubmit,
  submissionStatus,
  allSubmitted,
  onResolve,
  onLeave,
  playerName,
  error,
}: TopBarProps) {
  return (
    <header className="panel-surface flex h-12 items-center justify-between border-b border-[var(--color-panel-border)] px-4">
      <div className="flex items-center gap-4">
        <button
          onClick={onLeave}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          title="Back to lobby"
        >
          ←
        </button>
        <span className="text-sm font-semibold tracking-wide text-foreground">
          {gameName}
        </span>
        <span className="status-pill text-[var(--color-status-info)]">
          {isDirty ? "Command*" : "Command"}
        </span>
      </div>

      <div className="flex items-center gap-4">
        {error && (
          <span className="text-xs text-red-400 max-w-48 truncate" title={error}>
            ⚠ {error}
          </span>
        )}
        <span className="status-pill text-muted-foreground">
          {playerName}
        </span>
        <span className="status-pill text-muted-foreground">Turn {turn}</span>
        <span className="status-pill text-muted-foreground hidden sm:inline-flex">
          {submissionStatus}
        </span>

        {/* Resolve button — only shown when all players have submitted */}
        {allSubmitted && (
          <button
            onClick={onResolve}
            className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-semibold text-white shadow-[0_0_0_1px_rgb(34_197_94/0.25),0_8px_20px_rgb(34_197_94/0.15)] hover:-translate-y-px hover:bg-green-500 transition-all duration-200"
          >
            Resolve Turn
          </button>
        )}

        <button
          onClick={onSubmit}
          disabled={!isDirty && submitted}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-all duration-200 ${
            isDirty
              ? "bg-[var(--color-player-self)] text-white shadow-[0_0_0_1px_rgb(147_197_253/0.25),0_8px_20px_rgb(96_165_250/0.25)] hover:-translate-y-px hover:bg-[var(--color-player-self)]/85"
              : submitted
                ? "bg-secondary text-muted-foreground cursor-default"
                : "bg-[var(--color-player-self)]/60 text-white/80 hover:bg-[var(--color-player-self)] hover:text-white"
          }`}
        >
          {submitted && !isDirty ? "Submitted ✓" : "Submit Turn"}
        </button>
      </div>
    </header>
  );
}
