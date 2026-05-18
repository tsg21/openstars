import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

interface PanelCardBaseProps {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
  /** "panel" (default): outer card with panel-bg; "surface": inner elevated surface with p-3 */
  variant?: "panel" | "surface";
}

type PanelCardProps =
  | (PanelCardBaseProps &
      HTMLAttributes<HTMLDivElement> & {
        as?: "div";
      })
  | (PanelCardBaseProps &
      ButtonHTMLAttributes<HTMLButtonElement> & {
        as: "button";
      });

export function PanelCard(props: PanelCardProps) {
  const { children, className, interactive = false, variant = "panel" } = props;
  const sharedClassName = cn(
    "rounded-md border border-[var(--color-panel-border)]",
    variant === "panel" ? "rounded-lg bg-[var(--color-panel-bg)]" : "elevated-surface p-3",
    interactive &&
      "transition-colors hover:border-[var(--color-player-self)]/50",
    className,
  );

  if (props.as === "button") {
    const { as: buttonAs, type = "button", className: _c, children: _ch, interactive: _i, variant: _v, ...buttonProps } = props;
    void buttonAs;

    return (
      <button
        type={type}
        className={cn(sharedClassName, interactive && "cursor-pointer")}
        {...buttonProps}
      >
        {children}
      </button>
    );
  }

  const { as: divAs, className: _c, children: _ch, interactive: _i, variant: _v, ...divProps } = props;
  void divAs;

  return (
    <div className={sharedClassName} {...divProps}>
      {children}
    </div>
  );
}
