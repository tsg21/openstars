import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { cn } from "../lib/utils";

interface PanelCardBaseProps {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
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
  const { children, className, interactive = false } = props;
  const sharedClassName = cn(
    "rounded-lg border border-[var(--color-panel-border)] bg-[var(--color-panel-bg)]",
    interactive &&
      "transition-colors hover:border-[var(--color-player-self)]/50",
    className,
  );

  if (props.as === "button") {
    const { as: buttonAs, type = "button", ...buttonProps } = props;
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

  const { as: divAs, ...divProps } = props;
  void divAs;

  return (
    <div className={sharedClassName} {...divProps}>
      {children}
    </div>
  );
}
