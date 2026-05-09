import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  ApiError,
  getPredefinedRaces,
  getRace,
  previewRace,
} from "../api/client";
import {
  DEFAULT_RACE,
  HAB_DISPLAY,
  type Race,
  type RaceCostBreakdown,
  type RaceEconomy,
  type RaceHabitability,
  type RaceResearch,
  type Lrt,
  type ResearchCostProfile,
  type SelectRaceCommand,
} from "../types";
import {
  RESEARCH_FIELD_COLOURS,
  RESEARCH_FIELD_LABELS,
  RESEARCH_FIELDS,
  type ResearchField,
} from "../lib/research";
import { Button } from "./Button";
import { FormField, TextInput } from "./FormField";
import { MutedText } from "./MutedText";
import { PanelCard } from "./PanelCard";
import { useGameCommands } from "../hooks/useGameCommands";

type Props = {
  gameId: string;
  player: string;
};

type HabKey = keyof RaceHabitability;
type EconomyNumberKey = Exclude<{
  [K in keyof RaceEconomy]: RaceEconomy[K] extends number ? K : never;
}[keyof RaceEconomy], undefined>;

const BREAKDOWN_LABELS: Array<[keyof RaceCostBreakdown, string]> = [
  ["prt", "Primary trait"],
  ["lrts", "Lesser traits"],
  ["habitability", "Habitability"],
  ["growth", "Growth"],
  ["economy", "Economy"],
  ["research", "Research"],
  ["leftover", "Leftover bonus"],
  ["total", "Total"],
];

const LOCKED_PRTS = [
  {
    abbr: "SS",
    name: "Super Stealth",
    desc: "Mastery of cloaking and intelligence-gathering.",
    effects: ["+ Native cloaking", "+ Spy tech advantages", "- Scanner limitations"],
  },
  {
    abbr: "WM",
    name: "War Monger",
    desc: "Born for combat, with weapons research and ship handling advantages.",
    effects: ["+ Weapons advantages", "+ Extra initiative", "- Diplomacy penalty"],
  },
  {
    abbr: "CA",
    name: "Claim Adjuster",
    desc: "Can terraform hostile worlds toward their preferred biology.",
    effects: ["+ Full terraforming", "+ Hostile starts viable", "- Terraforming trade-offs"],
  },
  {
    abbr: "IS",
    name: "Inner Strength",
    desc: "Resilient and self-sufficient, with durable ships and colonies.",
    effects: ["+ Armour advantages", "+ Shield resilience", "- Fewer direct economic tricks"],
  },
  {
    abbr: "SD",
    name: "Space Demolition",
    desc: "Masters of mine warfare and territorial denial.",
    effects: ["+ Minefield control", "+ Mine immunity", "- Weaker direct weapons"],
  },
  {
    abbr: "PP",
    name: "Packet Physics",
    desc: "Specialists in mineral packet attacks and remote industry pressure.",
    effects: ["+ Packet attacks", "+ Long-range pressure", "- Narrower strategic profile"],
  },
  {
    abbr: "IT",
    name: "Interstellar Traveller",
    desc: "Gate-focused empire builders with unusual mobility options.",
    effects: ["+ Gate mobility", "+ Flexible logistics", "- Gate dependency"],
  },
  {
    abbr: "AR",
    name: "Alternate Reality",
    desc: "Orbital civilisation that draws resources from starbases rather than planetary industry.",
    effects: ["+ Starbase economy", "+ Distinct colony model", "- No normal factories"],
  },
] as const;

const AVAILABLE_LRTS = [
  ["IFE", "Improved Fuel Efficiency", "Fuel consumption -15%; unlocks Fuel Mizer and adds starting Propulsion."],
] as const satisfies ReadonlyArray<readonly [Lrt, string, string]>;

