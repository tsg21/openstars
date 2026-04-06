/**
 * Standalone Altair combat replay page.
 *
 * Accepts a CombatLog via:
 *   - JSON textarea paste
 *   - File upload
 *   - POST to the prototype simulate endpoint
 *
 * Controls: play/pause, step forward/back, jump to round, speed slider.
 */

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { keysToCamel } from "../lib/caseConvert";
import { ArenaView } from "./ArenaView";
import { buildFrames, findRoundBoundaries, type InitialToken } from "./replayReducer";
import type { CombatLog } from "./types";

const DEFAULT_FIXTURE = JSON.stringify(
  {
    tokens: [
      {
        id: "a1",
        owner: "alice",
        position: { x: 1000, y: 5000 },
        hp: 100,
        movement_quarters: 4,
        weapon_damage: 20,
        weapon_range_classic: 2,
      },
      {
        id: "b1",
        owner: "bob",
        position: { x: 9000, y: 5000 },
        hp: 100,
        movement_quarters: 4,
        weapon_damage: 20,
        weapon_range_classic: 2,
      },
    ],
    config: { S: 1000, T: 20, N_rounds: 16 },
  },
  null,
  2,
);

/** Extract initial token state from a CombatLog's first frame. */
function extractInitialTokens(log: CombatLog): InitialToken[] {
  const tokenMap = new Map<string, InitialToken>();
  for (const evt of log.events) {
    if (evt.type === "token_moved") {
      if (!tokenMap.has(evt.tokenId)) {
        tokenMap.set(evt.tokenId, {
          id: evt.tokenId,
          owner: "",
          x: evt.fromPos.x,
          y: evt.fromPos.y,
          hp: 100,
        });
      }
    }
  }
  return Array.from(tokenMap.values());
}

/** Try to parse snapshot JSON to recover initial token data. */
function extractTokensFromSnapshot(snapshotJson: string): InitialToken[] | null {
  try {
    const raw = JSON.parse(snapshotJson);
    const snap = keysToCamel(raw) as Record<string, unknown>;
    const tokens = snap.tokens as Array<Record<string, unknown>>;
    if (!Array.isArray(tokens)) return null;
    return tokens.map((t) => ({
      id: String(t.id),
      owner: String(t.owner),
      x: (t.position as { x: number }).x,
      y: (t.position as { y: number }).y,
      hp: typeof t.hp === "number" ? t.hp : 100,
    }));
  } catch {
    return null;
  }
}

