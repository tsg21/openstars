import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import { cn } from "../lib/utils";
import { MutedText } from "./MutedText";

interface FormFieldProps {
  label: ReactNode;
  children: ReactNode;
  className?: string;
}

export function FormField({ label, children, className }: FormFieldProps) {
  return (
    <div className={className}>
      <MutedText as="label" className="mb-1 block text-xs">
        {label}
      </MutedText>
      {children}
    </div>
  );
}

export function TextInput({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-md border border-[var(--color-panel-border)] bg-background px-3 py-1.5 text-sm focus:border-[var(--color-player-self)] focus:outline-none",
        className,
      )}
      {...props}
    />
  );
}

export function SelectInput({
  className,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "w-full rounded-md border border-[var(--color-panel-border)] bg-background px-3 py-1.5 text-sm focus:border-[var(--color-player-self)] focus:outline-none",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}
