import { describe, it, expect, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { SignInScreen } from "./SignInScreen";

describe("SignInScreen", () => {
  it("offers a single primary sign-in action", () => {
    render(<SignInScreen onSignIn={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: "Sign in with Google" }),
    ).toBeEnabled();
  });

  it("invokes onSignIn when the action is used", () => {
    const onSignIn = vi.fn();
    render(<SignInScreen onSignIn={onSignIn} />);

    act(() => screen.getByRole("button").click());

    expect(onSignIn).toHaveBeenCalledOnce();
  });

  it("disables the action and reports progress while loading", () => {
    render(<SignInScreen onSignIn={vi.fn()} loading />);
    const button = screen.getByRole("button", { name: "Signing in…" });
    expect(button).toBeDisabled();
  });

  it("shows the error and turns the action into a retry", () => {
    const onSignIn = vi.fn();
    render(
      <SignInScreen onSignIn={onSignIn} error={new Error("popup blocked")} />,
    );

    expect(screen.getByText("popup blocked")).toBeInTheDocument();
    act(() => screen.getByRole("button", { name: "Try again" }).click());
    expect(onSignIn).toHaveBeenCalledOnce();
  });

  it("shows no error box when there is no error", () => {
    render(<SignInScreen onSignIn={vi.fn()} />);
    expect(screen.queryByText(/blocked/)).not.toBeInTheDocument();
  });
});