export function CombatReplayPage() {
  const [jsonInput, setJsonInput] = useState("");
  const [snapshotInput, setSnapshotInput] = useState(DEFAULT_FIXTURE);
  const [log, setLog] = useState<CombatLog | null>(null);
  const [initialTokens, setInitialTokens] = useState<InitialToken[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(100);
  const [simulating, setSimulating] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const frames = useMemo(
    () => (log ? buildFrames(log, initialTokens) : []),
    [log, initialTokens],
  );

  const roundBoundaries = useMemo(
    () => (log ? findRoundBoundaries(log) : []),
    [log],
  );

  const maxFrame = frames.length - 1;

  // Playback timer
  useEffect(() => {
    if (playing && maxFrame > 0) {
      intervalRef.current = setInterval(() => {
        setFrameIndex((prev) => {
          if (prev >= maxFrame) {
            setPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, speed, maxFrame]);

  const loadLogJson = useCallback(
    (raw: string, snapshotJson?: string) => {
      try {
        const parsed = JSON.parse(raw);
        const converted = keysToCamel(parsed) as CombatLog;
        if (!converted.events || !Array.isArray(converted.events)) {
          throw new Error("Invalid CombatLog: missing events array");
        }
        setLog(converted);

        // Try to get initial tokens from the snapshot, fall back to log analysis
        const fromSnap = snapshotJson
          ? extractTokensFromSnapshot(snapshotJson)
          : null;
        setInitialTokens(fromSnap ?? extractInitialTokens(converted));

        setFrameIndex(0);
        setPlaying(false);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to parse JSON");
      }
    },
    [],
  );

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        const text = reader.result as string;
        setJsonInput(text);
        loadLogJson(text);
      };
      reader.readAsText(file);
    },
    [loadLogJson],
  );

  const handleSimulate = useCallback(async () => {
    setSimulating(true);
    setError(null);
    try {
      const resp = await fetch("/api/v1/combat-altair-prototype/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: snapshotInput,
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${text}`);
      }
      const data = await resp.text();
      setJsonInput(data);
      loadLogJson(data, snapshotInput);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setSimulating(false);
    }
  }, [snapshotInput, loadLogJson]);

  const jumpToRound = useCallback(
    (direction: "prev" | "next") => {
      const current = frameIndex;
      if (direction === "next") {
        const next = roundBoundaries.find((b) => b > current);
        if (next !== undefined) setFrameIndex(Math.min(next, maxFrame));
      } else {
        const prev = [...roundBoundaries].reverse().find((b) => b < current);
        if (prev !== undefined) setFrameIndex(prev);
      }
    },
    [frameIndex, roundBoundaries, maxFrame],
  );

  const currentFrame = frames[frameIndex] ?? null;

  return (
    <div className="flex h-screen flex-col bg-[#0f172a] text-[#e2e8f0]">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-[#1e293b] px-4 py-2">
        <h1 className="text-lg font-semibold tracking-tight">
          Altair Combat Prototype
        </h1>
        <a
          href="/"
          className="text-sm text-[#94a3b8] hover:text-white transition-colors"
        >
          Back to game
        </a>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left panel: input */}
        <div className="flex w-80 flex-col gap-3 overflow-y-auto border-r border-[#1e293b] p-3">
          <section>
            <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-[#94a3b8]">
              Simulate
            </h2>
            <textarea
              value={snapshotInput}
              onChange={(e) => setSnapshotInput(e.target.value)}
              className="h-40 w-full rounded border border-[#334155] bg-[#1e293b] p-2 font-mono text-xs text-[#e2e8f0] focus:border-[#60a5fa] focus:outline-none"
              placeholder="Paste BattleSnapshot JSON…"
            />
            <button
              onClick={handleSimulate}
              disabled={simulating}
              className="mt-1 w-full rounded bg-[#3b82f6] px-3 py-1.5 text-sm font-medium text-white hover:bg-[#2563eb] disabled:opacity-50 transition-colors"
            >
              {simulating ? "Simulating…" : "Run simulation"}
            </button>
          </section>

          <div className="border-t border-[#1e293b] pt-2">
            <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-[#94a3b8]">
              Or load log JSON
            </h2>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              className="h-32 w-full rounded border border-[#334155] bg-[#1e293b] p-2 font-mono text-xs text-[#e2e8f0] focus:border-[#60a5fa] focus:outline-none"
              placeholder="Paste CombatLog JSON…"
            />
            <div className="mt-1 flex gap-2">
              <button
                onClick={() => loadLogJson(jsonInput)}
                className="flex-1 rounded bg-[#334155] px-3 py-1.5 text-sm font-medium text-[#e2e8f0] hover:bg-[#475569] transition-colors"
              >
                Load JSON
              </button>
              <label className="flex-1 cursor-pointer rounded bg-[#334155] px-3 py-1.5 text-center text-sm font-medium text-[#e2e8f0] hover:bg-[#475569] transition-colors">
                Upload file
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          {error && (
            <p className="rounded bg-red-900/30 p-2 text-xs text-red-400">{error}</p>
          )}

          {currentFrame && (
            <section className="border-t border-[#1e293b] pt-2">
              <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-[#94a3b8]">
                Status
              </h2>
              <div className="space-y-0.5 font-mono text-xs text-[#cbd5e1]">
                <p>Round: {currentFrame.roundIndex}</p>
                <p>Tick: {currentFrame.tickIndex}</p>
                <p>
                  Frame: {frameIndex} / {maxFrame}
                </p>
                <div className="mt-1 space-y-0.5">
                  {currentFrame.tokens.map((t) => (
                    <p
                      key={t.id}
                      className={t.alive ? "" : "line-through opacity-50"}
                    >
                      {t.id} ({t.owner}): ({t.x}, {t.y}) {t.hp}hp
                    </p>
                  ))}
                </div>
              </div>
            </section>
          )}
        </div>

        {/* Centre: arena */}
        <div className="flex flex-1 flex-col">
          <div className="flex-1 overflow-hidden p-4">
            {currentFrame && log ? (
              <ArenaView
                frame={currentFrame}
                arenaSize={log.config.S * 10}
                className="h-full w-full"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-[#475569]">
                <p>Run a simulation or load a combat log to begin.</p>
              </div>
            )}
          </div>

          {/* Controls bar */}
          {frames.length > 0 && (
            <div className="flex items-center gap-3 border-t border-[#1e293b] px-4 py-2">
              <button
                onClick={() => jumpToRound("prev")}
                className="rounded bg-[#334155] px-2 py-1 text-xs font-medium hover:bg-[#475569] transition-colors"
                title="Previous round"
              >
                ⏮
              </button>
              <button
                onClick={() => setFrameIndex((i) => Math.max(0, i - 1))}
                className="rounded bg-[#334155] px-2 py-1 text-xs font-medium hover:bg-[#475569] transition-colors"
                title="Step back"
              >
                ◀
              </button>
              <button
                onClick={() => setPlaying((p) => !p)}
                className="rounded bg-[#3b82f6] px-3 py-1 text-xs font-medium text-white hover:bg-[#2563eb] transition-colors"
              >
                {playing ? "⏸ Pause" : "▶ Play"}
              </button>
              <button
                onClick={() => setFrameIndex((i) => Math.min(maxFrame, i + 1))}
                className="rounded bg-[#334155] px-2 py-1 text-xs font-medium hover:bg-[#475569] transition-colors"
                title="Step forward"
              >
                ▶
              </button>
              <button
                onClick={() => jumpToRound("next")}
                className="rounded bg-[#334155] px-2 py-1 text-xs font-medium hover:bg-[#475569] transition-colors"
                title="Next round"
              >
                ⏭
              </button>

              <input
                type="range"
                min={0}
                max={maxFrame}
                value={frameIndex}
                onChange={(e) => setFrameIndex(Number(e.target.value))}
                className="mx-2 flex-1"
              />

              <label className="flex items-center gap-1 text-xs text-[#94a3b8]">
                Speed
                <input
                  type="range"
                  min={10}
                  max={500}
                  step={10}
                  value={510 - speed}
                  onChange={(e) => setSpeed(510 - Number(e.target.value))}
                  className="w-20"
                />
              </label>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
