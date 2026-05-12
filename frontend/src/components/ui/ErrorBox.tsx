import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface ErrorBoxProps {
  children: ReactNode;
  className?: string;
}

export function ErrorBox({ children, className }: ErrorBoxProps) {
  return (
    <p
      className={cn(
        "rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400",
        className,
      )}
    >
      {children}
    </p>
  );
}
