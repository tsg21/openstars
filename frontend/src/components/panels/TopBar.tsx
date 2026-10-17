import type { PlayerStateResearch } from "../../types";
import { Button } from "../ui/Button";
import { MutedText } from "../ui/MutedText";

interface TopBarProps {
  gameName: string;
  turn: number;
  waitingForNextTurn: boolean;
  mode: "command" | "production" | "designer" | "research";
  onModeChange: (mode: "command" | "production" | "designer" | "research") => void;
  raceSelectionActive?: boolean;
  productionEnabled?: boolean;
  onSubmit: () => void;
  submissionStatus: string;
  onLeave: () => void;
  onSignOut: () => void;
  playerName: string;
  error: string | null;
  research: PlayerStateResearch | null;
}

export function TopBar({
  gameName,
  turn,
  waitingForNextTurn,
  mode,
  onModeChange,
  raceSelectionActive = false,
  productionEnabled = true,
  onSubmit,
  submissionStatus,
  onLeave,
  onSignOut,
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
          {raceSelectionActive ? (
            <Button
              variant="primary"
              size="xs"
              onClick={() => undefined}
            >
              Race Selection
            </Button>
          ) : (
            <>
              <Button
                variant={mode === "command" ? "primary" : "ghost"}
                size="xs"
                onClick={() => onModeChange("command")}
              >
                Command
              </Button>
              <Button
                variant={mode === "production" ? "primary" : "ghost"}
                size="xs"
                disabled={!productionEnabled}
                title={!productionEnabled ? "No owned planets yet" : undefined}
                onClick={() => { if (productionEnabled) onModeChange("production"); }}
              >
                Production
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
            </>
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

        <Button
          onClick={onSubmit}
          size="xs"
          className="font-semibold bg-[var(--color-player-self)] text-white shadow-[0_0_0_1px_rgb(147_197_253/0.25),0_8px_20px_rgb(96_165_250/0.25)] hover:-translate-y-px hover:bg-[var(--color-player-self)]/85 transition-all duration-200"
        >
          Submit Turn
        </Button>
        <Button
          onClick={onLeave}
          variant="ghost"
          size="xs"
          title="Back to lobby"
        >
          Lobby
        </Button>
        <Button
          onClick={onSignOut}
          variant="ghost"
          size="xs"
          title="Sign out"
        >
          Sign out
        </Button>
      </div>
    </header>
  );
}
