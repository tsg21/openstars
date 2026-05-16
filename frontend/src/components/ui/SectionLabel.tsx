import type { ElementType, ReactNode } from "react";
import { cn } from "../../lib/utils";

interface SectionLabelProps<T extends ElementType = "div"> {
  as?: T;
  children: ReactNode;
  className?: string;
}

export function SectionLabel<T extends ElementType = "div">({
  as,
  children,
  className,
}: SectionLabelProps<T>) {
  const Component = as ?? "div";

  return (
    <Component className={cn("text-xs uppercase tracking-widest text-muted-foreground", className)}>
      {children}
    </Component>
  );
}
