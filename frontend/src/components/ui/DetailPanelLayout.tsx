import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

export function DetailPanelContent({ children }: { children: ReactNode }) {
  return <div className="flex h-full flex-col gap-3 p-4">{children}</div>;
}

export function DetailPanelHeading({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement> & {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h2 className={cn("text-base font-semibold text-foreground", className)} {...props}>
      {children}
    </h2>
  );
}