const LOCKED_LRTS = [
  ["TT", "Total Terraforming", "Unlocks wider terraforming steps and reduces terraforming cost."],
  ["ARM", "Advanced Remote Mining", "Unlocks advanced mining hulls and robots; starting fleet gains Midget Miners."],
  ["ISB", "Improved Starbases", "Unlocks extra starbase hulls, auto-cloaks starbases, and reduces starbase cost."],
  ["GR", "Generalised Research", "Research is split between the current field and every other field."],
  ["UR", "Ultimate Recycling", "Scrapping recovers far more minerals and resources."],
  ["MA", "Mineral Alchemy", "Resource-to-mineral conversion is four times more efficient."],
  ["NRSE", "No Ramscoop Engines", "Forbids most ramscoop engines and unlocks Interspace-10."],
  ["CE", "Cheap Engines", "Engines cost half as much, but high warp travel can fail to engage."],
  ["OBRM", "Only Basic Remote Mining", "Limits remote mining hardware and increases planet population caps."],
  ["NAS", "No Advanced Scanners", "Forbids most penetrating scanners, but doubles normal scanner ranges."],
  ["LSP", "Low Starting Population", "Homeworld starts with reduced population."],
  ["BET", "Bleeding Edge Technology", "New tech costs more until prerequisites are exceeded; miniaturisation improves."],
  ["RS", "Regenerating Shields", "Shields are stronger and regenerate; armour is weaker."],
] as const;

const ECONOMY_FIELDS: Array<{
  key: EconomyNumberKey;
  label: string;
  min: number;
  max: number;
}> = [
  { key: "colonistsPerResource", label: "Colonists per resource", min: 700, max: 2500 },
  { key: "factoryOutputPer10", label: "Factory output per 10", min: 5, max: 15 },
  { key: "factoryCostResources", label: "Factory cost", min: 5, max: 25 },
  { key: "factoriesPer10kColonists", label: "Factories per 10k colonists", min: 5, max: 25 },
  { key: "mineOutputPer10", label: "Mine output per 10", min: 5, max: 25 },
  { key: "mineCostResources", label: "Mine cost", min: 2, max: 15 },
  { key: "minesPer10kColonists", label: "Mines per 10k colonists", min: 5, max: 25 },
  { key: "arResourceDivisor", label: "AR resource divisor", min: 5, max: 25 },
];

function cloneRace(race: Race): Race {
  return {
    ...race,
    lrts: [...race.lrts],
    habitability: {
      gravity: { ...race.habitability.gravity, range: [...race.habitability.gravity.range] },
      temperature: { ...race.habitability.temperature, range: [...race.habitability.temperature.range] },
      radiation: { ...race.habitability.radiation, range: [...race.habitability.radiation.range] },
    },
    economy: { ...race.economy },
    research: {
      fieldProfile: { ...race.research.fieldProfile },
      startAtTech3: race.research.startAtTech3,
    },
    leftoverBonus: race.leftoverBonus ? { ...race.leftoverBonus } : null,
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Number.isFinite(value) ? value : min));
}

function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.code}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong";
}

function SectionHead({ children }: { children: ReactNode }) {
  return (
    <div className="mb-3 flex items-center gap-2.5">
      <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
        {children}
      </span>
      <div className="h-px flex-1 bg-[var(--color-panel-border)]" />
    </div>
  );
}

function BudgetBar({ pointsLeft }: { pointsLeft: number | null }) {
  const budget = 1650;
  const value = pointsLeft ?? 0;
  const pct = Math.max(0, Math.min(100, (value / budget) * 100));
  const over = value < 0;
  const warn = value < 200 && !over;
  const color = over
    ? "var(--color-status-danger)"
    : warn
      ? "var(--color-status-warning)"
      : "var(--color-player-self)";

  return (
    <div className="flex min-w-[210px] items-center gap-2.5 rounded border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] px-3 py-1.5">
      <MutedText className="whitespace-nowrap text-xs">Race Points</MutedText>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-[var(--color-surface-3)]">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="min-w-[52px] text-right font-mono text-xs font-semibold" style={{ color }}>
        {pointsLeft === null ? "--" : `${value > 0 ? "+" : ""}${value}`}
      </span>
    </div>
  );
}

function SidebarRow({ k, v, vColor }: { k: string; v: string; vColor?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-0.5">
      <span className="text-[10px] text-muted-foreground">{k}</span>
      <span className="truncate text-right font-mono text-[10px]" style={vColor ? { color: vColor } : undefined}>
        {v}
      </span>
    </div>
  );
}

function SidebarGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mb-4">
      <p className="mb-2 border-b border-[var(--color-panel-border)] pb-1 text-[10px] uppercase tracking-widest text-muted-foreground">
        {title}
      </p>
      {children}
    </div>
  );
}

