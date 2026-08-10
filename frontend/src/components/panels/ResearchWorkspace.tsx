import { useMemo, useState } from "react";
import {
  RESEARCH_FIELDS,
  RESEARCH_FIELD_COLOURS,
  RESEARCH_FIELD_LABELS,
  RESEARCH_MAX_LEVEL,
  type ResearchField,
} from "../../lib/research";
import type { PlayerStateResearch, SetResearchCommand } from "../../types";
import { Button } from "../ui/Button";
import { MutedText } from "../ui/MutedText";
import { StatusBadge } from "../ui/StatusBadge";

type Props = {
  research: PlayerStateResearch;
  ownedPlanetsLeftoverOnlyCount: number;
  ownedPlanetsCount: number;
  pendingCommand: SetResearchCommand | null;
  onChange: (cmd: SetResearchCommand | null) => void;
};

type LocalState = {
  currentField: ResearchField;
  nextField: ResearchField | null;
  allocationPercent: number;
};

function clampPct(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function buildCommand(local: LocalState, committed: LocalState): SetResearchCommand | null {
  const cmd: SetResearchCommand = { type: "set_research" };
  if (local.currentField !== committed.currentField) cmd.currentField = local.currentField;
  if (local.nextField !== committed.nextField) cmd.nextField = local.nextField;
  if (local.allocationPercent !== committed.allocationPercent) cmd.allocationPercent = local.allocationPercent;

  return Object.keys(cmd).length === 1 ? null : cmd;
}

export function ResearchWorkspace({
  research,
  ownedPlanetsLeftoverOnlyCount,
  ownedPlanetsCount,
  pendingCommand,
  onChange,
}: Props) {
  const committed = useMemo<LocalState>(() => ({
    currentField: research.currentField,
    nextField: research.nextField,
    allocationPercent: research.allocationPercent,
  }), [research]);

  const seeded = useMemo<LocalState>(() => ({
    currentField: pendingCommand?.currentField ?? committed.currentField,
    nextField: pendingCommand?.nextField !== undefined ? pendingCommand.nextField : committed.nextField,
    allocationPercent: pendingCommand?.allocationPercent ?? committed.allocationPercent,
  }), [pendingCommand, committed]);

  const [local, setLocal] = useState<LocalState>(seeded);
  const [allocationInput, setAllocationInput] = useState(String(seeded.allocationPercent));

  const [seededForLocal, setSeededForLocal] = useState(seeded);
  if (seeded !== seededForLocal) {
    setSeededForLocal(seeded);
    setLocal(seeded);
    setAllocationInput(String(seeded.allocationPercent));
  }

  const scaledReservable = Math.floor((research.reservableResourcesThisTurn * local.allocationPercent) / 100);
  const localLevel = research.levels[local.currentField];
  const localCost = research.progress[local.currentField] + research.remainingCost[local.currentField];

  const updateLocal = (next: LocalState) => {
    setLocal(next);
    onChange(buildCommand(next, committed));
  };

  const setAllocationPercent = (value: number) => {
    const clamped = clampPct(value);
    updateLocal({ ...local, allocationPercent: clamped });
    setAllocationInput(String(clamped));
  };

  return (
    <div className="flex h-full justify-center overflow-hidden p-4">
      <section className="panel-surface flex h-full w-full max-w-5xl min-w-0 flex-col overflow-y-auto rounded-md border border-[var(--color-panel-border)] p-4">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-foreground">Research</h2>
        </div>

        <div className="mb-3 grid gap-3 md:grid-cols-3">
          <label className="text-sm">Resource Allocation
            <div className="mt-1 flex w-fit items-center rounded-md border border-[var(--color-panel-border)] bg-background/60">
              <Button
                variant="ghost"
                size="xs"
                onClick={() => setAllocationPercent(local.allocationPercent - 1)}
                aria-label="Decrease allocation"
              >
                -
              </Button>
              <input
                aria-label="Allocation percent"
                type="number"
                min={0}
                max={100}
                value={allocationInput}
                className="w-14 bg-transparent px-2 py-1 text-right text-sm text-foreground"
                onChange={(e) => setAllocationInput(e.target.value)}
                onBlur={() => setAllocationPercent(Number(allocationInput))}
              />
              <MutedText className="pr-2 text-sm">%</MutedText>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => setAllocationPercent(local.allocationPercent + 1)}
                aria-label="Increase allocation"
              >
                +
              </Button>
            </div>
          </label>
          <label className="text-sm">Current field
            <select
              aria-label="Current field"
              value={local.currentField}
              className="mt-1 w-full rounded-md border border-[var(--color-panel-border)] bg-background/60 px-3 py-2 text-sm text-foreground"
              onChange={(e) => updateLocal({ ...local, currentField: e.target.value as ResearchField })}
            >
              {RESEARCH_FIELDS.map((field) => (
                <option key={field} value={field} disabled={research.levels[field] === RESEARCH_MAX_LEVEL}>{RESEARCH_FIELD_LABELS[field]}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">Next field
            <select
              aria-label="Next field"
              value={local.nextField ?? ""}
              className="mt-1 w-full rounded-md border border-[var(--color-panel-border)] bg-background/60 px-3 py-2 text-sm text-foreground"
              onChange={(e) => updateLocal({ ...local, nextField: e.target.value ? (e.target.value as ResearchField) : null })}
            >
              <option value="">(none)</option>
              {RESEARCH_FIELDS.map((field) => (
                <option key={field} value={field}>{RESEARCH_FIELD_LABELS[field]}</option>
              ))}
            </select>
          </label>
        </div>
        {local.currentField === local.nextField && local.nextField !== null && (
          <p className="mb-2 text-xs text-amber-300">Same as current — next field will reset to none on apply.</p>
        )}

        <div className="mb-4 space-y-1">
          {RESEARCH_FIELDS.map((field) => {
            const level = research.levels[field];
            const isMax = level === RESEARCH_MAX_LEVEL;
            const cost = research.progress[field] + research.remainingCost[field];
            const pct = cost === 0 ? 0 : Math.floor((100 * research.progress[field]) / cost);
            const isCurrent = local.currentField === field;
            const isQueued = local.nextField === field;
            return (
              <button
                key={field}
                data-testid={`research-row-${field}`}
                disabled={isMax}
                onClick={() => !isMax && updateLocal({ ...local, currentField: field })}
                className="grid w-full grid-cols-[8rem_4.5rem_minmax(0,1fr)_6rem_7rem] items-center gap-2 rounded border border-[var(--color-panel-border)] px-2 py-1 text-left disabled:opacity-50"
              >
                <span style={{ color: RESEARCH_FIELD_COLOURS[field] }} className="truncate">{RESEARCH_FIELD_LABELS[field]}</span>
                <StatusBadge className="w-fit" style={{ color: RESEARCH_FIELD_COLOURS[field] }}>
                  {level}
                </StatusBadge>
                {isMax ? (
                  <>
                    <span className="h-2" />
                    <span className="font-semibold">MAX</span>
                  </>
                ) : (
                  <>
                    <div className="h-2 flex-1 rounded bg-secondary">
                      <div className="h-2 rounded bg-[var(--color-player-self)]" style={{ width: `${pct}%` }} />
                    </div>
                    <span>{research.progress[field]} / {cost}</span>
                  </>
                )}
                <span data-testid={`research-marker-${field}`}>{isCurrent ? "● current" : isQueued ? "○ next" : "▷"}</span>
              </button>
            );
          })}
        </div>

        <div className="mb-4 text-sm">
          <p>
            Reserved this turn:{" "}
            {research.reservableResourcesThisTurn === 0
              ? "— (no reservable resources)"
              : `≈ ${Math.floor((research.reservableResourcesThisTurn * local.allocationPercent) / 100)} resources`}
          </p>
          {localLevel === RESEARCH_MAX_LEVEL ? (
            <p>Cost to next level: — (maxed)</p>
          ) : (
            <>
              <p>Cost to next level ({RESEARCH_FIELD_LABELS[local.currentField]}): {localCost} resources</p>
              <p>
                Estimated completion: {scaledReservable === 0 ? "— (no research income)" : `≈ ${Math.ceil(research.remainingCost[local.currentField] / scaledReservable)} turns`}
              </p>
            </>
          )}
          {ownedPlanetsLeftoverOnlyCount > 0 && (
            <MutedText as="p" className="text-xs">{ownedPlanetsLeftoverOnlyCount} of {ownedPlanetsCount} planets set to leftover-only</MutedText>
          )}
        </div>

      </section>
    </div>
  );
}
