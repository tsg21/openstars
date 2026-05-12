import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders children", () => {
    render(<StatusBadge>42</StatusBadge>);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("applies pill shape classes", () => {
    render(<StatusBadge>Level</StatusBadge>);
    const el = screen.getByText("Level");
    expect(el.className).toContain("rounded-full");
    expect(el.className).toContain("font-bold");
  });

  it("merges extra className for colour overrides", () => {
    render(<StatusBadge className="text-green-400">Active</StatusBadge>);
    expect(screen.getByText("Active").className).toContain("text-green-400");
  });
});
