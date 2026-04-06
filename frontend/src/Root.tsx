import { lazy, Suspense } from "react";
import App from "./App";

const CombatReplayPage = lazy(() =>
  import("./combat-altair-prototype").then((m) => ({ default: m.CombatReplayPage })),
);

export default function Root() {
  if (window.location.pathname === "/combat-altair-prototype") {
    return (
      <Suspense
        fallback={
          <div className="flex h-screen items-center justify-center bg-[#0f172a] text-[#94a3b8]">
            Loading…
          </div>
        }
      >
        <CombatReplayPage />
      </Suspense>
    );
  }
  return <App />;
}
