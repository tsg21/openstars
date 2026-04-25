import type { PlayerStateResearch } from "../types";
import { Button } from "./Button";
import { MutedText } from "./MutedText";

interface TopBarProps {
  gameName: string;
  turn: number;
  isDirty: boolean;
  submitted: boolean;
  waitingForNextTurn: boolean;
  mode: "command" | "designer" | "research";
  onModeChange: (mode: "command" | "designer" | "research") => void;
  onSubmit: () => void;
  submissionStatus: string;
  allSubmitted: boolean;
  onResolve: () => void;
  onLeave: () => void;
  playerName: string;
  error: string | null;
  research: PlayerStateResearch | null;
}

export function TopBar({
  gameName,
  turn,
  isDirty,
  submitted,
  waitingForNextTurn,
  mode,
  onModeChange,
  onSubmit,
  submissionStatus,
  allSubmitted,
  onResolve,
  onLeave,
  playerName,
  error,
  research,
}: TopBarProps) {
  return (
    <header className="panel-surface flex h-14 items-center justify-between gap-4 border-b border-[var(--color-panel-border)] px-4">
      <div className="flex min-w-0 items-center gap-4">
        <span className="text-base font-semibold tracking-[0.18em] text-foreground">
          OpenStars!
        </span>
        <span
          className="truncate text-sm font-semibold text-foreground"
          title={gameName}
        >
          {gameName}
        </span>
        <div
          className="flex items-center rounded-lg border border-[var(--color-panel-border)] bg-background/60 p-1"
          aria-label="View selector"
        >
          <Button
            variant={mode === "command" ? "primary" : "ghost"}
            size="xs"
            onClick={() => onModeChange("command")}
          >
            {isDirty ? "Command*" : "Command"}
          </Button>
          <Button
            variant={mode === "designer" ? "primary" : "ghost"}
            size="xs"
            onClick={() => onModeChange("designer")}
          >
            Designer
          </Button>
          {research && (
            <Button
              variant={mode === "research" ? "primary" : "ghost"}
              size="xs"
              onClick={() => onModeChange("research")}
            >
              Research
            </Button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {error && (
          <span className="text-xs text-red-400 max-w-48 truncate" title={error}>
            ⚠ {error}
          </span>
        )}
        <MutedText className="status-pill">
          {playerName}
        </MutedText>
        <MutedText className="status-pill">Turn {turn}</MutedText>
        <MutedText
          className={`status-pill hidden sm:inline-flex ${
            waitingForNextTurn
              ? "animate-pulse text-[var(--color-status-info)]"
              : ""
          }`}
        >
          {submissionStatus}
        </MutedText>

        {allSubmitted && (
          <Button
            onClick={onResolve}
            variant="success"
            size="xs"
            className="shadow-[0_0_0_1px_rgb(34_197_94/0.25),0_8px_20px_rgb(34_197_94/0.15)] hover:-translate-y-px hover:bg-green-500 transition-all"
          >
            Resolve Turn
          </Button>
        )}

        <Button
          onClick={onSubmit}
          disabled={!isDirty && submitted}
          size="xs"
          className={`font-semibold transition-all duration-200 ${
            isDirty
              ? "bg-[var(--color-player-self)] text-white shadow-[0_0_0_1px_rgb(147_197_253/0.25),0_8px_20px_rgb(96_165_250/0.25)] hover:-translate-y-px hover:bg-[var(--color-player-self)]/85"
              : submitted
                ? "bg-secondary text-muted-foreground cursor-default"
                : "bg-[var(--color-player-self)]/60 text-white/80 hover:bg-[var(--color-player-self)] hover:text-white"
          }`}
        >
          {submitted && !isDirty ? "Submitted ✓" : "Submit Turn"}
        </Button>
        <Button
          onClick={onLeave}
          variant="ghost"
          size="xs"
          title="Back to lobby"
        >
          Lobby
        </Button>
      </div>
    </header>
  );
}
