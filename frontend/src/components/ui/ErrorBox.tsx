import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface ErrorBoxProps {
  children: ReactNode;
  className?: string;
}

export function ErrorBox({ children, className }: ErrorBoxProps) {
  return (
    // A div, not a p: callers pass block content (paragraphs, retry buttons),
    // and role="alert" announces the failure when the box appears.
    <div
      role="alert"
      className={cn(
        "rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400",
        className,
      )}
    >
      {children}
    </div>
  );
}
