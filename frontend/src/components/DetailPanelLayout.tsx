import type { ReactNode } from "react";
import { cn } from "../lib/utils";

export function DetailPanelContent({ children }: { children: ReactNode }) {
  return <div className="flex h-full flex-col gap-3 p-4">{children}</div>;
}

export function DetailPanelHeading({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <h2 className={cn("text-base font-semibold text-foreground", className)}>{children}</h2>;
}

export function DetailPanelCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "elevated-surface rounded-md border border-[var(--color-panel-border)] p-3",
        className,
      )}
    >
      {children}
    </div>
  );
}
