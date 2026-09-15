import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorBox } from "./ErrorBox";

describe("ErrorBox", () => {
  it("renders children inside the styled container", () => {
    render(<ErrorBox>Something went wrong</ErrorBox>);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("applies the error colour classes", () => {
    render(<ErrorBox>Error</ErrorBox>);
    const el = screen.getByText("Error");
    expect(el.className).toContain("text-red-400");
    expect(el.className).toContain("border-red-500/30");
  });

  it("merges extra className", () => {
    render(<ErrorBox className="mt-2">Error</ErrorBox>);
    expect(screen.getByText("Error").className).toContain("mt-2");
  });

  it("announces itself as an alert and accepts block children", () => {
    render(
      <ErrorBox>
        <p>Something went wrong</p>
      </ErrorBox>,
    );
    const alert = screen.getByRole("alert");
    expect(alert.tagName).toBe("DIV");
    expect(alert).toContainElement(screen.getByText("Something went wrong"));
  });
});
