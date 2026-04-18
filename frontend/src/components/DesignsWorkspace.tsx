import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  Design,
  DesignerCreateDesignComponent,
  DesignerDesignDetailResponse,
  DesignerDesignSummary,
  DesignerReferenceData,
} from "../types";
import {
  createDesign,
  getDesignDetail,
  getDesignerReferenceData,
  getDesigns,
  ApiError,
} from "../api/client";
import { Button } from "./Button";
import { FormField, SelectInput, TextInput } from "./FormField";
import { MutedText } from "./MutedText";

interface DesignsWorkspaceProps {
  gameId: string;
  player: string;
}

type CreateSlotDraft = {
  slotNumber: number;
  componentId: string;
  componentCount: number;
};

type DesignSelection = {
  summary: DesignerDesignSummary;
  detail: Design | null;
};

export function DesignsWorkspace({ gameId, player }: DesignsWorkspaceProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [referenceData, setReferenceData] = useState<DesignerReferenceData | null>(null);
  const [designSummaries, setDesignSummaries] = useState<DesignerDesignSummary[]>([]);
  const [selectedDesign, setSelectedDesign] = useState<DesignSelection | null>(null);
  const [creating, setCreating] = useState(false);
  const [selectedHullId, setSelectedHullId] = useState("");
  const [designName, setDesignName] = useState("");
  const [slotDrafts, setSlotDrafts] = useState<CreateSlotDraft[]>([]);
  const [saving, setSaving] = useState(false);
  const selectedDesignSummary = selectedDesign?.summary ?? null;
  const selectedDesignDetail = selectedDesign?.detail ?? null;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [reference, summaries] = await Promise.all([
          getDesignerReferenceData(gameId, player, "ship"),
          getDesigns(gameId, player),
        ]);
        if (cancelled) return;
        setReferenceData(reference);
        setDesignSummaries(summaries);
        setSelectedDesign(summaries[0] ? { summary: summaries[0], detail: null } : null);
      } catch (err) {
        if (cancelled) return;
        setError(formatApiError(err));
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [gameId, player]);

  const selectedHull = useMemo(() => {
    if (!referenceData) return null;
    return referenceData.hulls.find((hull) => hull.id === selectedHullId) ?? null;
  }, [referenceData, selectedHullId]);

  useEffect(() => {
    if (!selectedHull) {
      setSlotDrafts([]);
      return;
    }
    setSlotDrafts(
      selectedHull.slots.map((slot) => ({
        slotNumber: slot.slotNumber,
        componentId: "",
        componentCount: 1,
      })),
    );
  }, [selectedHull]);

  const componentOptionsBySlotNumber = useMemo(() => {
    const bySlot = new Map<number, DesignerReferenceData["components"]>();
    if (!selectedHull || !referenceData) {
      return bySlot;
    }
    for (const slot of selectedHull.slots) {
      bySlot.set(
        slot.slotNumber,
        referenceData.components.filter((component) =>
          slot.slotCategories.includes(component.componentType),
        ),
      );
    }
    return bySlot;
  }, [selectedHull, referenceData]);

  const selectedComponents = useMemo(
    () =>
      slotDrafts
        .filter((slot) => slot.componentId)
        .map((slot): DesignerCreateDesignComponent => ({
          slotNumber: slot.slotNumber,
          componentId: slot.componentId,
          componentCount: slot.componentCount,
        })),
    [slotDrafts],
  );

  const missingRequiredSlots = useMemo(() => {
    if (!selectedHull) {
      return [];
    }
    const selectedSlotNumbers = new Set(
      selectedComponents.map((component) => component.slotNumber),
    );
    return selectedHull.slots
      .filter((slot) => slot.required && !selectedSlotNumbers.has(slot.slotNumber))
      .map((slot) => slot.slotNumber);
  }, [selectedComponents, selectedHull]);

  const canSave =
    creating &&
    !!selectedHull &&
    designName.trim().length > 0 &&
    missingRequiredSlots.length === 0 &&
    selectedComponents.length > 0 &&
    !saving;

  const derivedSummary = useMemo(() => {
    if (!referenceData || selectedComponents.length === 0) {
      return null;
    }
    let scannerNormal = 0;
    let scannerPenetrating = 0;
    const cargoCapacity = 0;
    let resources = 0;
    let ironium = 0;
    let boranium = 0;
    let germanium = 0;
    for (const assignment of selectedComponents) {
      const component = referenceData.components.find((entry) => entry.id === assignment.componentId);
      if (!component) continue;
      resources += component.cost.resources * assignment.componentCount;
      ironium += component.cost.ironium * assignment.componentCount;
      boranium += component.cost.boranium * assignment.componentCount;
      germanium += component.cost.germanium * assignment.componentCount;
      if (component.scanner) {
        scannerNormal = Math.max(scannerNormal, component.scanner.normal);
        scannerPenetrating = Math.max(scannerPenetrating, component.scanner.penetrating);
      }
    }
    return {
      fuelCapacity: selectedHull?.fuelCapacity ?? 0,
      scannerNormal,
      scannerPenetrating,
      cargoCapacity,
      resources,
      ironium,
      boranium,
      germanium,
    };
  }, [referenceData, selectedComponents, selectedHull]);

  const loadDesignDetailOrNull = useCallback(async (designId: string): Promise<Design | null> => {
    try {
      const detail: DesignerDesignDetailResponse = await getDesignDetail(gameId, player, designId);
      return detail.design;
    } catch {
      return null;
    }
  }, [gameId, player]);

  async function refreshDesigns(selectDesignId?: string) {
    const summaries = await getDesigns(gameId, player);
    setDesignSummaries(summaries);
    if (!summaries.length) {
      setSelectedDesign(null);
      return;
    }
    const selectedSummary = (
      (selectDesignId ? summaries.find((design) => design.id === selectDesignId) : null) ??
      summaries[0]
    )!;
    const detail = await loadDesignDetailOrNull(selectedSummary.id);
    setSelectedDesign({ summary: selectedSummary, detail });
  }

  async function selectDesign(design: DesignerDesignSummary) {
    setCreating(false);
    setError(null);
    const detail = await loadDesignDetailOrNull(design.id);
    setSelectedDesign({ summary: design, detail });
    if (!detail) {
      setError("Unable to load full design detail. Showing summary values.");
    }
  }

  async function handleSave() {
    if (!canSave || !selectedHull) return;
    setSaving(true);
    setError(null);
    try {
      const result = await createDesign(gameId, player, {
        name: designName.trim(),
        hull: selectedHull.id,
        components: selectedComponents,
      });
      await refreshDesigns(result.design.id);
      setCreating(false);
      setDesignName("");
      setSlotDrafts([]);
      setSelectedHullId("");
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  }

  function setSlotComponent(slotNumber: number, componentId: string) {
    setSlotDrafts((current) =>
      current.map((slot) => {
        if (slot.slotNumber !== slotNumber) return slot;
        const hullSlot = selectedHull?.slots.find(
          (candidate) => candidate.slotNumber === slotNumber,
        );
        const slotMax = hullSlot?.capacity ?? Number.POSITIVE_INFINITY;
        const boundedCount = Math.min(slotMax, Math.max(1, slot.componentCount));
        return {
          ...slot,
          componentId,
          componentCount: componentId ? boundedCount : 1,
        };
      }),
    );
  }

  function setSlotComponentCount(slotNumber: number, count: number) {
    setSlotDrafts((current) =>
      current.map((slot) => {
        if (slot.slotNumber !== slotNumber) return slot;
        const hullSlot = selectedHull?.slots.find(
          (candidate) => candidate.slotNumber === slotNumber,
        );
        const slotMax = hullSlot?.capacity ?? Number.POSITIVE_INFINITY;
        const normalised = Number.isNaN(count) ? 1 : Math.trunc(count);
        return {
          ...slot,
          componentCount: Math.min(slotMax, Math.max(1, normalised)),
        };
      }),
    );
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <MutedText>Loading designs…</MutedText>
      </div>
    );
  }

  if (!referenceData) {
    return (
      <div className="p-4">
        <p className="text-red-400">{error ?? "Failed to load designer data."}</p>
      </div>
    );
  }

  return (
    <div className="flex h-full gap-4 overflow-hidden p-4">
      <section className="panel-surface flex w-80 flex-col rounded-md border border-[var(--color-panel-border)] p-3">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground">Designs</h2>
          <Button
            variant="primary"
            size="xs"
            onClick={() => {
              setCreating(true);
              setSelectedDesign(null);
              setDesignName("");
              setSelectedHullId(referenceData.hulls[0]?.id ?? "");
            }}
          >
            Create New
          </Button>
        </div>
        <div className="space-y-1 overflow-y-auto">
          {designSummaries.map((design) => (
            <button
              key={design.id}
              type="button"
              className="w-full rounded-md border border-[var(--color-panel-border)] px-2 py-1 text-left hover:bg-white/5"
              onClick={() => void selectDesign(design)}
            >
              <div className="truncate text-sm text-foreground">{design.name}</div>
              <div className="text-xs text-muted-foreground">{design.hull}</div>
            </button>
          ))}
          {designSummaries.length === 0 && (
            <div className="rounded-md border border-dashed border-[var(--color-panel-border)] p-3 text-xs text-muted-foreground">
              No designs yet.
            </div>
          )}
        </div>
      </section>

      <section className="panel-surface flex min-w-0 flex-1 flex-col rounded-md border border-[var(--color-panel-border)] p-4">
        {error && <p className="mb-3 text-sm text-red-400">{error}</p>}

        {creating ? (
          <div className="space-y-4 overflow-y-auto">
            <h2 className="text-base font-semibold text-foreground">Create Ship Design</h2>
            <FormField label="Hull">
              <SelectInput
                aria-label="Hull"
                value={selectedHullId}
                onChange={(event) => setSelectedHullId(event.target.value)}
              >
                <option value="">Select a hull…</option>
                {referenceData.hulls.map((hull) => (
                  <option key={hull.id} value={hull.id}>
                    {hull.name}
                  </option>
                ))}
              </SelectInput>
            </FormField>

            {selectedHull && (
              <div className="space-y-2">
                <div className="text-xs uppercase tracking-widest text-muted-foreground">Slots</div>
                {selectedHull.slots.map((slot) => {
                  const draft = slotDrafts.find((item) => item.slotNumber === slot.slotNumber);
                  const options = componentOptionsBySlotNumber.get(slot.slotNumber) ?? [];
                  const minCount = 1;
                  const maxCount = slot.capacity;
                  return (
                    <div
                      key={slot.slotNumber}
                      className="grid grid-cols-[1fr_1fr_100px] items-end gap-2 rounded-md border border-[var(--color-panel-border)] p-2"
                    >
                      <div>
                        <div className="text-sm text-foreground">
                          Slot {slot.slotNumber}
                          {slot.required ? " *" : ""}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {slot.slotCategories.join(", ")} (capacity {slot.capacity})
                        </div>
                      </div>
                      <FormField label="Component">
                        <SelectInput
                          aria-label={`Component slot ${slot.slotNumber}`}
                          value={draft?.componentId ?? ""}
                          onChange={(event) => setSlotComponent(slot.slotNumber, event.target.value)}
                        >
                          <option value="">Unassigned</option>
                          {options.map((component) => (
                            <option key={component.id} value={component.id}>
                              {component.name}
                            </option>
                          ))}
                        </SelectInput>
                      </FormField>
                      <FormField label="Count">
                        <TextInput
                          aria-label={`Count slot ${slot.slotNumber}`}
                          type="number"
                          min={minCount}
                          max={maxCount}
                          value={draft?.componentCount ?? 1}
                          disabled={!draft?.componentId}
                          onChange={(event) => {
                            const parsed = Number(event.target.value);
                            setSlotComponentCount(slot.slotNumber, Math.min(maxCount, parsed));
                          }}
                        />
                      </FormField>
                    </div>
                  );
                })}
              </div>
            )}

            <FormField label="Design name">
              <TextInput
                aria-label="Design name"
                value={designName}
                onChange={(event) => setDesignName(event.target.value)}
                maxLength={64}
              />
            </FormField>

            {missingRequiredSlots.length > 0 && (
              <p className="text-sm text-amber-400">
                Missing required slots: {missingRequiredSlots.join(", ")}
              </p>
            )}

            {derivedSummary && (
              <div className="rounded-md border border-[var(--color-panel-border)] p-3 text-sm">
                <div className="font-semibold text-foreground">Derived summary</div>
                <div className="mt-1 text-muted-foreground">
                  Fuel capacity {derivedSummary.fuelCapacity} mg • Scanner {derivedSummary.scannerNormal}/
                  {derivedSummary.scannerPenetrating} • Cargo {derivedSummary.cargoCapacity}
                </div>
                <div className="text-muted-foreground">
                  Cost: {derivedSummary.resources} resources, {derivedSummary.ironium} ironium,{" "}
                  {derivedSummary.boranium} boranium, {derivedSummary.germanium} germanium
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Button variant="primary" size="sm" disabled={!canSave} onClick={() => void handleSave()}>
                {saving ? "Saving…" : "Save Design"}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setCreating(false);
                  setSelectedHullId("");
                  setSlotDrafts([]);
                  setDesignName("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : selectedDesignSummary ? (
          <div className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">{selectedDesignSummary.name}</h2>
            <p className="text-sm text-muted-foreground">Hull: {selectedDesignSummary.hull}</p>
            <p className="text-sm text-muted-foreground">
              Fuel capacity {selectedDesignSummary.fuelCapacity} mg • Cost {selectedDesignSummary.cost.resources} resources
            </p>
            {selectedDesignDetail ? (
              <p className="text-sm text-muted-foreground">
                Scanner {selectedDesignDetail.scanner.normal}/{selectedDesignDetail.scanner.penetrating}
                {" "}• Cargo {selectedDesignDetail.cargoCapacity}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">Scanner unknown • Cargo unknown</p>
            )}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">Select a design to inspect.</div>
        )}
      </section>
    </div>
  );
}

function formatApiError(err: unknown): string {
  if (err instanceof ApiError) {
    return `${err.code}: ${err.message}`;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Unknown error";
}
