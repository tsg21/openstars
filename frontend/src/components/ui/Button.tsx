import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

type ButtonVariant =
  | "primary"
  | "action"
  | "secondary"
  | "ghost"
  | "success"
  | "dangerGhost"
  | "dashed";

type ButtonSize = "xs" | "sm" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-player-self)] text-white hover:bg-[var(--color-player-self)]/85 disabled:opacity-50",
  action:
    "bg-[var(--color-action-blue)] text-white hover:bg-[var(--color-action-blue-hover)] disabled:opacity-50",
  secondary:
    "border border-[var(--color-panel-border)] text-muted-foreground hover:text-foreground disabled:opacity-50",
  ghost:
    "text-muted-foreground hover:text-foreground disabled:opacity-50",
  success:
    "bg-green-600 text-white hover:bg-green-700 disabled:opacity-50",
  dangerGhost:
    "text-red-400 hover:text-red-300 disabled:opacity-50",
  dashed:
    "border border-dashed border-[var(--color-panel-border)] text-muted-foreground hover:border-[var(--color-player-self)]/50 hover:text-foreground disabled:opacity-50",
};

const sizeClasses: Record<ButtonSize, string> = {
  xs: "px-3 py-1 text-xs",
  sm: "px-4 py-1.5 text-sm",
  icon: "p-1",
};

export function Button({
  children,
  className,
  variant = "secondary",
  size = "sm",
  fullWidth = false,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "rounded-md font-medium transition-colors duration-200 disabled:cursor-not-allowed",
        size !== "icon" && "leading-none",
        sizeClasses[size],
        fullWidth && "w-full",
        variant !== "ghost" && variant !== "dangerGhost" && variant !== "dashed" && "border border-transparent",
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
