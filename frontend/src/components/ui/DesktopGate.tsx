import type { ReactNode } from "react";
import { MutedText } from "./MutedText";

interface DesktopGateProps {
  children: ReactNode;
}

/**
 * Shows a "desktop only" message when viewport is below 800px.
 * On wider screens, renders children normally.
 */
export function DesktopGate({ children }: DesktopGateProps) {
  return (
    <>
      {/* Below 800px: show message */}
      <div className="flex h-screen items-center justify-center bg-background text-foreground min-[800px]:hidden">
        <div className="text-center px-8">
          <h1 className="text-xl font-bold mb-2">OpenStars!</h1>
          <MutedText as="p" className="text-sm">
            OpenStars! is designed for desktop browsers.
          </MutedText>
          <MutedText as="p" className="mt-1 text-xs">
            Please use a screen at least 800px wide.
          </MutedText>
        </div>
      </div>

      {/* 800px+: show the game */}
      <div className="hidden min-[800px]:contents">{children}</div>
    </>
  );
}
