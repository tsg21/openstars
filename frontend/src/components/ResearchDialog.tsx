import { useEffect, useMemo, useState } from "react";
import {
  RESEARCH_FIELDS,
  RESEARCH_FIELD_COLOURS,
  RESEARCH_FIELD_LABELS,
  RESEARCH_MAX_LEVEL,
  type ResearchField,
} from "../lib/research";
import type { PlayerStateResearch, SetResearchCommand } from "../types";
import { Button } from "./Button";

type Props = {
  open: boolean;
  onClose: () => void;
  research: PlayerStateResearch;
  ownedPlanetsLeftoverOnlyCount: number;
  ownedPlanetsCount: number;
  pendingCommand: SetResearchCommand | null;
  onApply: (cmd: SetResearchCommand | null) => void;
};

type LocalState = {
  currentField: ResearchField;
  nextField: ResearchField | null;
  allocationPercent: number;
};

function clampPct(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function sameState(a: LocalState, b: LocalState): boolean {
  return a.currentField === b.currentField && a.nextField === b.nextField && a.allocationPercent === b.allocationPercent;
}

export function ResearchDialog({
  open,
  onClose,
  research,
  ownedPlanetsLeftoverOnlyCount,
  ownedPlanetsCount,
  pendingCommand,
  onApply,
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

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const isDirty = !sameState(local, committed);
  const scaledReservable = Math.floor((research.reservableResourcesThisTurn * local.allocationPercent) / 100);
  const localLevel = research.levels[local.currentField];
  const localCost = research.progress[local.currentField] + research.remainingCost[local.currentField];

  const apply = () => {
    const cmd: SetResearchCommand = { type: "set_research" };
    if (local.currentField !== committed.currentField) cmd.currentField = local.currentField;
    if (local.nextField !== committed.nextField) cmd.nextField = local.nextField;
    if (local.allocationPercent !== committed.allocationPercent) cmd.allocationPercent = local.allocationPercent;

    if (Object.keys(cmd).length === 1) {
      onApply(null);
    } else {
      onApply(cmd);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
      <button className="absolute inset-0 bg-black/60" aria-label="Close research dialog" onClick={onClose} />
      <div className="panel-surface relative z-10 w-full max-w-3xl rounded-lg border border-[var(--color-panel-border)] p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Research</h2>
          <Button variant="ghost" size="xs" onClick={onClose}>✕</Button>
        </div>

        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <label className="text-sm">Allocation
            <input type="range" min={0} max={100} step={1} value={local.allocationPercent}
              onChange={(e) => {
                const value = Number(e.target.value);
                setLocal((prev) => ({ ...prev, allocationPercent: value }));
                setAllocationInput(String(value));
              }}
            />
          </label>
          <label className="text-sm">Percent
            <input aria-label="Allocation percent" type="number" min={0} max={100} value={allocationInput}
              onChange={(e) => setAllocationInput(e.target.value)}
              onBlur={() => {
                const value = clampPct(Number(allocationInput));
                setLocal((prev) => ({ ...prev, allocationPercent: value }));
                setAllocationInput(String(value));
              }}
            />
          </label>
          <div className="text-sm self-end">
            {research.reservableResourcesThisTurn === 0
              ? "— (no reservable resources)"
              : `≈ ${Math.floor((research.reservableResourcesThisTurn * local.allocationPercent) / 100)} resources this turn`}
          </div>
        </div>

        <div className="mb-3 grid gap-3 md:grid-cols-2">
          <label className="text-sm">Current field
            <select aria-label="Current field" value={local.currentField} onChange={(e) => setLocal((prev) => ({ ...prev, currentField: e.target.value as ResearchField }))}>
              {RESEARCH_FIELDS.map((field) => (
                <option key={field} value={field} disabled={research.levels[field] === RESEARCH_MAX_LEVEL}>{RESEARCH_FIELD_LABELS[field]}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">Next field
            <select aria-label="Next field" value={local.nextField ?? ""} onChange={(e) => setLocal((prev) => ({ ...prev, nextField: e.target.value ? (e.target.value as ResearchField) : null }))}>
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
                onClick={() => !isMax && setLocal((prev) => ({ ...prev, currentField: field }))}
                className="flex w-full items-center gap-2 rounded border border-[var(--color-panel-border)] px-2 py-1 text-left disabled:opacity-50"
              >
                <span style={{ color: RESEARCH_FIELD_COLOURS[field] }} className="w-28">{RESEARCH_FIELD_LABELS[field]}</span>
                {isMax ? (
                  <span>lvl {level} · MAX</span>
                ) : (
                  <>
                    <div className="h-2 flex-1 rounded bg-secondary">
                      <div className="h-2 rounded bg-[var(--color-player-self)]" style={{ width: `${pct}%` }} />
                    </div>
                    <span>lvl {level}</span>
                    <span>{research.progress[field]} / {cost}</span>
                  </>
                )}
                <span data-testid={`research-marker-${field}`}>{isCurrent ? "● current" : isQueued ? "○ queued next" : "▷"}</span>
              </button>
            );
          })}
        </div>

        <div className="mb-4 text-sm">
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
            <p className="text-xs text-muted-foreground">{ownedPlanetsLeftoverOnlyCount} of {ownedPlanetsCount} planets set to leftover-only</p>
          )}
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={apply} disabled={!isDirty}>Apply</Button>
        </div>
      </div>
    </div>
  );
}