function HabRangeRow({
  label,
  color,
  dim,
  factor,
  onImmuneChange,
  onLowChange,
  onHighChange,
}: {
  label: string;
  color: string;
  dim: HabKey;
  factor: Race["habitability"][HabKey];
  onImmuneChange: (immune: boolean) => void;
  onLowChange: (value: number) => void;
  onHighChange: (value: number) => void;
}) {
  const [low, high] = factor.range;
  const width = high - low;

  return (
    <div className="grid items-center gap-2.5 border-b border-[var(--color-panel-border)] py-2 last:border-b-0 md:grid-cols-[98px_70px_1fr_78px_78px]">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ background: color }} />
        {label}
      </div>
      <label className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
        <input
          type="checkbox"
          checked={factor.immune}
          onChange={(event) => onImmuneChange(event.target.checked)}
        />
        Immune
      </label>
      <div className="relative flex h-6 items-center">
        <div className="absolute inset-x-0 h-1 rounded-sm bg-[var(--color-surface-3)]" />
        <div
          className="absolute h-1 rounded-sm opacity-70"
          style={{ left: `${low}%`, width: `${width}%`, background: color }}
        />
        <input
          aria-label={`${dim} low`}
          type="range"
          min={0}
          max={100}
          disabled={factor.immune}
          value={low}
          className="absolute inset-x-0 h-6 w-full cursor-ew-resize opacity-0 disabled:cursor-not-allowed"
          onChange={(event) => onLowChange(clamp(Number(event.target.value), 0, high))}
        />
        <input
          aria-label={`${dim} high`}
          type="range"
          min={0}
          max={100}
          disabled={factor.immune}
          value={high}
          className="absolute inset-x-0 h-6 w-full cursor-ew-resize opacity-0 disabled:cursor-not-allowed"
          onChange={(event) => onHighChange(clamp(Number(event.target.value), low, 100))}
        />
        <span
          className="absolute z-10 h-3.5 w-3.5 rounded-full border-2 border-background"
          style={{ left: `${low}%`, transform: "translateX(-50%)", background: color }}
        />
        <span
          className="absolute z-10 h-3.5 w-3.5 rounded-full border-2 border-background"
          style={{ left: `${high}%`, transform: "translateX(-50%)", background: color }}
        />
      </div>
      <input
        aria-label={`${dim} low value`}
        type="number"
        min={0}
        max={100}
        disabled={factor.immune}
        value={low}
        className="h-[30px] rounded-md border border-[var(--color-panel-border)] bg-background px-2 text-center font-mono text-[10px] disabled:opacity-50"
        onChange={(event) => onLowChange(clamp(Number(event.target.value), 0, high))}
      />
      <input
        aria-label={`${dim} high value`}
        type="number"
        min={0}
        max={100}
        disabled={factor.immune}
        value={high}
        className="h-[30px] rounded-md border border-[var(--color-panel-border)] bg-background px-2 text-center font-mono text-[10px] disabled:opacity-50"
        onChange={(event) => onHighChange(clamp(Number(event.target.value), low, 100))}
      />
      <div className="md:col-start-3 md:col-span-3 -mt-1 text-[10px] text-muted-foreground">
        {factor.immune ? "Immune to this environmental dimension" : `${HAB_DISPLAY[dim](low)} to ${HAB_DISPLAY[dim](high)}`}
      </div>
    </div>
  );
}

