import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
}

export function StatusBadge({ children, className, ...props }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "rounded-full border border-[var(--color-panel-border)] bg-background/60 px-2.5 py-0.5 text-sm font-bold",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
