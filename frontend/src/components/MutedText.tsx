import type { ElementType, ReactNode } from "react";
import { cn } from "../lib/utils";

interface MutedTextProps<T extends ElementType = "span"> {
  as?: T;
  children: ReactNode;
  className?: string;
}

export function MutedText<T extends ElementType = "span">({
  as,
  children,
  className,
}: MutedTextProps<T>) {
  const Component = as ?? "span";

  return <Component className={cn("text-muted-foreground", className)}>{children}</Component>;
}
