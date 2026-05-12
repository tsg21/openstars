import type { ReactNode } from "react";

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
          <p className="text-sm text-muted-foreground">
            OpenStars! is designed for desktop browsers.
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Please use a screen at least 800px wide.
          </p>
        </div>
      </div>

      {/* 800px+: show the game */}
      <div className="hidden min-[800px]:contents">{children}</div>
    </>
  );
}
