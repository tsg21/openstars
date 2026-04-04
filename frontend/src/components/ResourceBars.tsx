import { useEffect, useMemo, useRef } from "react";
import type { Minerals } from "../types";

const MINERAL_CONFIG = [
  { key: "ironium", label: "Ironium", bright: "#60a5fa", dark: "#1e40af" },
  { key: "boranium", label: "Boranium", bright: "#facc15", dark: "#713f12" },
  { key: "germanium", label: "Germanium", bright: "#e5e7eb", dark: "#6b7280" },
] as const;

const CONCENTRATION_MAX = 200;
const CONCENTRATION_MARKER_COLOUR = "#3f3f46";

export interface ResourceBarsProps {
  minerals: Minerals;
  miningRate?: Minerals | null;
  concentrations?: Minerals | null;
  colonists?: number | null;
  maxValue?: number | null;
}

export function ResourceBars({
  minerals,
  miningRate,
  concentrations,
  colonists,
  maxValue,
}: ResourceBarsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const rows = useMemo(
    () => [
      ...MINERAL_CONFIG.map(({ key, label, bright, dark }) => ({
        mineralKey: key,
        label,
        value: minerals[key],
        rate: miningRate?.[key] ?? 0,
        concentration: concentrations?.[key] ?? null,
        bright,
        dark,
      })),
      ...(colonists != null
        ? [
            {
              mineralKey: null,
              label: "Colonists",
              value: colonists,
              rate: 0,
              concentration: null,
              bright: "#f9fafb",
              dark: "#d1d5db",
            },
          ]
        : []),
    ],
    [minerals, miningRate, concentrations, colonists],
  );

  const scaleMax =
    maxValue != null
      ? Math.max(maxValue, ...rows.map((row) => row.value))
      : Math.max(100, ...rows.map((row) => row.value));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio ?? 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, W, H);

    const labelW = 72;
    const valueW = 64;
    const barX = labelW;
    const barW = W - labelW - valueW - 4;
    const rowH = H / rows.length;
    const barH = 10;

    rows.forEach(({ label, value, rate, concentration, bright, dark }, i) => {
      const y = i * rowH + rowH / 2;

      ctx.font = "11px ui-monospace, monospace";
      ctx.fillStyle = "#9ca3af";
      ctx.textBaseline = "middle";
      ctx.textAlign = "left";
      ctx.fillText(label, 0, y);

      const trackY = y - barH / 2;
      ctx.fillStyle = "#1f2937";
      ctx.beginPath();
      ctx.roundRect(barX, trackY, barW, barH, 2);
      ctx.fill();

      const stockW = Math.round((value / scaleMax) * barW);
      if (stockW > 0) {
        ctx.fillStyle = bright;
        ctx.beginPath();
        ctx.roundRect(barX, trackY, stockW, barH, 2);
        ctx.fill();
      }

      const rateW = Math.round((rate / scaleMax) * barW);
      if (rateW > 0) {
        ctx.fillStyle = dark;
        ctx.beginPath();
        ctx.roundRect(barX + stockW, trackY, rateW, barH, 2);
        ctx.fill();
      }

      if (concentration != null) {
        const markerX = barX + Math.round((Math.max(0, Math.min(CONCENTRATION_MAX, concentration)) / CONCENTRATION_MAX) * barW);
        const markerY = y;
        const markerRadius = 4;

        ctx.fillStyle = CONCENTRATION_MARKER_COLOUR;
        ctx.beginPath();
        ctx.moveTo(markerX, markerY - markerRadius);
        ctx.lineTo(markerX + markerRadius, markerY);
        ctx.lineTo(markerX, markerY + markerRadius);
        ctx.lineTo(markerX - markerRadius, markerY);
        ctx.closePath();
        ctx.fill();
      }

      ctx.fillStyle = "#f9fafb";
      ctx.textAlign = "right";
      ctx.fillText(`${value.toLocaleString()}kT`, W, y);
    });
  }, [rows, scaleMax]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full"
      style={{ height: rows.length * 22 }}
      role="img"
      aria-label="Resource bars"
    />
  );
}
