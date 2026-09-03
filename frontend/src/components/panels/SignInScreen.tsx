/**
 * Sign-in screen — the unauthenticated entry point.
 *
 * Nothing else in the app is reachable until Google sign-in succeeds, so this
 * carries the OpenStars! branding and reuses the lobby's cover-art treatment.
 */

import { Button } from "../ui/Button";
import { ErrorBox } from "../ui/ErrorBox";
import { MutedText } from "../ui/MutedText";

const COVER_ART_URL =
  "https://storage.googleapis.com/openstars-assets/stars.jpg";

interface SignInScreenProps {
  onSignIn: () => void;
  loading?: boolean;
  error?: Error | null;
}

export function SignInScreen({ onSignIn, loading, error }: SignInScreenProps) {
  return (
    <div className="relative flex h-screen items-center justify-center overflow-hidden bg-background text-foreground">
      <div className="absolute left-1/2 top-1/2 h-[700px] w-[850px] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl border border-white/10 shadow-2xl">
        <img
          src={COVER_ART_URL}
          alt="Stars! cover art"
          className="absolute inset-0 h-full w-full object-cover object-center opacity-40"
        />
        <div className="absolute inset-0 bg-background/60" />
      </div>

      <div className="relative z-10 w-full max-w-sm space-y-6 p-8 text-center">
        <div>
          <h1 className="text-3xl font-bold tracking-wide">OpenStars!</h1>
          <MutedText as="p" className="mt-1">
            Sign in to reach your games
          </MutedText>
        </div>

        {error && (
          <ErrorBox className="px-4 py-3 text-sm">
            <p>{error.message}</p>
          </ErrorBox>
        )}

        <Button
          onClick={onSignIn}
          disabled={loading}
          variant="primary"
          className="w-full"
        >
          {loading
            ? "Signing in…"
            : error
              ? "Try again"
              : "Sign in with Google"}
        </Button>
      </div>
    </div>
  );
}
