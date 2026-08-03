import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  Design,
  DesignerCreateDesignComponent,
  DesignerDesignDetailResponse,
  DesignerDesignSummary,
  DesignerReferenceData,
} from "../../types";
import {
  createDesign,
  getDesignDetail,
  getDesignerReferenceData,
  getDesigns,
  ApiError,
} from "../../api/client";
import { Button } from "../ui/Button";
import { FormField, SelectInput, TextInput } from "../ui/FormField";
import { MutedText } from "../ui/MutedText";
import {
  assignmentsToFitState,
  computeDesignValidationErrors,
  fitStateToAssignments,
  type FitState,
} from "../../lib/designerFit";
import { DragAndDropFitter } from "../designer/DragAndDropFitter";

interface DesignsWorkspaceProps {
  gameId: string;
  player: string;
}

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
  const [fitState, setFitState] = useState<FitState>(() => new Map());
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
        setSelectedDesign(null);
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

  const selectedDesignHull = useMemo(() => {
    if (!referenceData || !selectedDesignDetail) return null;
    return referenceData.hulls.find((hull) => hull.id === selectedDesignDetail.hull) ?? null;
  }, [referenceData, selectedDesignDetail]);

  const selectedDesignFitState = useMemo(
    () => assignmentsToFitState(selectedDesignDetail?.components),
    [selectedDesignDetail],
  );
  const ignoreReadOnlyFitChange = useCallback(() => undefined, []);

  const [fitStateHull, setFitStateHull] = useState(selectedHull);
  if (selectedHull !== fitStateHull) {
    setFitStateHull(selectedHull);
    setFitState(new Map());
  }

  const selectedComponents = useMemo(
    (): DesignerCreateDesignComponent[] => fitStateToAssignments(fitState),
    [fitState],
  );

  const validationErrors = useMemo(() => {
    if (!selectedHull) {
      return [];
    }
    return computeDesignValidationErrors(selectedHull, fitState);
  }, [fitState, selectedHull]);

  const canSave =
    creating &&
    !!selectedHull &&
    designName.trim().length > 0 &&
    validationErrors.length === 0 &&
    selectedComponents.length > 0 &&
    !saving;

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
      setFitState(new Map());
      setSelectedHullId("");
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
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
              <MutedText as="div" className="text-xs">{design.hull}</MutedText>
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
          <div className="min-h-0 space-y-4 overflow-y-auto">
            <h2 className="text-base font-semibold text-foreground">Create Ship Design</h2>
            {selectedHull && (
              <DragAndDropFitter
                hull={selectedHull}
                components={referenceData.components}
                value={fitState}
                onChange={setFitState}
                controls={
                  <div className="grid gap-3 md:grid-cols-2">
                    <FormField label="Design name">
                      <TextInput
                        aria-label="Design name"
                        value={designName}
                        onChange={(event) => setDesignName(event.target.value)}
                        maxLength={64}
                      />
                    </FormField>

                    <FormField label="Hull">
                      <SelectInput
                        aria-label="Hull"
                        value={selectedHullId}
                        onChange={(event) => setSelectedHullId(event.target.value)}
                      >
                        {referenceData.hulls.map((hull) => (
                          <option key={hull.id} value={hull.id}>
                            {hull.name}
                          </option>
                        ))}
                      </SelectInput>
                    </FormField>
                  </div>
                }
                actions={
                  <div className="flex items-center gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={!canSave}
                      onClick={() => void handleSave()}
                    >
                      {saving ? "Saving…" : "Save Design"}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setCreating(false);
                        setSelectedHullId("");
                        setFitState(new Map());
                        setDesignName("");
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                }
              />
            )}
          </div>
        ) : selectedDesignDetail && selectedDesignHull ? (
          <div className="min-h-0 space-y-4 overflow-y-auto">
            <h2 className="text-base font-semibold text-foreground">{selectedDesignDetail.name}</h2>
            <DragAndDropFitter
              hull={selectedDesignHull}
              components={referenceData.components}
              value={selectedDesignFitState}
              onChange={ignoreReadOnlyFitChange}
              readOnly
              controls={
                <div className="grid gap-3 md:grid-cols-2">
                  <FormField label="Design name">
                    <TextInput
                      aria-label="Design name"
                      value={selectedDesignDetail.name}
                      disabled
                      readOnly
                    />
                  </FormField>

                  <FormField label="Hull">
                    <SelectInput aria-label="Hull" value={selectedDesignDetail.hull} disabled>
                      <option value={selectedDesignDetail.hull}>{selectedDesignHull.name}</option>
                    </SelectInput>
                  </FormField>
                </div>
              }
            />
          </div>
        ) : selectedDesignSummary ? (
          <div className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">{selectedDesignSummary.name}</h2>
            <MutedText as="p" className="text-sm">Hull: {selectedDesignSummary.hull}</MutedText>
            <MutedText as="p" className="text-sm">
              Fuel capacity {selectedDesignSummary.fuelCapacity} mg • Cost {selectedDesignSummary.cost.resources} resources
            </MutedText>
            <MutedText as="p" className="text-sm">Scanner unknown • Cargo unknown</MutedText>
          </div>
        ) : (
          <MutedText as="div" className="text-sm">Select a design to inspect.</MutedText>
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
