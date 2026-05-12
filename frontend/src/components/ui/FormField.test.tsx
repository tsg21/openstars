import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CompactInput, CompactSelect } from "./FormField";

describe("CompactInput", () => {
  it("renders an input with compact styling classes", () => {
    render(<CompactInput aria-label="test" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("px-1.5");
    expect(input.className).toContain("text-xs");
  });

  it("forwards props to the underlying input", () => {
    render(<CompactInput aria-label="qty" placeholder="0" defaultValue="42" />);
    expect(screen.getByDisplayValue("42")).toBeInTheDocument();
  });

  it("merges extra className", () => {
    render(<CompactInput aria-label="test" className="w-16" />);
    expect(screen.getByRole("textbox").className).toContain("w-16");
  });
});

describe("CompactSelect", () => {
  it("renders a select with compact styling classes", () => {
    render(
      <CompactSelect aria-label="test">
        <option value="a">Option A</option>
      </CompactSelect>,
    );
    const select = screen.getByRole("combobox");
    expect(select.className).toContain("px-1.5");
    expect(select.className).toContain("text-xs");
  });

  it("renders children as options", () => {
    render(
      <CompactSelect aria-label="test">
        <option value="foo">Foo</option>
        <option value="bar">Bar</option>
      </CompactSelect>,
    );
    expect(screen.getByRole("option", { name: "Foo" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Bar" })).toBeInTheDocument();
  });
});
