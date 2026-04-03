import { useEffect, useRef } from "react";
import type { Minerals } from "../types";

const MINERAL_CONFIG = [
  { key: "ironium", label: "Ironium", bright: "#60a5fa", dark: "#1e40af" },
  { key: "boranium", label: "Boranium", bright: "#facc15", dark: "#713f12" },
  { key: "germanium", label: "Germanium", bright: "#e5e7eb", dark: "#6b7280" },
] as const;

export interface MineralBarsProps {
  minerals: Minerals;
  miningRate?: Minerals | null;
  concentrations?: Minerals | null;
}

export function MineralBars({
  minerals,
  miningRate,
  concentrations,
}: MineralBarsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const maxStock = Math.max(
    100,
    minerals.ironium,
    minerals.boranium,
    minerals.germanium,
  );

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
    const valueW = 52;
    const barX = labelW;
    const barW = W - labelW - valueW - 4;
    const rowH = H / 3;
    const barH = 10;

    MINERAL_CONFIG.forEach(({ key, label, bright, dark }, i) => {
      const stock = minerals[key];
      const rate = miningRate?.[key] ?? 0;
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

      const stockW = Math.round((stock / maxStock) * barW);
      if (stockW > 0) {
        ctx.fillStyle = bright;
        ctx.beginPath();
        ctx.roundRect(barX, trackY, stockW, barH, 2);
        ctx.fill();
      }

      const rateW = Math.round((rate / maxStock) * barW);
      if (rateW > 0) {
        ctx.fillStyle = dark;
        ctx.beginPath();
        ctx.roundRect(barX + stockW, trackY, rateW, barH, 2);
        ctx.fill();
      }

      ctx.fillStyle = "#f9fafb";
      ctx.textAlign = "right";
      ctx.fillText(`${stock.toLocaleString()}kT`, W, y);
    });
  }, [minerals, miningRate, maxStock]);

  return (
    <div className="space-y-1">
      <canvas
        ref={canvasRef}
        className="w-full"
        style={{ height: 66 }}
        role="img"
        aria-label="Mineral stockpile bars"
      />
      {concentrations && (
        <div className="text-xs text-muted-foreground">
          conc: {concentrations.ironium} / {concentrations.boranium} / {concentrations.germanium}
        </div>
      )}
    </div>
  );
}