export function RaceSelectionScreen({
  gameId,
  player,
}: Props) {
  const { replaceCommands } = useGameCommands();
  const [race, setRace] = useState<Race>(() => cloneRace(DEFAULT_RACE));
  const [lastSavedRace, setLastSavedRace] = useState<Race | null>(null);
  const [selectedPredefinedId, setSelectedPredefinedId] = useState<string | null>("humanoid");
  const [predefined, setPredefined] = useState<Array<{ id: string; race: Race }>>([]);
  const [costBreakdown, setCostBreakdown] = useState<RaceCostBreakdown | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const previewRequestId = useRef(0);

  useEffect(() => {
    let cancelled = false;

    async function loadRace() {
      setLoading(true);
      setSubmitError(null);
      try {
        const [predefinedRaces, saved] = await Promise.all([
          getPredefinedRaces(),
          getRace(gameId, player),
        ]);
        if (cancelled) return;

        setPredefined(predefinedRaces);
        const humanoid = predefinedRaces.find((candidate) => candidate.id === "humanoid")?.race ?? DEFAULT_RACE;
        const nextRace = saved.race ?? humanoid;
        setRace(cloneRace(nextRace));
        setLastSavedRace(saved.race ? cloneRace(saved.race) : null);
        setSelectedPredefinedId(saved.race ? null : "humanoid");
        setCostBreakdown(saved.costBreakdown);
      } catch (error) {
        if (!cancelled) {
          setSubmitError(formatApiError(error));
          setRace(cloneRace(DEFAULT_RACE));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadRace();
    return () => {
      cancelled = true;
    };
  }, [gameId, player]);

  useEffect(() => {
    const requestId = previewRequestId.current + 1;
    previewRequestId.current = requestId;

    const timeout = setTimeout(() => {
      void previewRace(race, player)
        .then((response) => {
          if (previewRequestId.current !== requestId) return;
          setCostBreakdown(response.costBreakdown);
          setPreviewError(null);
        })
        .catch((error) => {
          if (previewRequestId.current !== requestId) return;
          setCostBreakdown(null);
          setPreviewError(formatApiError(error));
        });
    }, 250);

    return () => clearTimeout(timeout);
  }, [player, race]);

  const setCustomRace = useCallback((updater: (current: Race) => Race) => {
    setSelectedPredefinedId(null);
    setSubmitError(null);
    setRace((current) => updater(cloneRace(current)));
  }, []);

  const updateHab = (key: HabKey, updater: (factor: Race["habitability"][HabKey]) => Race["habitability"][HabKey]) => {
    setCustomRace((current) => ({
      ...current,
      habitability: {
        ...current.habitability,
        [key]: updater(current.habitability[key]),
      },
    }));
  };

  const updateEconomy = (key: keyof RaceEconomy, value: RaceEconomy[keyof RaceEconomy]) => {
    setCustomRace((current) => ({
      ...current,
      economy: {
        ...current.economy,
        [key]: value,
      },
    }));
  };

  const updateResearch = (updater: (research: RaceResearch) => RaceResearch) => {
    setCustomRace((current) => ({
      ...current,
      research: updater(current.research),
    }));
  };

  const selectPreset = (id: string) => {
    const preset = predefined.find((candidate) => candidate.id === id);
    if (!preset) return;
    setRace(cloneRace(preset.race));
    setSelectedPredefinedId(id);
    setSubmitError(null);
  };

  const reset = () => {
    setRace(cloneRace(lastSavedRace ?? predefined.find((candidate) => candidate.id === "humanoid")?.race ?? DEFAULT_RACE));
    setSelectedPredefinedId(lastSavedRace ? null : "humanoid");
    setSubmitError(null);
  };

  const pointsLeft = costBreakdown?.pointsLeft ?? null;
  const canStageRace = race.name.trim().length > 0 && race.pluralName.trim().length > 0 && !previewError && (pointsLeft === null || pointsLeft >= 0);
  const habitableEstimate = useMemo(() => {
    const factors = [race.habitability.gravity, race.habitability.temperature, race.habitability.radiation];
    if (factors.some((factor) => factor.immune)) {
      return null;
    }
    return Math.round(
      factors.reduce((value, factor) => value * ((factor.range[1] - factor.range[0]) / 100), 1) * 100,
    );
  }, [race.habitability]);
  const validationMessages = [
    ...(race.name.trim() ? [] : ["Race name is required."]),
    ...(race.pluralName.trim() ? [] : ["Plural name is required."]),
    ...(pointsLeft !== null && pointsLeft < 0 ? [`Over budget by ${Math.abs(pointsLeft)} points.`] : []),
  ];

  useEffect(() => {
    if (!canStageRace) {
      replaceCommands({ kind: "race" }, []);
      return;
    }

    const command: SelectRaceCommand = selectedPredefinedId
      ? { type: "select_race", predefinedId: selectedPredefinedId }
      : { type: "select_race", race };
    replaceCommands({ kind: "race" }, [command]);
  }, [canStageRace, race, replaceCommands, selectedPredefinedId]);

  if (loading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading race designer...</p>
      </main>
    );
  }

  return (
    <main className="flex flex-1 overflow-hidden bg-background">
      <div className="flex min-h-0 flex-1 justify-center overflow-hidden">
        <section className="min-w-0 flex-1 overflow-y-auto p-6">
          <div className="mx-auto flex w-full max-w-[62rem] gap-6">
            <div className="min-w-0 flex-1">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <BudgetBar pointsLeft={pointsLeft} />
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="xs" onClick={reset}>Reset</Button>
            </div>
          </div>
          {submitError && (
            <p className="mb-4 max-w-3xl rounded-md border border-[var(--color-status-danger)]/40 bg-[var(--color-status-danger)]/10 px-3 py-2 text-sm text-[var(--color-status-danger)]">
              {submitError}
            </p>
          )}

          <section id="race-section-preset" className="mb-8">
            <SectionHead>Preset</SectionHead>
            <PanelCard className="p-4">
              <div className="grid gap-2 md:grid-cols-2">
                <button
                  type="button"
                  className={[
                    "rounded-md border p-3 text-left transition-colors",
                    selectedPredefinedId === "humanoid"
                      ? "border-[var(--color-player-self)] bg-[var(--color-player-self)]/10"
                      : "border-[var(--color-panel-border)] bg-[var(--color-surface-2)] hover:border-[var(--color-ring)]/50",
                  ].join(" ")}
                  onClick={() => selectPreset("humanoid")}
                >
                  <div className="mb-1 flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold">Humanoid</span>
                    <span className="rounded border border-[var(--color-panel-border)] px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">JOAT</span>
                  </div>
                  <p className="text-[11px] leading-snug text-muted-foreground">
                    Baseline Jack of All Trades race with standard economy, broad habitability, and standard research.
                  </p>
                </button>
                <div className="rounded-md border border-dashed border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3 opacity-50">
                  <div className="mb-1 flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold">Insectoid</span>
                    <span className="rounded border border-[var(--color-panel-border)] px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">HE</span>
                  </div>
                  <p className="text-[11px] leading-snug text-muted-foreground">
                    Fast-growing expansionists with narrow long-term trade-offs.
                  </p>
                </div>
              </div>
            </PanelCard>
          </section>

          <section id="race-section-identity" className="mb-8">
            <SectionHead>Identity</SectionHead>
            <PanelCard className="p-4">
              <div className="grid gap-3 md:grid-cols-[1fr_1fr_7rem] md:items-end">
                <FormField label="Race name">
                  <TextInput
                    aria-label="Race name"
                    value={race.name}
                    maxLength={32}
                    placeholder="Humanoid"
                    onChange={(event) => setCustomRace((current) => ({ ...current, name: event.target.value }))}
                  />
                </FormField>
                <FormField label="Plural name">
                  <TextInput
                    aria-label="Plural race name"
                    value={race.pluralName}
                    maxLength={32}
                    placeholder="Humanoids"
                    onChange={(event) => setCustomRace((current) => ({ ...current, pluralName: event.target.value }))}
                  />
                </FormField>
                <FormField label="Emblem">
                  <TextInput
                    aria-label="Emblem"
                    type="number"
                    min={0}
                    max={31}
                    value={race.emblem}
                    className="font-mono"
                    onChange={(event) => setCustomRace((current) => ({ ...current, emblem: clamp(Number(event.target.value), 0, 31) }))}
                  />
                </FormField>
              </div>
            </PanelCard>
          </section>

          <section id="race-section-prt" className="mb-8">
            <SectionHead>Primary Racial Trait - choose exactly one</SectionHead>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
              <button
                type="button"
                className={`rounded-md border p-3 text-left ${race.prt === "JOAT" ? "border-[var(--color-player-self)] bg-[var(--color-player-self)]/10" : "border-[var(--color-panel-border)] bg-[var(--color-surface-2)]"}`}
                aria-pressed={race.prt === "JOAT"}
                onClick={() => setCustomRace((current) => ({ ...current, prt: "JOAT" }))}
              >
                <div className="mb-0.5 flex items-start justify-between gap-1">
                  <span className="text-xs font-semibold">Jack of All Trades</span>
                  <span className="rounded border border-[var(--color-panel-border)] px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">JOAT</span>
                </div>
                <p className="mb-2 text-[11px] leading-snug text-muted-foreground">
                  Balanced generalists with a broad starting profile.
                </p>
                <span className="text-[10px] text-[var(--color-status-success)]">+ Standard start enabled</span>
              </button>
              <button
                type="button"
                className={`rounded-md border p-3 text-left ${race.prt === "HE" ? "border-[var(--color-player-self)] bg-[var(--color-player-self)]/10" : "border-[var(--color-panel-border)] bg-[var(--color-surface-2)]"}`}
                aria-pressed={race.prt === "HE"}
                onClick={() => setCustomRace((current) => ({ ...current, prt: "HE" }))}
              >
                <div className="mb-0.5 flex items-start justify-between gap-1">
                  <span className="text-xs font-semibold">Hyper Expansion</span>
                  <span className="rounded border border-[var(--color-panel-border)] px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">HE</span>
                </div>
                <p className="mb-2 text-[11px] leading-snug text-muted-foreground">Built for rapid colonisation and explosive population growth.</p>
                <span className="text-[10px] text-[var(--color-status-success)]">+ Population growth x2</span>
              </button>
              {LOCKED_PRTS.map((prt) => (
                <button
                  key={prt.abbr}
                  type="button"
                  disabled
                  className="rounded-md border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3 text-left opacity-55"
                >
                  <div className="mb-0.5 flex items-start justify-between gap-1">
                    <span className="text-xs font-semibold">{prt.name}</span>
                    <span className="rounded border border-[var(--color-panel-border)] px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">{prt.abbr}</span>
                  </div>
                  <p className="mb-2 text-[11px] leading-snug text-muted-foreground">{prt.desc}</p>
                  <div className="flex flex-col gap-0.5">
                    {prt.effects.map((effect) => (
                      <span
                        key={effect}
                        className={`text-[10px] ${effect.startsWith("+") ? "text-[var(--color-status-success)]" : "text-[var(--color-status-danger)]"}`}
                      >
                        {effect}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section id="race-section-lrt" className="mb-8">
            <SectionHead>Lesser Racial Traits - pick any combination</SectionHead>
            <div className="grid grid-cols-2 gap-1">
              {AVAILABLE_LRTS.map(([abbr, name, desc]) => {
                const checked = race.lrts.includes(abbr);
                return (
                  <label
                    key={abbr}
                    className="flex cursor-pointer items-start gap-2.5 rounded-md border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3 text-left transition-colours hover:border-[var(--color-ring)]"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      aria-label={name}
                      className="mt-0.5"
                      onChange={(event) => {
                        setCustomRace((current) => ({
                          ...current,
                          lrts: event.target.checked
                            ? Array.from(new Set([...current.lrts, abbr]))
                            : current.lrts.filter((lrt) => lrt !== abbr),
                        }));
                      }}
                    />
                    <span>
                      <span className="mb-0.5 flex items-center gap-1.5">
                        <span className="text-xs font-medium">{name}</span>
                        <span className="rounded border border-[var(--color-panel-border)] px-1 py-0.5 font-mono text-[9px] text-muted-foreground">{abbr}</span>
                      </span>
                      <span className="block text-[11px] leading-snug text-muted-foreground">{desc}</span>
                    </span>
                  </label>
                );
              })}
              {LOCKED_LRTS.map(([abbr, name, desc]) => (
                <button
                  key={abbr}
                  type="button"
                  disabled
                  className="flex items-start gap-2.5 rounded-md border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3 text-left opacity-55"
                >
                  <span className="mt-0.5 flex h-3.5 w-3.5 flex-shrink-0 items-center justify-center rounded border border-[var(--color-ring)] bg-[var(--color-surface-3)] text-[9px]" />
                  <span>
                    <span className="mb-0.5 flex items-center gap-1.5">
                      <span className="text-xs font-medium">{name}</span>
                      <span className="rounded border border-[var(--color-panel-border)] px-1 py-0.5 font-mono text-[9px] text-muted-foreground">{abbr}</span>
                    </span>
                    <span className="block text-[11px] leading-snug text-muted-foreground">{desc}</span>
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section id="race-section-habitat" className="mb-8">
            <SectionHead>Habitat - survivable environmental ranges</SectionHead>
            <PanelCard className="px-4 pb-2 pt-3">
              <div className="mb-1 hidden gap-2.5 md:grid md:grid-cols-[98px_70px_1fr_78px_78px]">
                <MutedText className="text-[10px]">Dimension</MutedText>
                <MutedText className="text-[10px]">Immune</MutedText>
                <MutedText className="pl-1 text-[10px]">Range</MutedText>
                <MutedText className="text-center text-[10px]">Min</MutedText>
                <MutedText className="text-center text-[10px]">Max</MutedText>
              </div>
              <HabRangeRow
                label="Gravity"
                color="var(--color-ironium-bright)"
                dim="gravity"
                factor={race.habitability.gravity}
                onImmuneChange={(immune) => updateHab("gravity", (current) => ({ ...current, immune }))}
                onLowChange={(value) => updateHab("gravity", (current) => ({ ...current, range: [value, current.range[1]] }))}
                onHighChange={(value) => updateHab("gravity", (current) => ({ ...current, range: [current.range[0], value] }))}
              />
              <HabRangeRow
                label="Temperature"
                color="var(--color-boranium-bright)"
                dim="temperature"
                factor={race.habitability.temperature}
                onImmuneChange={(immune) => updateHab("temperature", (current) => ({ ...current, immune }))}
                onLowChange={(value) => updateHab("temperature", (current) => ({ ...current, range: [value, current.range[1]] }))}
                onHighChange={(value) => updateHab("temperature", (current) => ({ ...current, range: [current.range[0], value] }))}
              />
              <HabRangeRow
                label="Radiation"
                color="var(--color-status-danger)"
                dim="radiation"
                factor={race.habitability.radiation}
                onImmuneChange={(immune) => updateHab("radiation", (current) => ({ ...current, immune }))}
                onLowChange={(value) => updateHab("radiation", (current) => ({ ...current, range: [value, current.range[1]] }))}
                onHighChange={(value) => updateHab("radiation", (current) => ({ ...current, range: [current.range[0], value] }))}
              />
            </PanelCard>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="status-pill text-muted-foreground">
                {habitableEstimate === null ? "Immunity affects habitable-world estimate" : `~${habitableEstimate}% of worlds in range`}
              </span>
            </div>
          </section>

          <section id="race-section-economy" className="mb-8">
            <SectionHead>Economy</SectionHead>
            <PanelCard className="p-4">
              <label className="mb-4 block text-sm">
                <span className="flex items-center justify-between gap-3">
                  <span>Maximum population growth</span>
                  <span className="status-pill font-mono">{race.maxGrowthRate}%{race.prt === "HE" ? ` · 2× effective (${2 * race.maxGrowthRate}%)` : ""}</span>
                </span>
                <input
                  aria-label="Max growth rate"
                  type="range"
                  min={1}
                  max={20}
                  value={race.maxGrowthRate}
                  className="mt-2 w-full accent-[var(--color-player-self)]"
                  onChange={(event) => setCustomRace((current) => ({ ...current, maxGrowthRate: Number(event.target.value) }))}
                />
              </label>
              <div className="grid gap-2 md:grid-cols-2">
                {ECONOMY_FIELDS.map((field) => (
                  <div key={field.key} className="rounded-md border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <MutedText className="text-[11px]">{field.label}</MutedText>
                      <span className="rounded border border-[var(--color-panel-border)] bg-background px-2 py-0.5 font-mono text-[11px]">
                        {race.economy[field.key]}
                      </span>
                    </div>
                    <input
                      aria-label={field.label}
                      type="range"
                      min={field.min}
                      max={field.max}
                      value={race.economy[field.key]}
                      className="w-full accent-[var(--color-player-self)]"
                      onChange={(event) => updateEconomy(field.key, clamp(Number(event.target.value), field.min, field.max))}
                    />
                    <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground">
                      <span>{field.min}</span>
                      <span>{field.max}</span>
                    </div>
                  </div>
                ))}
              </div>
              <label className="mt-3 flex items-center gap-2 rounded-md border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3 text-sm">
                <input
                  type="checkbox"
                  checked={race.economy.factoriesSaveGermanium}
                  onChange={(event) => updateEconomy("factoriesSaveGermanium", event.target.checked)}
                />
                Factories save germanium
              </label>
            </PanelCard>
          </section>

          <section id="race-section-research" className="mb-8">
            <SectionHead>Research cost profile</SectionHead>
            <PanelCard className="px-4 py-2">
              {RESEARCH_FIELDS.map((field) => {
                const selected = race.research.fieldProfile[field];
                return (
                  <div
                    key={field}
                    className="grid items-center gap-3 border-b border-[var(--color-panel-border)] py-2 last:border-b-0 md:grid-cols-[130px_1fr]"
                  >
                    <div className="flex items-center gap-2 text-xs">
                      <span
                        className="h-2 w-2 flex-shrink-0 rounded-sm"
                        style={{ background: RESEARCH_FIELD_COLOURS[field] }}
                      />
                      {RESEARCH_FIELD_LABELS[field]}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {(["cheap", "standard", "expensive"] as ResearchCostProfile[]).map((profile) => (
                        <button
                          key={profile}
                          type="button"
                          aria-pressed={selected === profile}
                          className={[
                            "rounded border px-2 py-1 font-mono text-[11px] transition-colors",
                            selected === profile
                              ? "border-[var(--color-player-self)] bg-[var(--color-player-self)]/10 text-[var(--color-player-self)]"
                              : "border-[var(--color-panel-border)] bg-[var(--color-surface-3)] text-muted-foreground hover:border-[var(--color-ring)]",
                          ].join(" ")}
                          onClick={() => updateResearch((current) => ({
                            ...current,
                            fieldProfile: {
                              ...current.fieldProfile,
                              [field]: profile,
                            } as Record<ResearchField, ResearchCostProfile>,
                          }))}
                        >
                          {profile}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
              <label className="mt-3 flex items-center gap-2 border-t border-[var(--color-panel-border)] pt-3 text-sm">
                <input
                  type="checkbox"
                  checked={race.research.startAtTech3}
                  onChange={(event) => updateResearch((current) => ({ ...current, startAtTech3: event.target.checked }))}
                />
                Start expensive fields at tech 3
              </label>
            </PanelCard>
          </section>

          </div>

        <aside className="w-60 flex-shrink-0 self-start border-l border-[var(--color-panel-border)] bg-[var(--color-surface-1)] p-4">
          <SidebarGroup title="Race">
            <SidebarRow k="Name" v={race.name || "-"} />
            <SidebarRow k="Plural" v={race.pluralName || "-"} />
            <SidebarRow k="Emblem" v={String(race.emblem)} />
          </SidebarGroup>

          <SidebarGroup title="Primary Trait">
            <p className="text-xs font-semibold">{race.prt === "HE" ? "Hyper Expansion" : "Jack of All Trades"}</p>
          </SidebarGroup>

          <SidebarGroup title="Habitat">
            {(["gravity", "temperature", "radiation"] as HabKey[]).map((key) => {
              const factor = race.habitability[key];
              const label = key.charAt(0).toUpperCase() + key.slice(1);
              const value = factor.immune
                ? "immune"
                : `${HAB_DISPLAY[key](factor.range[0])}-${HAB_DISPLAY[key](factor.range[1])}`;
              return <SidebarRow key={key} k={label} v={value} />;
            })}
            <SidebarRow
              k="In range"
              v={habitableEstimate === null ? "immune" : `~${habitableEstimate}%`}
              vColor={habitableEstimate === null || habitableEstimate >= 10 ? "var(--color-player-self)" : "var(--color-status-danger)"}
            />
          </SidebarGroup>

          <SidebarGroup title="Research">
            {RESEARCH_FIELDS.map((field) => (
              <div key={field} className="flex items-baseline justify-between gap-2 py-0.5">
                <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <span className="h-1.5 w-1.5 flex-shrink-0 rounded-sm" style={{ background: RESEARCH_FIELD_COLOURS[field] }} />
                  {RESEARCH_FIELD_LABELS[field]}
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">{race.research.fieldProfile[field]}</span>
              </div>
            ))}
          </SidebarGroup>

          <SidebarGroup title="Cost">
            {costBreakdown ? (
              <>
                {BREAKDOWN_LABELS.map(([key, label]) => (
                  <SidebarRow key={key} k={label} v={String(costBreakdown[key])} />
                ))}
                <SidebarRow
                  k="Remaining"
                  v={`${costBreakdown.pointsLeft > 0 ? "+" : ""}${costBreakdown.pointsLeft}`}
                  vColor={costBreakdown.pointsLeft < 0 ? "var(--color-status-danger)" : "var(--color-player-self)"}
                />
              </>
            ) : (
              <MutedText className="text-[10px]">Awaiting preview</MutedText>
            )}
          </SidebarGroup>

          <div className={`flex items-center gap-1.5 text-xs ${validationMessages.length === 0 ? "text-[var(--color-status-success)]" : "text-[var(--color-status-danger)]"}`}>
            <span className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] ${validationMessages.length === 0 ? "bg-[var(--color-status-success)]/20" : "bg-[var(--color-status-danger)]/20"}`}>
              {validationMessages.length === 0 ? "✓" : validationMessages.length}
            </span>
            {validationMessages.length === 0 ? "Ready to save" : `${validationMessages.length} issue${validationMessages.length === 1 ? "" : "s"} to fix`}
          </div>
        </aside>
          </div>
        </section>
      </div>
    </main>
  );
}
